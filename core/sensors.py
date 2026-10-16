"""Sensor payload validation and explicitly rule-based irrigation guidance."""
import math
from datetime import datetime, timedelta, timezone

from .config import SENSOR_DRY_THRESHOLD_PERCENT, SENSOR_STALE_SECONDS


def normalize_reading(payload, received_at=None):
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object")
    device_id=payload.get("device_id")
    if not isinstance(device_id,str) or not device_id.strip() or len(device_id.strip())>64:
        raise ValueError("device_id must be a non-empty string of at most 64 characters")
    values={}
    # DHT11 advertised operating range; a NaN or out-of-range reading is invalid.
    ranges={"soil_moisture_percent":(0,100),"temperature_c":(0,50),"humidity_percent":(20,90)}
    for key,(low,high) in ranges.items():
        value=payload.get(key)
        if isinstance(value,bool) or not isinstance(value,(int,float)): raise ValueError(f"{key} must be a finite JSON number")
        value=float(value)
        if not math.isfinite(value) or not low<=value<=high:
            raise ValueError(f"{key} must be between {low} and {high}")
        values[key]=value
    timestamp=payload.get("timestamp")
    if timestamp is None:
        if payload.get("sequence") is None: raise ValueError("Provide timestamp or sequence")
        timestamp=(received_at or datetime.now(timezone.utc)).isoformat()
    if not isinstance(timestamp,str): raise ValueError("timestamp must be an ISO 8601 string")
    try: parsed=datetime.fromisoformat(timestamp.replace("Z","+00:00"))
    except ValueError: raise ValueError("timestamp must be a valid ISO 8601 value") from None
    if parsed.tzinfo is None: raise ValueError("timestamp must include a timezone offset")
    now=received_at or datetime.now(timezone.utc)
    if parsed.astimezone(timezone.utc) > now.astimezone(timezone.utc).replace(microsecond=0) + timedelta(minutes=5):
        raise ValueError("timestamp cannot be more than five minutes in the future")
    sequence=payload.get("sequence")
    if sequence is not None and (isinstance(sequence,bool) or not isinstance(sequence,int) or sequence<0):
        raise ValueError("sequence must be a non-negative integer")
    raw_adc=payload.get("raw_adc")
    if raw_adc is not None and (isinstance(raw_adc,bool) or not isinstance(raw_adc,int) or not 0<=raw_adc<=4095):
        raise ValueError("raw_adc must be an integer from 0 to 4095")
    calibrated=payload.get("calibrated",False)
    if not isinstance(calibrated,bool): raise ValueError("calibrated must be true or false")
    return {"device_id":device_id.strip(),"timestamp":parsed.astimezone(timezone.utc).isoformat(),
            **values,"sequence":sequence,"raw_adc":raw_adc,"calibrated":calibrated,"demo":False}


def connection_state(reading, now=None, stale_seconds=SENSOR_STALE_SECONDS):
    if reading is None: return {"state":"Disconnected","stale":True,"age_seconds":None}
    try:
        timestamp=datetime.fromisoformat(reading["timestamp"].replace("Z","+00:00"))
        if timestamp.tzinfo is None: timestamp=timestamp.replace(tzinfo=timezone.utc)
    except (ValueError,KeyError,TypeError):
        return {"state":"Invalid timestamp","stale":True,"age_seconds":None}
    age=max(0,int(((now or datetime.now(timezone.utc))-timestamp.astimezone(timezone.utc)).total_seconds()))
    stale=age>stale_seconds
    return {"state":"Stale" if stale else "Connected","stale":stale,"age_seconds":age}


def irrigation_prediction(reading, water_balance=None, now=None, threshold_percent=SENSOR_DRY_THRESHOLD_PERCENT,
                          stale_seconds=SENSOR_STALE_SECONDS,active_crop=True,crop_stage=None):
    """Use calibrated sensor percentage and optional balance only as a baseline.

    A relative sensor percentage is not volumetric water content. A conflict with
    the separate balance estimate is surfaced as insufficient data for inspection.
    """
    if not active_crop:
        return {"status":"NO IRRIGATION NEEDED","source":"Rule-based baseline","reason":"No active crop is recorded for this field.","measurements":["Saved crop and planting/harvest dates"]}
    if reading is None: return {"status":"INSUFFICIENT DATA","source":"Rule-based baseline","reason":"No sensor readings have been received.","measurements":[]}
    state=connection_state(reading,now=now,stale_seconds=stale_seconds)
    if reading.get("demo"): return {"status":"INSUFFICIENT DATA","source":"Rule-based baseline","reason":"Simulated demo readings are for interface testing and cannot make a field recommendation.","measurements":["Simulated values (not physical sensors)"]}
    if state["stale"]: return {"status":"INSUFFICIENT DATA","source":"Rule-based baseline","reason":"The latest reading is stale or has an invalid timestamp.","measurements":["ESP32 soil-moisture reading"]}
    if not reading.get("calibrated"):
        return {"status":"INSUFFICIENT DATA","source":"Rule-based baseline","reason":"The sensor has not reported a calibrated relative-moisture reading.","measurements":["ESP32 raw-calibration status"]}
    dry=float(reading["soil_moisture_percent"]) < threshold_percent
    balance_action=None
    if water_balance:
        balance_action="dry" if water_balance.get("stress") else "sufficient"
        if dry != (balance_action=="dry"):
            return {"status":"INSUFFICIENT DATA","source":"Rule-based baseline","reason":"Hardware moisture and the separate weather-based water-balance estimate disagree. Inspect the field and sensor placement.","measurements":["Calibrated ESP32 relative soil moisture","Weather/crop/soil water-balance estimate"]}
    needed=dry
    reason=(f"Calibrated relative soil moisture is below the configured {threshold_percent:.0f}% threshold." if needed
            else f"Calibrated relative soil moisture is at or above the configured {threshold_percent:.0f}% threshold.")
    if balance_action: reason += " The separate water-balance estimate agrees." 
    if crop_stage=="late_stage": reason += " The crop is near its expected harvest window; follow crop-specific local guidance before watering."
    return {"status":"IRRIGATION NEEDED" if needed else "NO IRRIGATION NEEDED",
            "source":"Rule-based baseline (not ML)","reason":reason,
            "measurements":["ESP32 soil-moisture percentage (calibrated relative reading)"] + (["Weather/crop/soil water-balance estimate"] if water_balance else [])}
