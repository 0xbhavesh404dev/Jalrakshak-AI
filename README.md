# JalRakshak AI

**Predict the Need. Save Every Drop.** An irrigation advisory prototype that combines weather-based estimates with readings from an optional ESP32 soil-moisture and DHT11 sensor. Sensor readings, model estimates and rule-based guidance are shown as separate sources. The ESP32 only measures and reports; it does not control irrigation equipment.

## Hardware prototype

The project hardware baseline is:

1. **ESP32 development board** — reads the sensors and provides the future Wi-Fi connection.
2. **Soil-moisture sensor module** — FC-28 or, preferably, a capacitive sensor.
3. **DHT11 temperature and humidity sensor** — measures air temperature and relative humidity.
4. **Breadboard**
5. **Male-to-male jumper wires**
6. **USB data cable**
7. **LED and 220 Ω resistor** — local indicator that the ESP32 has recently uploaded readings.

The minimum useful demonstration is the ESP32, soil-moisture sensor and DHT11. The LED is optional. This project does not require or control a pump, relay, valve, or LDR.

### Intended sensor-to-app flow

```text
ESP32 → soil moisture + temperature + humidity + timestamp
      → validated sensor payload
      → JalRakshak AI dashboard
      → irrigation recommendation and explanation
```

The firmware is in `hardware/esp32_sensor/esp32_sensor.ino`; the FastAPI ingestion service is `sensor_api.py`. The service stores readings in the existing SQLite database. Do not treat raw ADC output as a percentage. Firmware starts with `CALIBRATION_VALID = false`, so the website will not make a sensor prediction until you calibrate the probe and set it true.

Suggested payload for the integration boundary:

```json
{
  "soil_moisture_percent": 38,
  "temperature_c": 31.4,
  "humidity_percent": 58,
  "timestamp": "2026-10-16T11:45:00+05:30"
}
```

## Install and run the website

Requires Python 3.10 or newer.

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
streamlit run app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
test -f .env || cp .env.example .env
streamlit run app.py
```

Set `JALRAKSHAK_OFFLINE=1` in `.env` only when you want the clearly labelled bundled Hyderabad demo data. The free Open-Meteo forecast and geocoding endpoints require no API key. The app uses a recent saved response if the network is unavailable; with no real cached data, it shows an unavailable state rather than presenting another location's demo weather as a live forecast. Optional Gemini photo analysis requires `GEMINI_API_KEY`; leave it blank to keep that feature disabled. Never commit `.env` or put secrets in source.

These commands start the **website only**. To use the optional ESP32, also start the sensor API as described in [Start the API and website](#start-the-api-and-website) below.

Weather requests follow the free [Open-Meteo forecast API](https://open-meteo.com/en/docs) and [geocoding API](https://open-meteo.com/en/docs/geocoding-api); neither needs a key. The app asks for supported hourly soil layers and daily crop-water inputs, validates responses, caches by coordinates, and labels unavailable/demo data. The optional Gemini REST request follows the [official generateContent API](https://ai.google.dev/api/generate-content); its model name remains configurable.

The app creates its SQLite database at `data/jalrakshak.sqlite3` on first run. Back up or delete that file as needed; it is ignored by Git.

## ESP32 hardware demo

### Wiring (ESP32 DevKit V1 example)

| Part | Pin / connection |
|---|---|
| Moisture sensor AO | GPIO34 (ADC1 input) |
| Moisture sensor VCC | 3V3, after checking the specific board/module voltage requirements |
| DHT11 DATA | GPIO4 |
| DHT11 VCC | 3V3 |
| LED anode (long leg) | GPIO18 through a 220 Ω resistor |
| LED cathode (short leg) | ESP32 GND |
| Both sensor GND pins | ESP32 GND |

Use the analog output (AO), not the digital threshold pin (DO). A capacitive probe is preferred for longer-term use; FC-28 resistive probes can corrode. ESP32 GPIO inputs are not 5 V tolerant: the moisture sensor's analog signal must never exceed the ESP32's allowed input voltage. A bare DHT11 may need a pull-up resistor on DATA; many modules already include one. Board pinouts and sensor modules vary, so verify labels before powering the circuit. Keep the board on USB during the demo. The LED turns on after a successful upload and turns off if no upload succeeds for 15 seconds; it does not indicate soil dryness or operate irrigation equipment.

### Start the API and website

The ESP32 and computer must be on the same trusted Wi-Fi/LAN. The API defaults to loopback, which is safe for desktop-only use but cannot receive a remote ESP32. For a LAN demo, edit the local, ignored `.env` file (do not replace an existing `.env`) and set:

```env
SENSOR_API_HOST=0.0.0.0
SENSOR_API_PORT=8000
SENSOR_API_BASE_URL=http://127.0.0.1:8000
SENSOR_API_TOKEN=PASTE_A_PRIVATE_RANDOM_TOKEN_HERE
SENSOR_STALE_SECONDS=120
SENSOR_DRY_THRESHOLD_PERCENT=30
```

Generate a token locally with `python -c "import secrets; print(secrets.token_urlsafe(32))"`; use the output only in your ignored `.env` and the ESP32 sketch. Binding beyond localhost requires a token. Do not expose this unauthenticated service to the public internet.

Start both services on the computer: open two terminals in the project folder and keep both terminals open while using the hardware. The website is at `http://localhost:8501`; the API status page is at `http://127.0.0.1:8000/` and its health check is `http://127.0.0.1:8000/health`.

