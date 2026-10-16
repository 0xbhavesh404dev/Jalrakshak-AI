"""Open-Meteo weather service and normalization for the irrigation model."""
import asyncio
import hashlib
import json
import time
from datetime import date, timedelta

import pandas as pd
import requests

from .config import OFFLINE, CACHE_DIR, SAMPLE_WEATHER

PRESETS = [
    {"name": "Hyderabad", "latitude": 17.385, "longitude": 78.4867, "country": "India"},
    {"name": "Warangal", "latitude": 17.9689, "longitude": 79.5941, "country": "India"},
]
_PLACE_CACHE = {}
_WEATHER_CACHE = {}
BASE = "https://api.open-meteo.com/v1/forecast"
GEO = "https://geocoding-api.open-meteo.com/v1/search"
CACHE_TTL_SECONDS = 15 * 60

CURRENT_VARIABLES = "temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m"
HOURLY_VARIABLES = ",".join((
    "temperature_2m", "relative_humidity_2m", "precipitation", "rain",
    "wind_speed_10m", "et0_fao_evapotranspiration",
    "soil_moisture_0_to_1cm", "soil_moisture_1_to_3cm",
    "soil_moisture_3_to_9cm", "soil_moisture_9_to_27cm",
    "soil_moisture_27_to_81cm",
))
DAILY_VARIABLES = ",".join((
    "temperature_2m_max", "temperature_2m_min", "precipitation_sum",
    "rain_sum", "precipitation_probability_max", "et0_fao_evapotranspiration",
    "relative_humidity_2m_mean", "wind_speed_10m_max",
))
SOIL_LAYERS = {
    "soil_moisture_0_to_1cm": (0, 1),
    "soil_moisture_1_to_3cm": (1, 3),
    "soil_moisture_3_to_9cm": (3, 9),
    "soil_moisture_9_to_27cm": (9, 27),
    "soil_moisture_27_to_81cm": (27, 81),
}


def search_places(name):
    """Search Open-Meteo geocoding; return known presets if offline/unavailable."""
    if OFFLINE or not name.strip():
        return PRESETS
    cache_key = name.strip().casefold()
    if cache_key in _PLACE_CACHE:
        return _PLACE_CACHE[cache_key]
    try:
        response = requests.get(
            GEO,
            params={"name": name, "count": 8, "language": "en", "format": "json"},
            timeout=8,
        )
        response.raise_for_status()
        results = [
            {"name": item["name"], "latitude": item["latitude"], "longitude": item["longitude"],
             "country": item.get("country", "")}
            for item in response.json().get("results", [])
        ]
        if results:
            _PLACE_CACHE[cache_key] = results
            return results
        return []
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return [place for place in PRESETS if name.casefold() in place["name"].casefold()]


def _sample():
    """Explicitly requested demo dataset; never use it for a failed live request."""
    with open(SAMPLE_WEATHER, encoding="utf-8") as file:
        raw = json.load(file)
    daily = pd.DataFrame(raw["daily"])
    daily["date"] = pd.date_range(date.today()-timedelta(days=len(daily)-1), periods=len(daily), freq="D")
    daily["is_forecast"] = daily.index >= max(0, len(daily)-7)
    frame = daily.rename(columns={"precipitation_sum": "rain"})
    for column in ("rain_prob", "rain", "et0", "tmax", "tmin", "humidity", "wind"):
        if column not in frame:
            frame[column] = None
    frame["rain_only"] = frame["rain"]
    frame.attrs["current"] = {}
    frame.attrs["soil_moisture"] = {"surface_m3_m3": None, "deeper_m3_m3": None, "layers_m3_m3": {}, "time": None}
    frame.attrs["rain_last_24h_mm"] = None
    frame.attrs["updated_at"] = None
    frame.attrs["data_source"] = "SAMPLE WEATHER — demo mode; not local forecast data"
    return frame, frame.attrs["data_source"], 0


def _number(value):
    if value is None or pd.isna(value):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if pd.notna(result) else None


def _weighted_soil_moisture(hourly, timestamp, top_cm, bottom_cm):
    """Depth-weight hourly API layers over a requested depth; return m³/m³."""
    if hourly.empty or timestamp is None or not len(hourly):
        return None
    times = pd.to_datetime(hourly["time"], errors="coerce", utc=True)
    target = pd.to_datetime(timestamp, errors="coerce", utc=True)
    if pd.isna(target) or times.isna().all():
        return None
    prior = times[times <= target]
    chosen = prior.index[-1] if len(prior) else (times-target).abs().idxmin()
    weighted = 0.0
    depth_total = 0.0
    for layer, (layer_top, layer_bottom) in SOIL_LAYERS.items():
        depth = max(0, min(bottom_cm, layer_bottom) - max(top_cm, layer_top))
        if depth == 0:
            continue
        if layer not in hourly:
            return None
        value = _number(hourly.at[chosen, layer])
        if value is None:
            return None
        weighted += value * depth
        depth_total += depth
    if depth_total != bottom_cm - top_cm:
        return None
    return weighted / depth_total


