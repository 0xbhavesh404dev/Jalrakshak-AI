import streamlit as st
import plotly.express as px
from core.db import init_db,list_farms,get_farm
from core.weather import get_weather
from core.ml import forecast_surface_moisture
from core.ui import page_header
init_db(); page_header("Weather", "See the weather data used in your field's estimate."); farms=list_farms()
if not farms: st.info("Set up a farm to view local weather."); st.stop()
fid=st.selectbox("Farm",[f["id"] for f in farms],format_func=lambda x:next(f["name"] for f in farms if f["id"]==x)); farm=get_farm(fid)
try:
    df,source,age=get_weather(farm["latitude"],farm["longitude"]); st.warning(source) if "OFFLINE" in source else st.caption(source+(f" · {age} hours old" if age else ""))
    st.plotly_chart(px.bar(df,x="date",y="rain",labels={"rain":"Rain (mm)","date":"Date"},title="Daily rainfall"),width="stretch")
    st.plotly_chart(px.line(df,x="date",y=["tmax","tmin"],labels={"value":"Temperature (°C)","date":"Date","variable":"Series"},title="Daily temperature"),width="stretch")
    soil=df.attrs.get("soil_moisture",{})
    if soil.get("surface_m3_m3") is not None or soil.get("deeper_m3_m3") is not None:
        a,b=st.columns(2)
        surface=soil.get("surface_m3_m3"); deeper=soil.get("deeper_m3_m3")
        a.metric("Modelled surface · 0–7 cm",f"{surface*100:.1f}%" if surface is not None else "Unavailable")
        b.metric("Modelled soil · 7–28 cm",f"{deeper*100:.1f}%" if deeper is not None else "Unavailable")
        st.caption("Open-Meteo modelled surface-layer moisture is separate from estimated root-zone storage and is not a physical sensor reading.")
    else:
        st.info("The weather model did not return current soil-moisture layers for this location.")
    ml=forecast_surface_moisture(None)
    st.info(ml["message"])
    st.dataframe(df,width="stretch",hide_index=True)
except Exception as e: st.error(f"Weather is unavailable: {e}")
