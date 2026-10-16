import streamlit as st
import asyncio
import pandas as pd
from datetime import date, datetime, timezone
from html import escape
import requests

from core.config import GEMINI_API_KEY
import core.config as app_config
from core.crops import crop_status
from core.db import (
    get_events, get_farm, get_harvest_event, get_observations, init_db,
    list_farms, mark_harvested_today, save_recommendation,
)
from core.decision import decide
from core.field_condition import estimate_field_condition
from core.harvest import harvest_weather_outlook
from core.soil_lookup import lookup_soil
from core.vision import inspect_soil_photo
from core.waterbalance import run_balance
from core.db import latest_sensor_reading, sensor_reading_history
from core.sensors import connection_state, irrigation_prediction
from core.ui import apply_css
from core.weather import get_weather_async

# getattr keeps the dashboard usable during Streamlit hot reloads if the config
# module in a running process was loaded before these optional settings existed.
SENSOR_API_BASE_URL = getattr(app_config, "SENSOR_API_BASE_URL", "http://127.0.0.1:8000")
SENSOR_API_TOKEN = getattr(app_config, "SENSOR_API_TOKEN", "")
SENSOR_DEMO_MODE = getattr(app_config, "SENSOR_DEMO_MODE", False)
SENSOR_DRY_THRESHOLD_PERCENT = getattr(app_config, "SENSOR_DRY_THRESHOLD_PERCENT", 30.0)
SENSOR_STALE_SECONDS = getattr(app_config, "SENSOR_STALE_SECONDS", 120)

@st.cache_data(ttl=5,show_spinner=False)
def _latest_sensor_from_api(base_url):
    headers={"Authorization":f"Bearer {SENSOR_API_TOKEN}"} if SENSOR_API_TOKEN else {}
    try:
        response=requests.get(f"{base_url}/api/sensors/latest",headers=headers,timeout=1.5)
        response.raise_for_status()
        body=response.json()
        return body.get("reading"),"Sensor API"
    except (requests.RequestException,ValueError,KeyError,TypeError):
        return None,"Sensor API unavailable"

apply_css()
init_db()
farms = list_farms()
if not farms:
    st.markdown('<section class="hero dashboard-hero"><div class="hero-kicker">JALRAKSHAK AI · FIELD DASHBOARD</div><h1>Check your field</h1><p>Choose a field location and crop to see the local weather outlook.</p></section>', unsafe_allow_html=True)
    st.info("Start by saving your field location and crop.")
    st.page_link("pages/1_Farm_Setup.py", label="Set up a field", icon="🌾")
    st.stop()

ids = [farm["id"] for farm in farms]
default_id = st.session_state.get("farm_id", ids[0])
fid = st.selectbox(
    "Choose your field", ids,
    index=ids.index(default_id) if default_id in ids else 0,
    format_func=lambda farm_id: next(f["name"] for f in farms if f["id"] == farm_id),
)
st.session_state["farm_id"] = fid
farm = get_farm(fid)
st.markdown(
    f'<section class="hero dashboard-hero"><div class="dashboard-hero-top">'
    f'<div class="hero-kicker"><span class="hero-kicker-dot"></span> YOUR FIELD · {escape(farm["place"])}</div>'
    f'<span class="hero-live-pill"><span></span> TODAY’S OUTLOOK</span></div>'
    f'<div class="dashboard-hero-content"><div><h1>{escape(farm["name"])}</h1>'
    f'<p>{escape(farm["crop"])} <span class="hero-divider">/</span> {farm["area_acres"]:.2f} acres</p></div>'
    f'<div class="hero-emblem" aria-hidden="true"><span>🌱</span><i></i><i></i><i></i></div></div>'
    f'<div class="hero-foot"><span>LOCAL WEATHER</span><span>·</span><span>SOIL-AWARE GUIDANCE</span></div></section>',
    unsafe_allow_html=True,
)
st.page_link("pages/1_Farm_Setup.py", label="Change field location or details", icon="📍")
st.caption("Choose a field, check its wet/dry outlook, then decide whether to water or record a harvest.")

try:
    with st.spinner("Loading local weather and soil-moisture estimates…"):
        weather, source, age = asyncio.run(get_weather_async(farm["latitude"], farm["longitude"]))
    if weather.empty:
        st.error("Live weather is unavailable, so today's advice can't be calculated for this field. Check your internet connection and reload.")
        st.stop()
    events = get_events(fid)
    observations = get_observations(fid)
    status = "fallow" if get_harvest_event(fid) else crop_status(
        farm["sowing_date"], harvest_date=farm["harvest_date"], crop=farm["crop"],
    )
    balance = run_balance(weather, farm, events, observations)
    soil_estimate = weather.attrs.get("soil_moisture", {})
    result = decide(balance, farm, status, soil_profile=soil_estimate)
    is_sample = "SAMPLE WEATHER" in source or "OFFLINE" in source
    save_recommendation(fid, date.today(), result, "Low" if is_sample else "Medium")
