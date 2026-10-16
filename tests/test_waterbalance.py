import pandas as pd
from core.waterbalance import run_balance,depletion_from_modelled_profile
farm={"crop":"Tomato","soil":"Loamy","sowing_date":"2026-01-01","area_acres":1,"irrigation_method":"Drip"}
def weather(rain=0): return pd.DataFrame([{"date":pd.Timestamp("2026-01-31"),"et0":5,"rain":rain,"rain_prob":0,"is_forecast":False}])
def test_dry_and_rain_effect():
    dry=run_balance(weather(),farm,observations=[{"date":"2026-01-31","state":"dry"}]); wet=run_balance(weather(10),farm,observations=[{"date":"2026-01-31","state":"dry"}])
    assert dry.iloc[0].depletion>wet.iloc[0].depletion
    assert dry.iloc[0].storage+dry.iloc[0].depletion==dry.iloc[0].taw
def test_observation_reset():
    x=run_balance(weather(),farm,observations=[{"date":"2026-01-31","state":"wet"}]); assert x.iloc[0].depletion>0

def test_api_profile_maps_soil_texture_and_depth_to_root_depletion():
    profile={
        "soil_moisture_0_to_1cm":.26,"soil_moisture_1_to_3cm":.26,
        "soil_moisture_3_to_9cm":.26,"soil_moisture_9_to_27cm":.26,
        "soil_moisture_27_to_81cm":.26,
    }
    assert depletion_from_modelled_profile("Loamy",.5,profile)==0
    dry={layer:.12 for layer in profile}
    assert depletion_from_modelled_profile("Loamy",.5,dry)==70
    assert depletion_from_modelled_profile("Loamy",.9,dry) is None
