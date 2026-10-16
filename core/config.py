from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
DATA_DIR = ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
SAMPLE_WEATHER = DATA_DIR / "sample_weather_hyderabad.json"
DB_PATH = Path(os.getenv("JALRAKSHAK_DB", str(DATA_DIR / "jalrakshak.sqlite3")))
OFFLINE = os.getenv("JALRAKSHAK_OFFLINE", "0").strip() == "1"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
SENSOR_API_HOST = os.getenv("SENSOR_API_HOST", "127.0.0.1").strip()
SENSOR_API_PORT = int(os.getenv("SENSOR_API_PORT", "8000"))
SENSOR_API_BASE_URL = os.getenv("SENSOR_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
SENSOR_API_TOKEN = os.getenv("SENSOR_API_TOKEN", "").strip()
SENSOR_STALE_SECONDS = max(30, int(os.getenv("SENSOR_STALE_SECONDS", "120")))
SENSOR_DEMO_MODE = os.getenv("SENSOR_DEMO_MODE", "0").strip() == "1"
SENSOR_DRY_THRESHOLD_PERCENT = float(os.getenv("SENSOR_DRY_THRESHOLD_PERCENT", "30"))
DISCLAIMER = ("This is an estimate based on weather data and standard crop parameters. "
              "Check the soil in the field before irrigating and follow local agricultural advice.")
