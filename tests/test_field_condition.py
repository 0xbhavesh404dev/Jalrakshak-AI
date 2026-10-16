import pandas as pd
from core.field_condition import estimate_field_condition

def frame(rain,tmax):
    return pd.DataFrame({"rain":rain,"tmax":tmax,"et0":[4.0]*len(rain),"is_forecast":[False]*len(rain)})

def test_recent_heavy_rain_means_likely_wet():
    assert estimate_field_condition(frame([0,0,6],[28,29,28]))["label"]=="Likely wet"

def test_hot_weather_without_rain_means_likely_dry():
    assert estimate_field_condition(frame([0,0,0],[34,35,36]))["label"]=="Likely dry"

def test_some_rain_means_likely_drying():
    assert estimate_field_condition(frame([0,1,1],[28,30,31]))["label"]=="Likely drying"

def test_warm_weather_with_no_rain_means_slightly_dry():
    assert estimate_field_condition(frame([0,0,0],[29,30,31]))["label"]=="Slightly dry"

def test_forecast_is_not_used_as_observation():
    data=frame([8],[38]); data["is_forecast"]=True
    assert estimate_field_condition(data)["label"]=="Not enough recent weather data"
