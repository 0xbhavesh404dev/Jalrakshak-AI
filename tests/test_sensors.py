from datetime import datetime, timedelta, timezone

import pytest

from core.db import init_db, latest_sensor_reading, save_sensor_reading, sensor_reading_history
from core.sensors import connection_state, irrigation_prediction, normalize_reading


def payload(**changes):
    value={"device_id":"esp32-a","timestamp":datetime.now(timezone.utc).isoformat(),
        "soil_moisture_percent":42,"temperature_c":30.5,"humidity_percent":60,
        "raw_adc":1800,"sequence":1,"calibrated":True}
    value.update(changes)
    return value


def test_payload_validation_and_timestamp_normalization():
    reading=normalize_reading(payload())
    assert reading["timestamp"].endswith("+00:00")
    assert reading["calibrated"] is True
    for bad in ({"soil_moisture_percent":float("nan")},{"temperature_c":81},
                {"temperature_c":-1},{"humidity_percent":-1},{"humidity_percent":91},
                {"soil_moisture_percent":"42"},{"device_id":""},{"timestamp":"bad"},
                {"timestamp":"2026-10-16T10:00:00"},{"raw_adc":4096}):
        with pytest.raises(ValueError): normalize_reading(payload(**bad))


def test_timestamp_may_be_replaced_by_sequence():
    received=datetime.now(timezone.utc)
    reading=normalize_reading({k:v for k,v in payload().items() if k!="timestamp"},received_at=received)
    assert reading["timestamp"]==received.isoformat()


def test_sensor_readings_persist_and_duplicate_timestamp_is_idempotent():
    init_db()
    reading=normalize_reading(payload())
    first=save_sensor_reading(reading)
    second=save_sensor_reading({**reading,"soil_moisture_percent":44})
    assert first["id"]==second["id"]
    assert latest_sensor_reading("esp32-a")["soil_moisture_percent"]==44
    assert len(sensor_reading_history(50,"esp32-a"))==1


def test_stale_and_missing_sensor_state():
    now=datetime.now(timezone.utc)
    old={"timestamp":(now-timedelta(seconds=121)).isoformat()}
    assert connection_state(old,now,120)["state"]=="Stale"
    assert connection_state(None,now)["state"]=="Disconnected"


def test_prediction_needs_calibration_freshness_and_conflict_review():
    now=datetime.now(timezone.utc)
    reading=normalize_reading(payload(timestamp=now.isoformat()))
    assert irrigation_prediction(reading,{"stress":False},now)["status"]=="NO IRRIGATION NEEDED"
    assert irrigation_prediction({**reading,"soil_moisture_percent":20},{"stress":False},now)["status"]=="INSUFFICIENT DATA"
    assert irrigation_prediction({**reading,"calibrated":False},None,now)["status"]=="INSUFFICIENT DATA"
    assert irrigation_prediction({**reading,"timestamp":(now-timedelta(minutes=5)).isoformat()},None,now)["status"]=="INSUFFICIENT DATA"
    assert irrigation_prediction({**reading,"demo":True},None,now)["status"]=="INSUFFICIENT DATA"
    assert irrigation_prediction(None,None,now,active_crop=False)["status"]=="NO IRRIGATION NEEDED"


def test_sensor_api_validates_ingests_latest_and_history(monkeypatch):
    from fastapi.testclient import TestClient
    import sensor_api
    monkeypatch.setattr(sensor_api,"SENSOR_API_HOST","127.0.0.1")
    monkeypatch.setattr(sensor_api,"SENSOR_API_TOKEN","")
    monkeypatch.setattr(sensor_api,"_is_loopback",lambda _host: True)
    with TestClient(sensor_api.app) as client:
        assert client.get("/health").json()["status"]=="ok"
        good=payload(timestamp=datetime.now(timezone.utc).isoformat())
        assert client.post("/api/sensors/readings",json=good).status_code==201
        repeated=client.post("/api/sensors/readings",json={**good,"timestamp":datetime.now(timezone.utc).isoformat(),"sequence":2})
        assert repeated.status_code==429
        assert client.get("/api/sensors/latest?device_id=esp32-a").json()["reading"]["device_id"]=="esp32-a"
        assert len(client.get("/api/sensors/history?device_id=esp32-a").json()["readings"])==1
        invalid=client.post("/api/sensors/readings",json=payload(temperature_c=200))
        assert invalid.status_code==422


def test_non_loopback_sensor_api_requires_token(monkeypatch):
    from fastapi import HTTPException
    import sensor_api
    monkeypatch.setattr(sensor_api,"SENSOR_API_TOKEN","secret")
    with pytest.raises(HTTPException): sensor_api._authorize(None,"192.168.1.25")
    sensor_api._authorize("Bearer secret","192.168.1.25")
    monkeypatch.setattr(sensor_api,"SENSOR_API_TOKEN","")
    with pytest.raises(HTTPException): sensor_api._authorize(None,"192.168.1.25")