except Exception:
    st.error("Could not prepare today's field outlook. Check the saved field details and weather connection, then try again.")
    st.stop()

if "SAMPLE WEATHER" in source or "OFFLINE" in source:
    st.warning(f"{source}. This is demo data, not a forecast for {farm['place']}.")
else:
    st.caption(f"Weather: {source}" + (f" · saved {age} hours ago" if age else ""))

condition = estimate_field_condition(weather)

st.markdown("### Live Hardware Sensors")
st.caption("Physical ESP32 readings are kept separate from Open-Meteo values and the estimated root-zone water balance.")
if st.button("Refresh sensor readings",key="refresh_sensor_readings"):
    _latest_sensor_from_api.clear()
    st.rerun()
history_rows=sensor_reading_history(48)
sensor_reading,api_status=_latest_sensor_from_api(SENSOR_API_BASE_URL)
if api_status!="Sensor API":
    sensor_reading=latest_sensor_reading()
demo_default=bool(SENSOR_DEMO_MODE)
with st.expander("Optional interface demo — simulated values only"):
    use_demo=st.checkbox("Show clearly labelled simulated sensor readings",value=demo_default,key="sensor_demo_enabled")
if "sensor_demo_enabled" not in st.session_state:
    use_demo=demo_default
if use_demo:
    sensor_reading={"device_id":"DEMO ONLY","timestamp":datetime.now(timezone.utc).isoformat(),
        "received_at":datetime.now(timezone.utc).isoformat(),"soil_moisture_percent":24.0,
        "temperature_c":29.0,"humidity_percent":56.0,"raw_adc":None,"sequence":None,
        "calibrated":True,"demo":True}
    demo_times=pd.date_range(end=pd.Timestamp.now(tz="UTC"),periods=8,freq="5min")
    chart_rows=pd.DataFrame({"time":demo_times,"Soil moisture · simulated (%)":[32,31,30,29,28,27,25,24]}).set_index("time")
else:
    chart_rows=pd.DataFrame(history_rows)
    if not chart_rows.empty:
        chart_rows["time"]=pd.to_datetime(chart_rows["timestamp"],utc=True,errors="coerce")
        chart_rows=chart_rows.sort_values("time").set_index("time")[["soil_moisture_percent"]].rename(columns={"soil_moisture_percent":"Soil moisture · hardware (%)"})
state=connection_state(sensor_reading,stale_seconds=SENSOR_STALE_SECONDS)
if sensor_reading is None:
    st.warning("Disconnected · no sensor readings have reached this database yet. Weather-based field advice above remains available.")
else:
    demo_tag=" · SIMULATED — NOT HARDWARE" if sensor_reading.get("demo") else ""
    if sensor_reading.get("demo"):
        st.info("DEMO MODE: values below are fabricated for interface testing. They are not stored and cannot produce a field recommendation.")
    elif state["stale"]:
        st.warning(f"{state['state']} · last received reading was {state['age_seconds']} seconds ago. New sensor data is not arriving.")
    else:
        st.success(f"Connected · last reading {state['age_seconds']} seconds ago")
    sensor_cols=st.columns(4)
    sensor_cols[0].metric("Soil moisture",f"{sensor_reading['soil_moisture_percent']:.1f}%{demo_tag}")
    sensor_cols[1].metric("Air temperature",f"{sensor_reading['temperature_c']:.1f} °C")
    sensor_cols[2].metric("Relative humidity",f"{sensor_reading['humidity_percent']:.1f}%")
    sensor_cols[3].metric("Device",sensor_reading["device_id"])
    reading_time=pd.to_datetime(sensor_reading["timestamp"],utc=True,errors="coerce")
    st.caption(f"Reading timestamp: {reading_time.strftime('%Y-%m-%d %H:%M:%S UTC') if not pd.isna(reading_time) else 'invalid'} · Calibration: {'calibrated relative reading' if sensor_reading.get('calibrated') else 'NOT CALIBRATED; percentage is not suitable for prediction'} · Expected update: about every 5 seconds")
    st.caption("Reading source: explicitly simulated demo" if sensor_reading.get("demo") else ("Reading source: sensor API" if api_status=="Sensor API" else "Sensor API unavailable; showing the last row from the shared local SQLite database."))
if not chart_rows.empty:
    st.line_chart(chart_rows)
else:
    st.caption("Sensor history will appear after the ESP32 sends readings to the local sensor API.")

