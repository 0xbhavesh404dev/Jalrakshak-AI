import pandas as pd
from core.simulator import scenario_weather
def test_history_preserved_and_heat_increases_et0():
    df=pd.DataFrame([{"date":pd.Timestamp("2026-01-01"),"is_forecast":False,"tmax":20,"tmin":10,"rain":2,"et0":3},{"date":pd.Timestamp("2026-01-02"),"is_forecast":True,"tmax":20,"tmin":10,"rain":2,"et0":3}]); out=scenario_weather(df,"Heatwave"); assert out.iloc[0].tmax==20 and out.iloc[1].et0>3
