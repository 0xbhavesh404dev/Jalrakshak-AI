"""Local HTTP ingress for calibrated ESP32 readings; run separately from Streamlit."""
import hmac
import ipaddress
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from core.config import SENSOR_API_HOST, SENSOR_API_PORT, SENSOR_API_TOKEN
from core.db import init_db, latest_sensor_reading, save_sensor_reading, sensor_reading_history
from core.sensors import connection_state, normalize_reading

@asynccontextmanager
async def lifespan(_app):
    if not _is_loopback(SENSOR_API_HOST) and not SENSOR_API_TOKEN:
        raise RuntimeError("Set SENSOR_API_TOKEN before binding the sensor API beyond localhost")
    init_db()
    yield


app=FastAPI(title="JalRakshak Sensor API",version="1.0.0",docs_url=None,redoc_url=None,lifespan=lifespan)
_last_post_by_device={}


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "sensor-api",
        "health": "/health",
        "latest_reading": "/api/sensors/latest",
        "readings": "/api/sensors/readings",
    }


def _is_loopback(host):
    try: return ipaddress.ip_address(host).is_loopback
    except ValueError: return host.casefold() in {"localhost"}


def _authorize(authorization,client_host):
    # A token is enforced whenever configured. Also guard against someone
    # overriding Uvicorn's bind host from the CLI while leaving .env loopback-only.
    remote=not _is_loopback(client_host or "")
    if remote and not SENSOR_API_TOKEN:
        raise HTTPException(status_code=401,detail="Remote sensor access requires SENSOR_API_TOKEN")
    if SENSOR_API_TOKEN:
        expected=f"Bearer {SENSOR_API_TOKEN}"
        if not authorization or not hmac.compare_digest(authorization,expected):
            raise HTTPException(status_code=401,detail="Valid device authorization is required")


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    length=request.headers.get("content-length")
    if length:
        try:
            if int(length)>4096: return JSONResponse({"detail":"Request body is too large"},status_code=413)
        except ValueError:
            return JSONResponse({"detail":"Invalid Content-Length"},status_code=400)
    if request.method=="POST" and len(await request.body())>4096:
        return JSONResponse({"detail":"Request body is too large"},status_code=413)
    return await call_next(request)


@app.get("/health")
def health():
    try:
        init_db()
        return {"status":"ok","service":"sensor-api"}
    except Exception:
        return JSONResponse({"status":"unavailable","service":"sensor-api"},status_code=503)


@app.post("/api/sensors/readings",status_code=201)
def ingest_reading(payload: dict,request: Request, authorization: str | None=Header(default=None)):
    _authorize(authorization,request.client.host if request.client else None)
    try:
        reading=normalize_reading(payload)
        now=datetime.now(timezone.utc).timestamp()
        prior=_last_post_by_device.get(reading["device_id"])
        if prior is not None and now-prior<1.0:
            raise HTTPException(status_code=429,detail="Send no more than one reading per device each second")
        saved=save_sensor_reading(reading)
        _last_post_by_device[reading["device_id"]]=now
    except ValueError as exc:
        raise HTTPException(status_code=422,detail=str(exc)) from exc
    except HTTPException:
        raise
    except (TypeError,KeyError,json.JSONDecodeError):
        raise HTTPException(status_code=400,detail="Malformed sensor reading") from None
    return {"status":"stored","reading":saved}


@app.get("/api/sensors/latest")
def latest(request: Request,device_id: str | None=None, authorization: str | None=Header(default=None)):
    _authorize(authorization,request.client.host if request.client else None)
    reading=latest_sensor_reading(device_id)
    if reading is None: return {"status":"missing","reading":None,"connection":connection_state(None)}
    return {"status":"ok","reading":reading,"connection":connection_state(reading)}


@app.get("/api/sensors/history")
def history(request: Request,limit: int=Query(default=50,ge=1,le=500),device_id: str | None=None,
            authorization: str | None=Header(default=None)):
    _authorize(authorization,request.client.host if request.client else None)
    return {"status":"ok","readings":sensor_reading_history(limit,device_id)}


if __name__=="__main__":
    import uvicorn
    uvicorn.run("sensor_api:app",host=SENSOR_API_HOST,port=SENSOR_API_PORT,reload=False)
