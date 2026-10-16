import streamlit as st
from core.db import init_db,list_farms,get_farm,get_events,get_observations
from core.weather import get_weather
from core.waterbalance import run_balance
from core.decision import decide
from core.crops import crop_status
from core.advisory import explain
from core.ui import page_header
init_db(); page_header("Ask about this advice", "Ask a simple question about the current estimate."); farms=list_farms()
if not farms: st.info("Set up a farm first."); st.stop()
fid=st.selectbox("Farm",[f['id'] for f in farms],format_func=lambda x:next(f['name'] for f in farms if f['id']==x)); farm=get_farm(fid); weather,source,_=get_weather(farm['latitude'],farm['longitude']); result=decide(run_balance(weather,farm,get_events(fid),get_observations(fid)),farm,crop_status(farm['sowing_date'],harvest_date=farm['harvest_date'],crop=farm['crop']))
lang=st.selectbox("Answer language",["English","Telugu","Hindi"]); question=st.text_input("Ask about the displayed estimate",placeholder="Why does the app recommend watering?")
if st.button("Explain",type="primary"):
    if question.strip():
        answer,kind=explain(question,result,farm,source,lang); st.caption(kind); st.write(answer)
    else: st.info("Enter a question first.")
st.caption("Answers explain this advisory only; they are not a substitute for local agricultural guidance.")
