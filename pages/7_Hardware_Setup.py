import streamlit as st
import requests

import core.config as app_config
from core.db import latest_sensor_reading, init_db
from core.sensors import connection_state
from core.ui import apply_css

API_BASE_URL = getattr(app_config, "SENSOR_API_BASE_URL", "http://127.0.0.1:8000")
API_TOKEN = getattr(app_config, "SENSOR_API_TOKEN", "")
STALE_SECONDS = getattr(app_config, "SENSOR_STALE_SECONDS", 120)

st.set_page_config(page_title="Hardware Setup · JalRakshak AI", page_icon="🔌", layout="wide")
apply_css()
init_db()

st.title("ESP32 hardware setup")
st.write("Connect your soil-moisture sensor and DHT11 to send real readings to JalRakshak AI.")
st.info("The ESP32 measures and reports sensor readings. It does not control a pump, relay, valve, or automatic watering.")

st.subheader("Parts you have")
st.write("ESP32 development board, FC-28 or capacitive soil-moisture module, DHT11, breadboard, jumper wires, USB data cable, LED, and 220 Ω resistor.")

st.subheader("Wiring · ESP32 DevKit V1 example")
st.write("Use the sensor module's analog output (AO) for moisture. Join all grounds together.")
st.table([
    {"Part / pin": "Moisture sensor AO", "ESP32 connection": "GPIO34"},
    {"Part / pin": "Moisture sensor VCC", "ESP32 connection": "3V3 (check your module's voltage requirements)"},
    {"Part / pin": "DHT11 DATA", "ESP32 connection": "GPIO4"},
    {"Part / pin": "DHT11 VCC", "ESP32 connection": "3V3"},
    {"Part / pin": "LED anode (long leg)", "ESP32 connection": "GPIO18 through the 220 Ω resistor"},
    {"Part / pin": "LED cathode (short leg)", "ESP32 connection": "GND"},
    {"Part / pin": "All sensor grounds", "ESP32 connection": "GND"},
])
st.warning("ESP32 inputs are not 5 V tolerant. Never let the moisture sensor's AO voltage exceed the ESP32 input limit. A capacitive probe is better for ongoing use; FC-28 resistive probes can corrode. A bare DHT11 may need a DATA pull-up resistor; many modules include one.")

st.subheader("Set up the software")
st.markdown(
    """1. Open `hardware/esp32_sensor.ino` in Arduino IDE and install the ESP32 board package, **DHT sensor library** by Adafruit, and **Adafruit Unified Sensor**.
2. Set your Wi-Fi name and password in the sketch. Set `API_URL` to your computer's LAN address, for example `http://192.168.1.10:8000/api/sensors/readings`.
3. Start `python sensor_api.py` and `streamlit run app.py` on the computer. Keep the ESP32 and computer on the same Wi-Fi network.
4. Initially keep `CALIBRATION_VALID = false`. In Serial Monitor at 115200 baud, record the ADC reading with the probe in dry reference soil and wet reference soil. Put those values in `SOIL_DRY_RAW` and `SOIL_WET_RAW`, then set calibration true and upload again.
5. The website reports relative moisture, not laboratory volumetric water content. Check the soil directly before making irrigation decisions."""
)
st.caption("The optional LED turns on after a successful sensor upload and goes off if no upload succeeds for 15 seconds. It indicates connection to the API, not a dry-soil or irrigation alert.")

st.subheader("Connection status")
headers = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}
try:
    response = requests.get(f"{API_BASE_URL}/api/sensors/latest", headers=headers, timeout=1.5)
    response.raise_for_status()
    reading = response.json().get("reading")
except (requests.RequestException, ValueError, AttributeError):
    reading = None
    st.caption("Sensor API is currently unavailable; showing the last reading saved in the local database, if available.")
if reading is None:
    reading = latest_sensor_reading()
state = connection_state(reading, stale_seconds=STALE_SECONDS)
if reading is None:
    st.warning("No hardware readings received yet. Check the API, Wi-Fi, and ESP32 settings above.")
elif state["stale"]:
    st.warning(f"Last reading is stale ({state['age_seconds']} seconds old). Check that new data is arriving.")
else:
    st.success(f"Connected · last reading {state['age_seconds']} seconds ago")
    values = st.columns(4)
    values[0].metric("Soil moisture", f"{reading['soil_moisture_percent']:.1f}%")
    values[1].metric("Air temperature", f"{reading['temperature_c']:.1f} °C")
    values[2].metric("Relative humidity", f"{reading['humidity_percent']:.1f}%")
    values[3].metric("Calibration", "Ready" if reading.get("calibrated") else "Needed")

