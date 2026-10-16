import pandas as pd
PRESETS={"Normal":(0,1,0),"Heatwave":(5,1,0),"Failed Monsoon":(2,0,7),"Monsoon Burst":(0,2.5,0),"Rain Tomorrow":(0,1,0),"Recent Harvest":(0,1,0)}

def scenario_weather(weather_df,name="Normal",temp_delta=None,rain_multiplier=None,dry_spell=None):
    dt,rm,ds=PRESETS[name]
    dt=dt if temp_delta is None else temp_delta; rm=rm if rain_multiplier is None else rain_multiplier
    out=weather_df.copy(deep=True); forecast=out["is_forecast"].astype(bool)
    for col in ("tmax","tmin","rain","et0"):
        out[col]=pd.to_numeric(out[col],errors="coerce").astype(float)
    if ds is not None: dry_spell=ds
    if dry_spell is not None and dry_spell>0:
        idx=out.index[forecast][:int(dry_spell)]; out.loc[idx,"rain"]=0
    if dt: out.loc[forecast,"tmax"]+=dt; out.loc[forecast,"tmin"]+=dt
    out.loc[forecast,"et0"]*=1+0.04*dt
    out.loc[forecast,"rain"]*=rm
    return out
