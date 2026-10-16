from core.weather import _normalize,search_places
def test_weather_schema():
    p={"daily":{"time":["2026-01-01"],"temperature_2m_max":[20],"temperature_2m_min":[10],"precipitation_sum":[0],"et0_fao_evapotranspiration":[3]}}
    df=_normalize(p); assert df.iloc[0].tmax==20 and df.iloc[0].rain==0
def test_offline_geocoding_uses_presets(monkeypatch):
    import core.weather as w
    monkeypatch.setattr(w,"OFFLINE",True)
    assert search_places("nonexistent")==w.PRESETS

def test_free_request_uses_supported_current_hourly_and_daily_variables(monkeypatch, tmp_path):
    import core.weather as w
    w._WEATHER_CACHE.clear()
    monkeypatch.setattr(w, "OFFLINE", False)
    monkeypatch.setattr(w, "CACHE_DIR", tmp_path)
    seen = {}
    from datetime import date, datetime
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    time_value = now.isoformat(timespec="minutes")

    class Response:
        def raise_for_status(self): pass
        def json(self):
            return {
                "current": {"time": time_value, "temperature_2m": 29.5,
                    "relative_humidity_2m": 55, "precipitation": 0.2, "rain": 0.1,
                    "wind_speed_10m": 8.0, "interval": 900},
                "hourly": {"time": [time_value], "precipitation": [1.0],
                    "soil_moisture_0_to_1cm": [0.1], "soil_moisture_1_to_3cm": [0.2],
                    "soil_moisture_3_to_9cm": [0.3], "soil_moisture_9_to_27cm": [0.4],
                    "soil_moisture_27_to_81cm": [0.5]},
                "daily": {"time": [date.today().isoformat()], "temperature_2m_max": [30],
                    "temperature_2m_min": [20], "precipitation_sum": [2], "rain_sum": [2],
                    "precipitation_probability_max": [30], "et0_fao_evapotranspiration": [4],
                    "relative_humidity_2m_mean": [60], "wind_speed_10m_max": [12]},
            }

    def fake_get(url, params, timeout):
        seen.update(url=url, params=params)
        return Response()

    monkeypatch.setattr(w.requests, "get", fake_get)
    frame, source, _ = w.get_weather(17.385, 78.4867, past_days=0, forecast_days=0)
    assert source == "Live weather"
    assert seen["url"] == w.BASE
    assert "soil_moisture_3_to_9cm" in seen["params"]["hourly"]
    assert "soil_moisture_0_to_7cm_mean" not in seen["params"]["daily"]
    assert frame.attrs["current"]["temperature_c"] == 29.5
    assert frame.attrs["rain_last_24h_mm"] == 1.0
    assert abs(frame.attrs["soil_moisture"]["surface_m3_m3"] - (1.7/7)) < 0.001
    assert abs(frame.attrs["soil_moisture"]["deeper_m3_m3"] - (8.3/21)) < 0.001

def test_weather_connection_failure_does_not_use_wrong_location_demo(monkeypatch, tmp_path):
    import core.weather as w
    w._WEATHER_CACHE.clear()
    monkeypatch.setattr(w, "OFFLINE", False)
    monkeypatch.setattr(w, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(w.requests, "get", lambda *args, **kwargs: (_ for _ in ()).throw(w.requests.ConnectionError()))
    frame, source, _ = w.get_weather(17.385, 78.4867, past_days=0, forecast_days=0)
    assert frame.empty
    assert source.startswith("WEATHER UNAVAILABLE")

def test_invalid_location_is_rejected_before_request():
    import pytest
    from core.weather import get_weather
    with pytest.raises(ValueError):
        get_weather(91, 0)

def test_soil_moisture_can_be_missing_without_failing_weather():
    from core.weather import _normalize
    payload = {"daily": {"time": ["2026-10-16"], "et0_fao_evapotranspiration": [3.2],
        "temperature_2m_max": [29], "temperature_2m_min": [20], "precipitation_sum": [1]}}
    frame = _normalize(payload)
    assert frame.attrs["soil_moisture"]["surface_m3_m3"] is None
    assert frame.attrs["soil_moisture"]["deeper_m3_m3"] is None

def test_missing_daily_et0_and_rain_are_filled_from_hourly_totals():
    from core.weather import _normalize
    payload = {
        "daily": {"time": ["2026-10-16"], "et0_fao_evapotranspiration": [None],
            "precipitation_sum": [None], "rain_sum": [None]},
        "hourly": {"time": [f"2026-10-16T{hour:02}:00" for hour in range(3)],
            "et0_fao_evapotranspiration": [0.1, 0.2, 0.3],
            "precipitation": [0.0, 1.5, 0.5], "rain": [0.0, 1.2, 0.4]},
    }
    frame = _normalize(payload)
    assert frame.iloc[0].et0 == 0.6
    assert frame.iloc[0].precipitation == 2.0
    assert frame.iloc[0].rain == 1.6
