from datetime import date,timedelta
import pandas as pd
from core.harvest import harvest_weather_outlook
from core.soil_lookup import texture_class,lookup_soil
from core.vision import inspect_soil_photo

def test_harvest_outlook_flags_rain_near_estimated_date():
    today=date(2026,10,16); harvest=today+timedelta(days=3)
    weather=pd.DataFrame({"date":pd.to_datetime([today+timedelta(days=2),harvest]),"rain":[6,5],"is_forecast":[True,True]})
    result=harvest_weather_outlook(weather,"Tomato",today-timedelta(days=60),harvest,today)
    assert result["status"]=="Rain watch near harvest"
    assert result["date"]==harvest

def test_texture_mapping_uses_sand_and_clay_not_color():
    assert texture_class(76,8)=="Sandy"
    assert texture_class(20,45)=="Clay"
    assert texture_class(50,12)=="Sandy loam"

def test_soil_map_outage_returns_fallback(monkeypatch):
    import core.soil_lookup as soil
    monkeypatch.setattr(soil.requests,"get",lambda *a,**k: (_ for _ in ()).throw(soil.requests.Timeout()))
    soil.lookup_soil.cache_clear()
    assert lookup_soil(17.38,78.48) is None
    soil.lookup_soil.cache_clear()

def test_soil_map_uses_nearest_valid_paired_pixel(monkeypatch):
    import core.soil_lookup as soil
    from PIL import Image

    latitude, longitude = 17.385, 78.4867
    target_x, target_y = soil._goode_xy(latitude, longitude)
    sand = Image.new("I", (3, 3), 0)
    clay = Image.new("I", (3, 3), 0)
    sand.putpixel((1, 1), 350)
    clay.putpixel((1, 1), 375)
    origin = (target_x - 375, target_y + 375, 250, 250)
    slightly_different_origin = (target_x - 375 + 1e-6, target_y + 375, 250, 250)
    coverages = iter([(sand, origin), (clay, slightly_different_origin)])
    monkeypatch.setattr(soil, "_coverage", lambda *args: next(coverages))
    soil.lookup_soil.cache_clear()
    try:
        result = soil.lookup_soil(latitude, longitude)
    finally:
        soil.lookup_soil.cache_clear()
    assert result["soil"] == "Clay loam"
    assert result["distance_m"] == 0

def test_photo_analysis_explains_missing_api_key(monkeypatch):
    import core.vision as vision
    monkeypatch.setattr(vision,"GEMINI_API_KEY","")
    result,error=inspect_soil_photo(b"photo","image/jpeg","Loamy","No recent rain")
    assert result is None and "GEMINI_API_KEY" in error
