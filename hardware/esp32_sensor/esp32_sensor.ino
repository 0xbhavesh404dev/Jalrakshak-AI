/* JalRakshak AI ESP32 sensor sender. No pump, valve, relay, or automatic watering. */
#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <time.h>

// Fill these in locally before upload. Do not commit real credentials.
const char* WIFI_SSID = "ACTFIBERNET_5G";
const char* WIFI_PASSWORD = "#F202/SF02";
const char* API_URL = "http://192.168.1.112:8000/api/sensors/readings";
const char* DEVICE_ID = "jalrakshak-esp32-01";
const char* DEVICE_TOKEN = "zEPPAMmi13mdgrdj3iNhj9TqQLLlkwer8gKgW2qpvP0"; // Required only when API is bound beyond localhost.

// ESP32 DevKit V1 wiring: capacitive moisture sensor AO -> GPIO34 (ADC1),
// DHT11 DATA -> GPIO4, sensor VCC -> 3V3, common GND -> GND.
// Verify the exact board and sensor breakout voltage before wiring.
constexpr int SOIL_ADC_PIN = 34; // input-only ADC1 pin; usable while Wi-Fi is active
constexpr int DHT_PIN = 4;
constexpr int DHT_TYPE = DHT11;
constexpr int STATUS_LED_PIN = 18; // external LED through 220 ohm resistor
constexpr uint32_t SEND_INTERVAL_MS = 5000;
constexpr uint32_t WIFI_RETRY_INTERVAL_MS = 10000;
constexpr uint32_t LED_SUCCESS_HOLD_MS = 15000;

// Measure these on the actual installed sensor. Some sensors read higher when dry.
// Set CALIBRATION_VALID true only after recording dry and wet reference values.
constexpr int SOIL_DRY_RAW = 3000;
constexpr int SOIL_WET_RAW = 1300;
constexpr bool CALIBRATION_VALID = false;

DHT dht(DHT_PIN, DHT_TYPE);
uint32_t sequenceNumber = 0;
uint32_t lastSend = 0;
uint32_t lastWifiAttempt = 0;
bool timeConfigured = false;
uint32_t lastSuccessfulPost = 0;
bool hasSuccessfulPost = false;

String isoTimestampOrEmpty() {
  struct tm timeInfo;
  if (!getLocalTime(&timeInfo, 50)) return "";
  char buffer[32];
  // UTC timestamp. configTime sets UTC and the backend stores UTC.
  if (strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", &timeInfo) == 0) return "";
  return String(buffer);
}

int relativeMoisturePercent(int raw) {
  if (SOIL_DRY_RAW == SOIL_WET_RAW) return 0;
  long percent = (long)(raw - SOIL_DRY_RAW) * 100L / (SOIL_WET_RAW - SOIL_DRY_RAW);
  return constrain((int)percent, 0, 100);
}

void connectWiFiIfDue(uint32_t now) {
  if (WiFi.status() == WL_CONNECTED || now - lastWifiAttempt < WIFI_RETRY_INTERVAL_MS) return;
  lastWifiAttempt = now;
  Serial.printf("Connecting to Wi-Fi: %s\n", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD); // returns immediately; retry is loop-driven
}

void sendReading() {
  int raw = analogRead(SOIL_ADC_PIN);
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("DHT11 read failed; skipping this payload.");
    return;
  }
  if (WiFi.status() != WL_CONNECTED) {
    Serial.printf("No Wi-Fi; reading not sent. ADC=%d\n", raw);
    return;
  }

  String timestamp = isoTimestampOrEmpty();
  String payload = "{\"device_id\":\"" + String(DEVICE_ID) + "\","
    "\"soil_moisture_percent\":" + String(relativeMoisturePercent(raw)) + ","
    "\"temperature_c\":" + String(temperature, 1) + ","
    "\"humidity_percent\":" + String(humidity, 1) + ","
    "\"raw_adc\":" + String(raw) + ","
    "\"sequence\":" + String(sequenceNumber++) + ","
    "\"calibrated\":" + String(CALIBRATION_VALID ? "true" : "false");
  if (timestamp.length()) payload += ",\"timestamp\":\"" + timestamp + "\"";
  payload += "}";

  HTTPClient http;
  http.setConnectTimeout(2000);
  http.setTimeout(2500);
  if (!http.begin(API_URL)) {
    Serial.println("Could not initialize HTTP request; check API_URL.");
    return;
  }
  http.addHeader("Content-Type", "application/json");
  if (strlen(DEVICE_TOKEN) > 0) http.addHeader("Authorization", String("Bearer ") + DEVICE_TOKEN);
  int status = http.POST(payload);
  Serial.printf("POST %s -> HTTP %d; ADC=%d moisture=%d%% calibrated=%s\n",
    API_URL, status, raw, relativeMoisturePercent(raw), CALIBRATION_VALID ? "yes" : "no");
  if (status > 0) Serial.println(http.getString());
  else Serial.printf("HTTP request failed: %s\n", http.errorToString(status).c_str());
  if (status >= 200 && status < 300) {
    lastSuccessfulPost = millis();
    hasSuccessfulPost = true;
  }
  http.end();
}

void setup() {
  Serial.begin(115200);
  pinMode(STATUS_LED_PIN, OUTPUT);
  digitalWrite(STATUS_LED_PIN, LOW);
  analogReadResolution(12);
  analogSetPinAttenuation(SOIL_ADC_PIN, ADC_11db);
  dht.begin();
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  lastWifiAttempt = millis();
  Serial.println("JalRakshak sensor sender started; this device does not control irrigation.");
}

void loop() {
  uint32_t now = millis();
  connectWiFiIfDue(now);
  if (WiFi.status() == WL_CONNECTED && !timeConfigured) {
    Serial.printf("Wi-Fi connected; ESP32 IP: %s\n", WiFi.localIP().toString().c_str());
    configTime(0, 0, "pool.ntp.org", "time.google.com");
    timeConfigured = true;
  }
  if (now - lastSend >= SEND_INTERVAL_MS) {
    lastSend = now;
    sendReading();
  }
  // LED indicates a recent successful upload only; it is not an irrigation alert.
  bool uploadIsRecent = hasSuccessfulPost && (now - lastSuccessfulPost < LED_SUCCESS_HOLD_MS);
  digitalWrite(STATUS_LED_PIN, uploadIsRecent ? HIGH : LOW);
  delay(20); // short yield only; no long blocking connect/read loop
}
