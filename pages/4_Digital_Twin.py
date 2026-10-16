import streamlit as st
import plotly.express as px
from core.db import init_db,list_farms,get_farm,get_events,get_observations
from core.weather import get_weather
from core.simulator import PRESETS,scenario_weather
from core.waterbalance import run_balance
from core.decision import decide,ACTION_LABELS
from core.crops import crop_status
from core.ui import page_header
init_db(); page_header("Try a weather scenario", "Explore how hotter or wetter forecast conditions could change the estimate.")
st.caption("This is a what-if exercise. It does not change the saved forecast or past field notes."); farms=list_farms()
if not farms: st.info("Set up a farm first."); st.stop()
fid=st.selectbox("Farm",[f["id"] for f in farms],format_func=lambda x:next(f["name"] for f in farms if f["id"]==x)); farm=get_farm(fid); base,source,_=get_weather(farm["latitude"],farm["longitude"])
preset=st.selectbox("Choose a what-if situation",list(PRESETS)); dt=st.slider("How much hotter? (°C)",0,10,PRESETS[preset][0]); rain=st.slider("Rain compared with the forecast",0.0,3.0,float(PRESETS[preset][1]),.1); dry=st.slider("Start with this many dry days",0,7,int(PRESETS[preset][2] or 0))
sim=scenario_weather(base,preset,dt,rain,dry); st.warning("SIMULATED SCENARIO — not a real weather forecast. Temperature-to-ET0 changes are approximations."); events=get_events(fid); obs=get_observations(fid); b=run_balance(base,farm,events,obs); s=run_balance(sim,farm,events,obs)
st.caption(f"Base source: {source}. Historical weather and observations are not changed."); left,right=st.columns(2); status=crop_status(farm['sowing_date'],harvest_date=farm['harvest_date'],crop=farm['crop'])
left.metric("Base recommendation",ACTION_LABELS[decide(b,farm,status)['action']]); right.metric("Scenario recommendation",ACTION_LABELS[decide(s,farm,status)['action']])
combo=s[['date','storage']].rename(columns={'storage':'Scenario'}).merge(b[['date','storage']].rename(columns={'storage':'Base'}),on='date'); st.plotly_chart(px.line(combo,x='date',y=['Base','Scenario'],labels={'value':'Estimated root-zone storage (mm)'},title='Base and simulated storage'),width="stretch")
