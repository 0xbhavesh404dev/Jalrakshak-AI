from .soils import efficiency,litres
from .waterbalance import depletion_from_modelled_profile

ACTION_LABELS={"NO_CROP":"NO ACTIVE CROP","IRRIGATE_NOW":"IRRIGATE NOW","IRRIGATE_SOON":"IRRIGATE SOON","WAIT":"WAIT","SKIP_RAIN_EXPECTED":"RAIN EXPECTED — RECHECK"}

def decide(balance,farm,status="growing",soil_profile=None):
    if status in ("not_yet_sown","fallow","harvested"): return {"action":"NO_CROP","reasons":["No active crop is recorded for today."],"net_mm":None,"gross_mm":None,"litres":None,"reassess":"After planting or recording the active crop."}
    if balance.empty: return {"action":"WAIT","reasons":["Weather projection is unavailable."],"net_mm":None,"gross_mm":None,"litres":None,"reassess":"Check weather data and try again."}
    target_date=None
    if soil_profile and soil_profile.get("time"):
        import pandas as pd
        parsed=pd.to_datetime(soil_profile["time"],errors="coerce")
        if not pd.isna(parsed): target_date=parsed.date()
    today_rows=balance[balance.date.dt.date==target_date] if target_date else balance.iloc[0:0]
    historical=balance[~balance.is_forecast]
    today=today_rows.iloc[0] if len(today_rows) else (historical.iloc[-1] if len(historical) else balance.iloc[0])
    future=balance[(balance.is_forecast)&(balance.date>today.date)]
    api_depletion=depletion_from_modelled_profile(farm["soil"],float(today.root),soil_profile.get("layers_m3_m3",{})) if soil_profile else None
    current_depletion=float(api_depletion) if api_depletion is not None else float(today.depletion)
    future_depletion=future.depletion
    if api_depletion is not None and len(future):
        # Rebase the existing crop/weather projection on today's API model state.
        offset=current_depletion-float(today.depletion)
        future_depletion=(future.depletion+offset).clip(lower=0)
        if "taw" in future:
            future_depletion=future_depletion.where(future_depletion<=future.taw,future.taw)
    irrig=bool(current_depletion>today.raw)
    likely_rain=(future.rain>=2)&(future.rain_prob.fillna(0)>=60) if len(future) else None
    # Do not defer irrigation just because any rain is forecast. Only defer when
    # the water-balance projection says that likely rain keeps depletion below
    # the crop threshold after accounting for forecast amount and crop water use.
    rain_relief=likely_rain&(future_depletion<=future.raw) if likely_rain is not None else None
    rainsoon=bool(rain_relief.head(3).any()) if rain_relief is not None else False
    likely_rainsoon=bool(likely_rain.head(3).any()) if likely_rain is not None else False
    if irrig and rainsoon: action="SKIP_RAIN_EXPECTED"; reasons=["Estimated depletion is above the crop threshold.","Likely near-term rain is projected to bring depletion below the crop threshold; check the field after the rain."]
    elif irrig:
        action="IRRIGATE_NOW"
        reasons=["Estimated root-zone depletion is above the readily available water threshold.","Forecast rain is too small to offset the estimated crop water deficit; check the soil before watering." if likely_rainsoon else "No sufficiently likely near-term rain was found."]
    else:
        crossed=future[future_depletion>future.raw]
        if len(crossed) and (crossed.iloc[0].date-today.date).days<=1: action="IRRIGATE_SOON"; reasons=["The projection approaches the crop water threshold within 24 hours."]
        else: action="WAIT"; reasons=["Estimated storage is currently above the crop threshold.","Reassess as the forecast changes."]
    net=max(0,current_depletion-float(today.raw)) if action in ("IRRIGATE_NOW","IRRIGATE_SOON") else None
    gross=net/efficiency(farm["irrigation_method"]) if net is not None else None
    if status=="late_stage":
        reasons.append("Near harvest: avoid a large irrigation based only on this estimate; follow crop-specific local guidance.")
        net=gross=None
    return {"action":action,"reasons":reasons,"net_mm":net,"gross_mm":gross,"litres":litres(gross,float(farm["area_acres"])) if gross is not None else None,"soil_moisture_used":api_depletion is not None,"reassess":"After expected rain" if action=="SKIP_RAIN_EXPECTED" else ("Check with local agricultural guidance before watering." if status=="late_stage" else "Tomorrow, or sooner if conditions change.")}
