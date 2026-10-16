import sqlite3, json
from contextlib import contextmanager
from datetime import date, datetime, timezone
from .config import DB_PATH

def connect():
    DB_PATH.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return _closing_connection(c)

@contextmanager
def _closing_connection(connection):
    try:
        with connection:
            yield connection
    finally:
        connection.close()
def init_db():
    with connect() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS farms(id INTEGER PRIMARY KEY,name TEXT NOT NULL,place TEXT NOT NULL,latitude REAL NOT NULL,longitude REAL NOT NULL,crop TEXT NOT NULL,soil TEXT NOT NULL,irrigation_method TEXT NOT NULL,area_acres REAL NOT NULL CHECK(area_acres>0),sowing_date TEXT NOT NULL,harvest_date TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS irrigation_events(id INTEGER PRIMARY KEY,farm_id INTEGER NOT NULL REFERENCES farms(id) ON DELETE CASCADE,date TEXT NOT NULL,gross_mm REAL NOT NULL CHECK(gross_mm>=0),method TEXT NOT NULL,note TEXT);
        CREATE TABLE IF NOT EXISTS observations(id INTEGER PRIMARY KEY,farm_id INTEGER NOT NULL REFERENCES farms(id) ON DELETE CASCADE,date TEXT NOT NULL,state TEXT NOT NULL CHECK(state IN ('dry','moist','wet')));
        CREATE TABLE IF NOT EXISTS harvest_events(id INTEGER PRIMARY KEY,farm_id INTEGER NOT NULL REFERENCES farms(id) ON DELETE CASCADE,date TEXT NOT NULL,place TEXT NOT NULL,latitude REAL NOT NULL,longitude REAL NOT NULL,UNIQUE(farm_id,date));
        CREATE TABLE IF NOT EXISTS recommendations(id INTEGER PRIMARY KEY,farm_id INTEGER NOT NULL REFERENCES farms(id) ON DELETE CASCADE,date TEXT NOT NULL,action TEXT NOT NULL,net_mm REAL,gross_mm REAL,litres REAL,data_quality TEXT NOT NULL,payload TEXT NOT NULL,UNIQUE(farm_id,date));
        CREATE TABLE IF NOT EXISTS sensor_readings(
          id INTEGER PRIMARY KEY,
          device_id TEXT NOT NULL,
          timestamp TEXT NOT NULL,
          received_at TEXT NOT NULL,
          soil_moisture_percent REAL NOT NULL CHECK(soil_moisture_percent BETWEEN 0 AND 100),
          temperature_c REAL NOT NULL CHECK(temperature_c BETWEEN -20 AND 80),
          humidity_percent REAL NOT NULL CHECK(humidity_percent BETWEEN 0 AND 100),
          raw_adc INTEGER,
          sequence INTEGER,
          calibrated INTEGER NOT NULL DEFAULT 0 CHECK(calibrated IN (0,1)),
          demo INTEGER NOT NULL DEFAULT 0 CHECK(demo IN (0,1)),
          UNIQUE(device_id,timestamp)
        );
        CREATE INDEX IF NOT EXISTS sensor_readings_time_idx ON sensor_readings(device_id,timestamp DESC);''')

def save_sensor_reading(reading, received_at=None):
    received_at = received_at or datetime.now(timezone.utc).isoformat()
    with connect() as c:
        c.execute("""INSERT INTO sensor_readings
          (device_id,timestamp,received_at,soil_moisture_percent,temperature_c,humidity_percent,raw_adc,sequence,calibrated,demo)
          VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(device_id,timestamp) DO UPDATE SET
          received_at=excluded.received_at,soil_moisture_percent=excluded.soil_moisture_percent,
          temperature_c=excluded.temperature_c,humidity_percent=excluded.humidity_percent,
          raw_adc=excluded.raw_adc,sequence=excluded.sequence,calibrated=excluded.calibrated,demo=excluded.demo""",
          (reading["device_id"], reading["timestamp"], received_at, reading["soil_moisture_percent"],
           reading["temperature_c"], reading["humidity_percent"], reading.get("raw_adc"),
           reading.get("sequence"), int(bool(reading.get("calibrated", False))), int(bool(reading.get("demo", False)))))
        row=c.execute("SELECT * FROM sensor_readings WHERE device_id=? AND timestamp=?",(reading["device_id"],reading["timestamp"])).fetchone()
        return dict(row)

def latest_sensor_reading(device_id=None):
    with connect() as c:
        if device_id:
            row=c.execute("SELECT * FROM sensor_readings WHERE device_id=? ORDER BY timestamp DESC,id DESC LIMIT 1",(device_id,)).fetchone()
        else:
            row=c.execute("SELECT * FROM sensor_readings ORDER BY timestamp DESC,id DESC LIMIT 1").fetchone()
        return dict(row) if row else None

def sensor_reading_history(limit=50, device_id=None):
    limit=max(1,min(int(limit),500))
    with connect() as c:
        if device_id:
            rows=c.execute("SELECT * FROM sensor_readings WHERE device_id=? ORDER BY timestamp DESC,id DESC LIMIT ?",(device_id,limit)).fetchall()
        else:
            rows=c.execute("SELECT * FROM sensor_readings ORDER BY timestamp DESC,id DESC LIMIT ?",(limit,)).fetchall()
        return [dict(row) for row in rows]
def save_farm(farm):
    required=("name","place","latitude","longitude","crop","soil","irrigation_method","area_acres","sowing_date")
    if any(k not in farm for k in required): raise ValueError("Missing farm fields")
    if float(farm["area_acres"])<=0: raise ValueError("Area must be positive")
    sowing=date.fromisoformat(str(farm["sowing_date"]))
    if farm.get("harvest_date"):
        harvest=date.fromisoformat(str(farm["harvest_date"]))
        if harvest < sowing: raise ValueError("Harvest date cannot be before sowing date")
    with connect() as c:
        cur=c.execute("INSERT INTO farms(name,place,latitude,longitude,crop,soil,irrigation_method,area_acres,sowing_date,harvest_date) VALUES(?,?,?,?,?,?,?,?,?,?)",tuple(farm.get(k) for k in required)+(farm.get("harvest_date"),)); return cur.lastrowid
def list_farms():
    with connect() as c: return [dict(r) for r in c.execute("SELECT * FROM farms ORDER BY id DESC")]
def get_farm(farm_id):
    with connect() as c:
        r=c.execute("SELECT * FROM farms WHERE id=?",(farm_id,)).fetchone(); return dict(r) if r else None
def delete_farm(farm_id):
    with connect() as c: c.execute("DELETE FROM farms WHERE id=?",(farm_id,))
def update_farm(farm_id,farm):
    if float(farm["area_acres"])<=0: raise ValueError("Area must be positive")
    sowing=date.fromisoformat(str(farm["sowing_date"]))
    if farm.get("harvest_date") and date.fromisoformat(str(farm["harvest_date"])) < sowing: raise ValueError("Harvest date cannot be before sowing date")
    with connect() as c: c.execute("UPDATE farms SET name=?,place=?,latitude=?,longitude=?,crop=?,soil=?,irrigation_method=?,area_acres=?,sowing_date=?,harvest_date=? WHERE id=?",tuple(farm[k] for k in ("name","place","latitude","longitude","crop","soil","irrigation_method","area_acres","sowing_date"))+(farm.get("harvest_date"),farm_id))
def add_irrigation(farm_id,day,gross_mm,method,note=""):
    if gross_mm<0: raise ValueError("Irrigation cannot be negative")
    with connect() as c: c.execute("INSERT INTO irrigation_events(farm_id,date,gross_mm,method,note) VALUES(?,?,?,?,?)",(farm_id,str(day),gross_mm,method,note))
def add_observation(farm_id,day,state):
    if state not in ("dry","moist","wet"): raise ValueError("Invalid observation state")
    with connect() as c: c.execute("INSERT INTO observations(farm_id,date,state) VALUES(?,?,?)",(farm_id,str(day),state))
def get_events(farm_id):
    with connect() as c: return [dict(r) for r in c.execute("SELECT * FROM irrigation_events WHERE farm_id=? ORDER BY date",(farm_id,))]
def get_observations(farm_id):
    with connect() as c: return [dict(r) for r in c.execute("SELECT * FROM observations WHERE farm_id=? ORDER BY date",(farm_id,))]
def mark_harvested_today(farm_id,day=None):
    day=date.fromisoformat(str(day)) if day else date.today()
    with connect() as c:
        farm=c.execute("SELECT * FROM farms WHERE id=?",(farm_id,)).fetchone()
        if farm is None: raise ValueError("Unknown farm")
        c.execute("INSERT INTO harvest_events(farm_id,date,place,latitude,longitude) VALUES(?,?,?,?,?) ON CONFLICT(farm_id,date) DO UPDATE SET place=excluded.place,latitude=excluded.latitude,longitude=excluded.longitude",(farm_id,day.isoformat(),farm["place"],farm["latitude"],farm["longitude"]))
        c.execute("UPDATE farms SET harvest_date=? WHERE id=?",(day.isoformat(),farm_id))
        return dict(c.execute("SELECT * FROM harvest_events WHERE farm_id=? AND date=?",(farm_id,day.isoformat())).fetchone())
def get_harvest_event(farm_id,day=None):
    day=date.fromisoformat(str(day)) if day else date.today()
    with connect() as c:
        row=c.execute("SELECT * FROM harvest_events WHERE farm_id=? AND date=?",(farm_id,day.isoformat())).fetchone()
        return dict(row) if row else None
def save_recommendation(farm_id,day,result,data_quality="Medium"):
    with connect() as c: c.execute("INSERT INTO recommendations(farm_id,date,action,net_mm,gross_mm,litres,data_quality,payload) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(farm_id,date) DO UPDATE SET action=excluded.action,net_mm=excluded.net_mm,gross_mm=excluded.gross_mm,litres=excluded.litres,data_quality=excluded.data_quality,payload=excluded.payload",(farm_id,str(day),result["action"],result.get("net_mm"),result.get("gross_mm"),result.get("litres"),data_quality,json.dumps(result)))
def history(farm_id):
    with connect() as c: return [dict(r) for r in c.execute("SELECT * FROM recommendations WHERE farm_id=? ORDER BY date DESC",(farm_id,))]