def _latest_hour_index(hourly, timestamp=None):
    if hourly.empty:
        return None
    times = pd.to_datetime(hourly["time"], errors="coerce", utc=True)
    if times.isna().all():
        return None
    target = pd.to_datetime(timestamp, errors="coerce", utc=True) if timestamp is not None else pd.Timestamp.now(tz="UTC")
    if pd.isna(target):
        target = times.dropna().iloc[-1]
    prior = times[times <= target]
    return prior.index[-1] if len(prior) else (times-target).abs().idxmin()


def _normalize(payload):
    """Validate a forecast payload and return its daily series plus API metadata."""
    daily = payload.get("daily") or {}
    dates = daily.get("time") or []
    if not dates:
        raise ValueError("Weather response did not contain daily dates")
    count = len(dates)

    def daily_column(name, fallback=None):
        values = daily.get(name)
        if values is None or len(values) != count:
            return [fallback] * count
        return values

    precipitation = daily_column("precipitation_sum")
    rain_only = daily_column("rain_sum")
    if all(value is None for value in precipitation):
        precipitation = list(rain_only)
    current = payload.get("current") or {}
    hour_data = payload.get("hourly") or {}
    hour_times = hour_data.get("time") or []
    hourly = pd.DataFrame({"time": hour_times})
    for variable in HOURLY_VARIABLES.split(","):
        values = hour_data.get(variable)
        if values is not None and len(values) == len(hour_times):
            hourly[variable] = values

    # A few dates in Open-Meteo's rolling forecast history can lack daily ET₀
    # even though the hourly series has it. Sum those hours by local date; keep
    # missing data missing if the hourly series cannot supply that date.
    daily_et0 = daily_column("et0_fao_evapotranspiration")
    hourly_dates = None
    if "time" in hourly and len(hourly):
        hourly_dates = pd.to_datetime(hourly["time"], errors="coerce").dt.date
    if "et0_fao_evapotranspiration" in hourly and len(hourly):
        hourly_et0 = pd.to_numeric(hourly["et0_fao_evapotranspiration"], errors="coerce")
        hourly_et0_by_date = hourly_et0.groupby(hourly_dates).sum(min_count=1)
        daily_et0 = [
            value if _number(value) is not None else hourly_et0_by_date.get(pd.to_datetime(day).date())
            for day, value in zip(dates, daily_et0)
        ]
    if hourly_dates is not None:
        # Same-day hourly totals fill occasional nulls in daily precipitation.
        for daily_values, hourly_key in ((precipitation, "precipitation"), (rain_only, "rain")):
            if hourly_key not in hourly:
                continue
            hourly_values = pd.to_numeric(hourly[hourly_key], errors="coerce")
            totals = hourly_values.groupby(hourly_dates).sum(min_count=1)
            daily_values[:] = [
                value if _number(value) is not None else totals.get(pd.to_datetime(day).date())
                for day, value in zip(dates, daily_values)
            ]

    api_date = date.today()
    current_time = current.get("time")
    if current_time:
        parsed_current = pd.to_datetime(current_time, errors="coerce")
        if not pd.isna(parsed_current):
            api_date = parsed_current.date()

    frame = pd.DataFrame({
        "date": pd.to_datetime(dates, errors="coerce"),
        "tmax": daily_column("temperature_2m_max"),
        "tmin": daily_column("temperature_2m_min"),
        "rain": [_number(rain_value) if _number(rain_value) is not None else precipitation_value
                 for rain_value, precipitation_value in zip(rain_only, precipitation)],
        "precipitation": precipitation,
        "rain_prob": daily_column("precipitation_probability_max"),
        "et0": daily_et0,
        "humidity": daily_column("relative_humidity_2m_mean"),
        "wind": daily_column("wind_speed_10m_max"),
    })
    frame["is_forecast"] = frame["date"].dt.date >= api_date
    for column in ("tmax", "tmin", "rain", "precipitation", "rain_prob", "et0", "humidity", "wind"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if frame.empty or frame["date"].isna().any():
        raise ValueError("Weather response contains invalid dates")
    if frame["et0"].isna().any():
        raise ValueError("Weather response is missing daily reference evapotranspiration")
    if frame["precipitation"].isna().any():
        raise ValueError("Weather response is missing daily precipitation")

    hour_index = _latest_hour_index(hourly, current_time)
    reference_time = current_time
    if reference_time is None and hour_index is not None:
        reference_time = hourly.at[hour_index, "time"]

    def current_or_hourly(current_key, hourly_key):
        value = _number(current.get(current_key))
        if value is None and hour_index is not None and hourly_key in hourly:
            value = _number(hourly.at[hour_index, hourly_key])
        return value

    current_values = {
        "temperature_c": current_or_hourly("temperature_2m", "temperature_2m"),
        "humidity_pct": current_or_hourly("relative_humidity_2m", "relative_humidity_2m"),
        "precipitation_mm": current_or_hourly("precipitation", "precipitation"),
        "rain_mm": current_or_hourly("rain", "rain"),
        "wind_kmh": current_or_hourly("wind_speed_10m", "wind_speed_10m"),
        "time": reference_time,
        "interval_seconds": _number(current.get("interval")),
    }
    last_24h_rain = None
    if not hourly.empty and reference_time and ("rain" in hourly or "precipitation" in hourly):
        rain_column = "rain" if "rain" in hourly else "precipitation"
        times = pd.to_datetime(hourly["time"], errors="coerce", utc=True)
        now_utc = pd.to_datetime(reference_time, errors="coerce", utc=True)
        if not pd.isna(now_utc):
            mask = (times > now_utc - timedelta(hours=24)) & (times <= now_utc)
            values = pd.to_numeric(hourly.loc[mask, rain_column], errors="coerce")
            if len(values) and values.notna().all():
                last_24h_rain = float(values.sum())
    soil_moisture = {
        "surface_m3_m3": _weighted_soil_moisture(hourly, reference_time, 0, 7),
        "deeper_m3_m3": _weighted_soil_moisture(hourly, reference_time, 7, 28),
        "layers_m3_m3": {},
        "time": reference_time,
    }
    if hour_index is not None:
        soil_moisture["layers_m3_m3"] = {
            layer: _number(hourly.at[hour_index, layer])
            for layer in SOIL_LAYERS if layer in hourly
        }
    frame.attrs["current"] = current_values
    frame.attrs["soil_moisture"] = soil_moisture
    frame.attrs["rain_last_24h_mm"] = last_24h_rain
    frame.attrs["updated_at"] = reference_time
    return frame


def get_weather(latitude, longitude, past_days=60, forecast_days=7):
    """Fetch weather, then use a recent local cache; never substitute another place."""
    latitude, longitude = float(latitude), float(longitude)
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Enter a valid latitude and longitude")
    if OFFLINE:
        return _sample()

    key = hashlib.sha256(
        f"{latitude:.4f},{longitude:.4f},{past_days},{forecast_days}".encode()
    ).hexdigest()
    now = time.time()
    memory = _WEATHER_CACHE.get(key)
    if memory and now - memory[0] < CACHE_TTL_SECONDS:
        return memory[1].copy(), memory[2], int((now-memory[0])/3600)

    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = CACHE_DIR / f"{key}.json"
    except OSError:
        path = None
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": CURRENT_VARIABLES,
        "hourly": HOURLY_VARIABLES,
        "daily": DAILY_VARIABLES,
        "timezone": "auto",
        "past_days": past_days,
        "forecast_days": forecast_days,
    }
    try:
        response = requests.get(BASE, params=params, timeout=12)
        response.raise_for_status()
        payload = response.json()
        frame = _normalize(payload)
        fetched = time.time()
        if path is not None:
            try:
                path.write_text(json.dumps({"saved": fetched, "payload": payload}), encoding="utf-8")
            except OSError:
                pass
        source = "Live weather"
        frame.attrs["data_source"] = source
        _WEATHER_CACHE[key] = (fetched, frame.copy(), source)
        return frame, source, 0
    except (requests.RequestException, ValueError, KeyError, TypeError, AttributeError):
        if path is not None and path.exists():
            try:
                cached = json.loads(path.read_text(encoding="utf-8"))
                frame = _normalize(cached["payload"])
                age = max(0, int((now-cached["saved"])/3600))
                source = "Cached weather"
                frame.attrs["data_source"] = source
                return frame, source, age
            except (ValueError, KeyError, TypeError, OSError):
                pass
        return pd.DataFrame(), "WEATHER UNAVAILABLE — live forecast could not be reached", 0


async def get_weather_async(latitude, longitude, past_days=60, forecast_days=7):
    """Run the reusable network service off the Streamlit script thread."""
    return await asyncio.to_thread(get_weather, latitude, longitude, past_days, forecast_days)
