import pandas as pd
from core.decision import decide
def test_no_crop(): assert decide(pd.DataFrame(),{"area_acres":1},"fallow")["action"]=="NO_CROP"

def case(today_dep,today_raw,forecast_dep,forecast_raw,rain=0,prob=0):
    return pd.DataFrame([
        {"date":pd.Timestamp("2026-01-01"),"is_forecast":False,"depletion":today_dep,"raw":today_raw,"rain":0,"rain_prob":0},
        {"date":pd.Timestamp("2026-01-02"),"is_forecast":True,"depletion":forecast_dep,"raw":forecast_raw,"rain":rain,"rain_prob":prob},
    ])
farm={"area_acres":1,"irrigation_method":"Drip","soil":"Loamy"}
def test_stressed_action_and_rain_override():
    assert decide(case(10,5,11,5),farm)["action"]=="IRRIGATE_NOW"
    assert decide(case(10,5,11,5,8,90),farm)["action"]=="SKIP_RAIN_EXPECTED"
def test_upcoming_threshold_and_wait():
    assert decide(case(3,5,6,5),farm)["action"]=="IRRIGATE_SOON"
    assert decide(case(3,5,4,5),farm)["action"]=="WAIT"
def test_late_harvest_suppresses_amount_with_caution():
    x=decide(case(10,5,11,5),farm,"late_stage")
    assert x["action"]=="IRRIGATE_NOW" and x["gross_mm"] is None
    assert any("Near harvest" in r for r in x["reasons"])

def test_api_modelled_soil_moisture_rebases_current_irrigation_decision():
    balance=case(3,5,4,5)
    balance["root"]=[.5,.5]
    balance["taw"]=[70,70]
    profile={"time":"2026-01-01T12:00","layers_m3_m3":{
        "soil_moisture_0_to_1cm":.12,"soil_moisture_1_to_3cm":.12,
        "soil_moisture_3_to_9cm":.12,"soil_moisture_9_to_27cm":.12,
        "soil_moisture_27_to_81cm":.12,
    }}
    result=decide(balance,farm,soil_profile=profile)
    assert result["action"]=="IRRIGATE_NOW"
    assert result["soil_moisture_used"] is True