st.markdown("### AI Irrigation Prediction")
st.caption("Rule-based baseline only. No trained irrigation ML model or validated training dataset is available.")
historical_balance=balance.loc[~balance["is_forecast"]]
balance_context=None
if not historical_balance.empty:
    last_balance=historical_balance.iloc[-1]
    balance_context={"stress":bool(last_balance["stress"])}
prediction=irrigation_prediction(sensor_reading,balance_context,stale_seconds=SENSOR_STALE_SECONDS,
                                 active_crop=result["action"]!="NO_CROP",crop_stage=status)
if sensor_reading is None and prediction["status"] == "INSUFFICIENT DATA":
    st.info("Hardware prediction is waiting for the ESP32. No sensor reading has arrived yet; the weather-based field recommendation above is still available.")
elif prediction["status"]=="IRRIGATION NEEDED": st.error(f"**{prediction['status']}** · {prediction['reason']}")
elif prediction["status"]=="NO IRRIGATION NEEDED": st.success(f"**{prediction['status']}** · {prediction['reason']}")
else: st.warning(f"**{prediction['status']}** · {prediction['reason']}")
if sensor_reading is not None:
    st.caption(f"Inputs: {', '.join(prediction['measurements'])} · Method: {prediction['source']} · Relative-moisture dry threshold: {SENSOR_DRY_THRESHOLD_PERCENT:.0f}% (configurable; not volumetric water content).")
st.caption("DHT11 temperature and humidity are displayed as air measurements only; the irrigation threshold does not use them as soil-moisture evidence.")
st.caption(f"Sensor API configured at {SENSOR_API_BASE_URL}. For an ESP32, use the computer's LAN IP address in firmware; 127.0.0.1 on the ESP32 refers to the ESP32 itself.")

advice = {
    "NO_CROP": ("Add a crop to get advice", "This field has no active crop saved."),
    "IRRIGATE_NOW": ("Check the soil before watering", "The weather suggests water may be needed. Water only if the soil feels dry."),
    "IRRIGATE_SOON": ("Check the field tomorrow", "The field may need water soon. Check the soil again before watering."),
    "WAIT": ("No watering needed right now", "Recent conditions do not point to an immediate need. Check again if the weather changes."),
    "SKIP_RAIN_EXPECTED": ("Wait for the rain", "Rain is expected soon. Check the soil after it rains before watering."),
}
advice_title, advice_text = advice.get(result["action"], advice["WAIT"])
if result["action"] == "IRRIGATE_NOW" and any("Forecast rain is too small" in reason for reason in result["reasons"]):
    advice_text = "A little rain may be forecast, but it may not cover the estimated crop water deficit. Check the soil by hand before deciding to water."
elif result["action"] == "IRRIGATE_NOW" and condition["label"] == "Likely wet":
    advice_text = "Recent rain may have left the field wet. Check the soil by hand before deciding to water."
elif result["action"] == "IRRIGATE_NOW" and condition["label"] == "Likely drying":
    advice_text = "The field may be drying. Check the soil by hand and water only if it feels dry."
action_style = {
    "IRRIGATE_NOW": "recommend-warning",
    "IRRIGATE_SOON": "recommend-warning",
    "WAIT": "recommend-success",
    "SKIP_RAIN_EXPECTED": "recommend-neutral",
    "NO_CROP": "recommend-neutral",
}.get(result["action"], "recommend-neutral")
st.markdown(
    f'<section class="recommend-banner today-advice {action_style}"><div class="advice-mark" aria-hidden="true">✳</div>'
    f'<div class="advice-copy"><div class="today-advice-kicker">YOUR NEXT STEP</div>'
    f'<h2>{escape(advice_title)}</h2><p>{escape(advice_text)}</p></div>'
    f'<div class="advice-side-note"><span>FIELD FIRST</span><small>Check before you water</small></div></section>',
    unsafe_allow_html=True,
)

# Keep the main page action-first. Detailed forecast numbers are available below.
current = weather.attrs.get("current", {})
st.markdown("#### Weather now")
rain_24h = weather.attrs.get("rain_last_24h_mm")
weather_cols = st.columns(4)
weather_cols[0].metric("Temperature", f"{current['temperature_c']:.1f} °C" if current.get("temperature_c") is not None else "Unavailable")
weather_cols[1].metric("Humidity", f"{current['humidity_pct']:.0f}%" if current.get("humidity_pct") is not None else "Unavailable")
weather_cols[2].metric("Rain · last 24 hours", f"{rain_24h:.1f} mm" if rain_24h is not None else "Unavailable")
weather_cols[3].metric("Wind", f"{current['wind_kmh']:.1f} km/h" if current.get("wind_kmh") is not None else "Unavailable")

