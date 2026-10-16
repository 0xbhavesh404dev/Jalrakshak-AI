"""Transparent weather-based surface condition heuristic, not a soil sensor."""
import pandas as pd

def estimate_field_condition(weather):
    observed=weather.loc[~weather["is_forecast"].fillna(True)].copy()
    if observed.empty or "rain" not in observed:
        return {"label":"Not enough recent weather data","detail":"We need recent observed rainfall and temperature to estimate whether the surface may be wet or drying."}
    observed["rain"]=pd.to_numeric(observed["rain"],errors="coerce")
    for col in ("tmax","et0"):
        if col not in observed: observed[col]=float("nan")
        observed[col]=pd.to_numeric(observed[col],errors="coerce")
    recent=observed.dropna(subset=["rain"]).tail(3)
    if recent.empty:
        return {"label":"Not enough recent weather data","detail":"Recent rainfall values are missing, so the surface condition is unknown."}
    rain=float(recent.rain.sum()); latest=float(recent.rain.iloc[-1]); heat=float(recent.tmax.mean()) if recent.tmax.notna().any() else None; et=float(recent.et0.mean()) if recent.et0.notna().any() else None
    detail=f"Last {len(recent)} observed day(s): {rain:.1f} mm rain total."
    if latest>=5 or rain>=8:
        return {"label":"Likely wet","detail":detail+" Recent rainfall was substantial; check the field before watering."}
    if rain>=2:
        return {"label":"Likely drying","detail":detail+" Some rain fell, but the weather estimate cannot tell how much water remains in your soil."}
    if heat is not None and (heat>=32 or (et is not None and et>=5)):
        return {"label":"Likely dry","detail":detail+f" Recent average high was {heat:.1f}°C; heat and evaporation can dry the surface."}
    if heat is not None and (heat>=28 or (et is not None and et>=3.5)):
        return {"label":"Slightly dry","detail":detail+f" Recent average high was {heat:.1f}°C with little rain; the surface may be starting to dry."}
    return {"label":"No significant recent rain","detail":detail+" Surface may be drying; check the soil directly."}
