from datetime import date, timedelta
from .crops import estimated_harvest

def harvest_weather_outlook(weather, crop, sowing_date, expected_harvest=None, today=None):
    """Show crop-calendar harvest estimate plus rain watch near the harvest date."""
    today=today or date.today()
    base=date.fromisoformat(str(expected_harvest)) if expected_harvest else estimated_harvest(crop,date.fromisoformat(str(sowing_date)))
    forecast=weather.loc[weather["is_forecast"].fillna(False)].copy()
    forecast["date"]=forecast["date"].apply(lambda d:d.date() if hasattr(d,"date") else date.fromisoformat(str(d)[:10]))
    forecast=forecast.loc[(forecast["date"]>=today)&(forecast["date"]<=base+timedelta(days=7))]
    if base < today-timedelta(days=7):
        return {"date":base,"status":"Estimated date has passed","detail":"The crop calendar estimate has passed. Check crop maturity in the field; local variety and growing conditions can shift the date."}
    if (base-today).days>7:
        return {"date":base,"status":"Not near the expected harvest window yet","detail":"This date comes from the crop's standard growing duration. Recheck the forecast as the window gets closer."}
    rain=float(forecast["rain"].fillna(0).sum()) if len(forecast) and "rain" in forecast else 0.0
    if rain>=10:
        status="Rain watch near harvest"
        detail=f"The forecast shows about {rain:.1f} mm rain through the next available days near the estimated date. Check field access and crop-specific harvest guidance."
    elif len(forecast):
        status="No major rain in the current forecast window"
        detail=f"About {rain:.1f} mm rain is forecast through the available days near the estimated date. This is a weather watch, not a maturity check."
    else:
        status="Forecast window unavailable"
        detail="The current weather record does not cover the estimated harvest date."
    return {"date":base,"status":status,"detail":detail}