#### Windows (PowerShell)

In **Terminal 1** (sensor API):

```powershell
.\.venv\Scripts\Activate.ps1
python sensor_api.py
```

In **Terminal 2** (website):

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

#### Linux

In **Terminal 1** (sensor API):

```bash
source .venv/bin/activate
python sensor_api.py
```

In **Terminal 2** (website):

```bash
source .venv/bin/activate
streamlit run app.py
```

Press `Ctrl+C` in each terminal to stop its service. To use the website without the ESP32, only start Streamlit using the [website instructions](#install-and-run-the-website).

The ESP32 and computer must use the same trusted Wi-Fi/LAN. In the ESP32 sketch, set `API_URL` to the computer's LAN address (for example `http://192.168.1.10:8000/api/sensors/readings`), not `127.0.0.1`; that address would refer to the ESP32 itself. Allow the computer's firewall to accept port 8000 on the private network if needed. The website's `SENSOR_API_BASE_URL` remains `http://127.0.0.1:8000` because the website and API run on the same computer.

For a LAN demo, configure the local, ignored `.env` file (do not replace an existing `.env`) with the settings shown above. The API must bind to `0.0.0.0` for the ESP32 to reach it; use a private random token, keep it secret, and do not expose port 8000 to the public internet. Check the API from the computer with `curl http://127.0.0.1:8000/health`.

If the ESP32 cannot connect, check the computer's LAN IP, firewall permission on port 8000, same Wi-Fi network, and router client isolation.

If Streamlit runs on a remote host, its local API and SQLite file are not automatically reachable from the farm. You need a private VPN or secured tunnel, firewall rules, token protection, and a reachable API endpoint. Never expose port 8000 directly to the public internet for this demo.

### Arduino IDE and sensor calibration

1. Install Arduino IDE and the Espressif ESP32 board package. Select the correct ESP32 board and USB port.
2. In Library Manager install **DHT sensor library** by Adafruit and **Adafruit Unified Sensor**. `WiFi`, `HTTPClient`, and `time` are included with the ESP32 board package.
3. Open `hardware/esp32_sensor/esp32_sensor.ino`. Set `WIFI_SSID`, `WIFI_PASSWORD`, `API_URL` (computer LAN IP), `DEVICE_ID`, and `DEVICE_TOKEN`. Keep real credentials out of committed files.
4. Before calibrating, upload with `CALIBRATION_VALID = false`. Open Serial Monitor at 115200 baud and record `ADC=` with the probe in dry reference soil and then thoroughly wet reference soil. Use the same probe placement, soil, and supply voltage for both readings.
5. Set `SOIL_DRY_RAW` and `SOIL_WET_RAW` to the actual measured dry/wet values. The conversion handles either direction automatically, then set `CALIBRATION_VALID = true` and upload again. If the references are equal, unstable, or outside 0–4095, investigate wiring/probe placement instead of enabling calibration.
6. This is a calibrated **relative sensor percentage**, not volumetric water content or a lab-validated soil-moisture measurement. Recalibrate for a changed sensor, soil, or installation. The default 30% dry threshold is only a configurable demo baseline; tune it against direct field checks.

The firmware samples about every five seconds, retries Wi-Fi in the background, uses bounded HTTP timeouts, sends an ISO UTC timestamp when NTP is available and otherwise sends a sequence number, and skips a payload when DHT11 values are invalid. Serial Monitor reports connection and HTTP errors. Example JSON:

```json
{"device_id":"jalrakshak-esp32-01","soil_moisture_percent":38,"temperature_c":31.4,"humidity_percent":58,"timestamp":"2026-10-16T11:45:00Z","sequence":12,"raw_adc":1840,"calibrated":true}
```

### API smoke test and dashboard

With the API running, send a clearly labelled test reading from the computer:

```bash
SENSOR_TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
curl -X POST http://127.0.0.1:8000/api/sensors/readings \
  -H 'Content-Type: application/json' \
  -d "{\"device_id\":\"demo-computer\",\"soil_moisture_percent\":42,\"temperature_c\":30.5,\"humidity_percent\":60,\"timestamp\":\"${SENSOR_TIMESTAMP}\",\"sequence\":1,\"raw_adc\":1800,\"calibrated\":true}"
```

For LAN-token configuration, include `-H 'Authorization: Bearer YOUR_PRIVATE_TOKEN'`; use a current timestamp, since readings more than five minutes in the future are rejected. `GET /api/sensors/latest` and `GET /api/sensors/history` return persisted readings; add `?device_id=jalrakshak-esp32-01` to filter.

On **Today's field outlook**, **Live Hardware Sensors** shows the last reading, age/status, calibration, and recent moisture chart. Use **Refresh sensor readings** to refresh the database view. The ESP32 posts every five seconds; dashboard values refresh when the page reruns. Missing, stale, or uncalibrated data cannot produce a hardware prediction. Optional demo values are visibly simulated, never persisted, and never drive a field recommendation. **AI Irrigation Prediction** is an explicitly labelled rule-based baseline, not ML. Disagreement with the water-balance estimate is shown as insufficient data for field inspection.

### Optional ML training

No validated labeled dataset or trained model is bundled. `data/sensor_training_template.csv` documents the CSV columns. `irrigation_needed` must be a real measured or expert-provided 0/1 label; do not generate labels from the same 30% threshold and describe the result as an independently learned irrigation policy. Install optional tooling with `python -m pip install scikit-learn joblib`, then run:

```bash
python training/train_irrigation_model.py path/to/labelled.csv --label-source measured
```

Use `--label-source expert` for labels reviewed by an agronomist. The script validates missing values and labels, trains a Random Forest on earlier records, evaluates on the later 20%, and reports accuracy, precision, recall, F1 and confusion matrices beside a 30% threshold baseline. Metrics describe only that dataset. The generated Joblib model is a trusted-local artifact; loading pickle-based model files from unknown sources can execute malicious code. No model accuracy is claimed until a suitable dataset is collected and evaluated.

## Checks

```bash
python -m compileall .
pytest -q
streamlit run app.py
```

The test suite is designed to run without internet. Live API availability depends on network access.

## Main workflow

The sidebar keeps the app to three steps: Home, Set up field, and Today's field outlook. A separate Field notes page records watering and observed soil condition. On setup, choose a town, allow browser location after pressing **Use my current location**, or enter coordinates. Soil can be selected manually or estimated from the selected location. The dashboard provides a weather-based wet/dry outlook, irrigation guidance, estimated harvest timing, and a harvest record. Optional soil map/photo tools are kept out of the main workflow.

Older weather exploration, scenario, and question-answering pages are not linked from the simplified navigation.

## Limitations

All root-zone quantities are estimates. Crop and soil parameters are simplified; rainfall effectiveness and irrigation efficiency are assumptions. Forecasts can be wrong. Rice/paddy is less suitable for this balance model. Scenario outputs are simulations. ESP32 soil moisture is a relative calibrated reading, and the DHT11 measures air conditions. The rule-based prediction threshold is not a validated irrigation policy. No ML model or suitable training dataset is bundled. Simulated comparisons are not proof of water savings. Consult local agricultural guidance and inspect field soil before acting. Physical wiring and sensor calibration still require testing on the owner's hardware.

See [DOCUMENTATION.md](JalRakshak_AI_Documentation.md) for the concept, and [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md) for the durable status log and remaining work.