surface_vwc = soil_estimate.get("surface_m3_m3")
deeper_vwc = soil_estimate.get("deeper_m3_m3")
if surface_vwc is not None or deeper_vwc is not None:
    st.markdown("#### Modelled soil moisture")
    moisture_cols = st.columns(2)
    for column, label, value in (
        (moisture_cols[0], "Surface · 0–7 cm", surface_vwc),
        (moisture_cols[1], "Deeper soil · 7–28 cm", deeper_vwc),
    ):
        column.metric(label, f"{value*100:.1f}%" if value is not None else "Unavailable",
                      help=f"Volumetric water content in m³/m³: {value:.3f}" if value is not None else "The weather model did not return these soil layers.")
    st.caption("Open-Meteo weather-model estimates, not physical soil measurements. Depth averages are calculated from its hourly model layers.")
    if result.get("soil_moisture_used"):
        st.caption("Today's recommendation uses the modelled soil layers to update the crop-specific root-zone estimate.")
else:
    st.info("Open-Meteo soil-moisture layers are unavailable for this forecast. The advice above uses the separate crop and soil water-balance estimate.")

today_stamp = pd.to_datetime(current.get("time"), errors="coerce") if current.get("time") else pd.NaT
today_for_forecast = today_stamp.date() if not pd.isna(today_stamp) else date.today()
today_rows = weather[weather["date"].dt.date == today_for_forecast]
today_et0 = today_rows.iloc[0]["et0"] if len(today_rows) else None
st.caption(f"Today’s reference water loss (ET₀): {today_et0:.1f} mm" if pd.notna(today_et0) else "Today’s reference water loss (ET₀): unavailable")
if current.get("time"):
    st.caption(f"Weather updated: {current['time']}")

with st.expander("See the 7-day forecast"):
    forecast = weather.loc[weather["is_forecast"]].head(7).copy()
    if forecast.empty:
        st.info("The forecast is not available yet.")
    else:
        display = forecast[["date", "tmax", "rain", "et0"]].copy()
        display.columns = ["Date", "High temperature (°C)", "Rain (mm)", "Water loss · ET₀ (mm)"]
        rain_chart = forecast[["date", "rain"]].dropna().set_index("date").rename(columns={"rain": "Rain (mm)"})
        if not rain_chart.empty:
            st.bar_chart(rain_chart)
        st.dataframe(display, hide_index=True, width="stretch")

harvest = harvest_weather_outlook(
    weather, farm["crop"], farm["sowing_date"], farm.get("harvest_date"),
)
harvest_line = f"Estimated harvest: {harvest['date'].strftime('%d %b %Y')}"
if harvest["status"] == "Estimated date has passed":
    harvest_line += " · check crop maturity in the field"
st.markdown(f"**{escape(harvest_line)}**")
if harvest["status"] in ("Rain watch near harvest", "No major rain in the current forecast window", "Forecast window unavailable"):
    st.caption(escape(harvest["status"] + ". " + harvest["detail"]))

today_harvest = get_harvest_event(fid)
if today_harvest:
    st.success(f"Harvest recorded today for {today_harvest['place']}.")
elif st.button("Record harvest today", help="Saves today's date and this field's saved location."):
    try:
        mark_harvested_today(fid)
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))

with st.expander("Optional: use a soil map or take a soil photo"):
    st.caption("These checks are optional. The main weather outlook and watering advice work without them.")
    mapped_soil = st.session_state.get(f"mapped_soil_{fid}")
    if st.button("Check mapped soil type", key=f"soilmap{fid}"):
        with st.spinner("Checking the public soil map…"):
            mapped_soil = lookup_soil(round(float(farm["latitude"]), 4), round(float(farm["longitude"]), 4))
        if mapped_soil:
            st.session_state[f"mapped_soil_{fid}"] = mapped_soil
        else:
            st.info("No mapped soil estimate was returned for this location. The soil type saved during setup is still used for the advice.")
    if mapped_soil:
        st.caption(f"Approximate mapped soil: {mapped_soil['soil']} · nearest mapped cell about {mapped_soil['distance_m']} m away. Compare with the field itself.")
    soil_for_photo = mapped_soil["soil"] if mapped_soil else farm["soil"]
    photo = st.camera_input("Take a close-up of bare soil", key=f"soilphoto{fid}")
    if photo and st.button("Estimate surface from photo", key=f"analyzesoil{fid}"):
        if not GEMINI_API_KEY:
            st.info("Photo analysis needs a Gemini key in your local .env. Photo capture works without it; the key is blank by design.")
        else:
            visual, error = inspect_soil_photo(photo.getvalue(), photo.type, soil_for_photo, condition["label"])
            if error:
                st.info(error)
            else:
                st.write(f"Photo estimate: **{visual['condition']}** · {visual['note']}")
                st.caption("A visual estimate, not a soil measurement. The model is instructed to ignore colour.")

st.page_link("pages/6_Water_Usage.py", label="Add a watering log or field note", icon="💧")
