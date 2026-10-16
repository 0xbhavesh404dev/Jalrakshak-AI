import streamlit as st
from core.db import init_db,list_farms,get_farm,get_events,get_observations,add_irrigation,add_observation
from core.ui import apply_css, page_header

apply_css()
init_db()
page_header("Field notes", "Record watering or how the soil feels. These notes improve the next estimate.")
farms=list_farms()
if not farms:
    st.info("Set up a field before adding notes.")
    st.page_link("pages/1_Farm_Setup.py",label="Set up a field",icon="🌾")
    st.stop()
fid=st.selectbox("Choose your field",[f["id"] for f in farms],format_func=lambda x:next(f["name"] for f in farms if f["id"]==x))
farm=get_farm(fid)
st.caption(f"Notes are saved for {farm['name']} · {farm['place']}.")

with st.expander("Record watering",expanded=True):
    with st.form("irrigation"):
        watering_date=st.date_input("When did you water?")
        amount=st.number_input("Water applied (mm)",min_value=0.0,value=10.0,step=1.0)
        method=st.selectbox("How did you water?",["Drip","Sprinkler","Flood/furrow"])
        note=st.text_input("Optional note")
        save_water=st.form_submit_button("Save watering note",type="primary")
        if save_water:
            add_irrigation(fid,watering_date.isoformat(),amount,method,note)
            st.success("Watering saved.")

with st.expander("Record how the soil feels"):
    with st.form("soil_observation"):
        observation_date=st.date_input("When did you check?",key="observation_date")
        feel=st.selectbox("Soil feels",["moist","dry","wet"])
        save_observation=st.form_submit_button("Save soil note")
        if save_observation:
            add_observation(fid,observation_date.isoformat(),feel)
            st.success("Soil note saved.")

events=get_events(fid)[-5:][::-1]
observations=get_observations(fid)[-5:][::-1]
if events or observations:
    st.markdown("### Recent notes")
    for event in events:
        st.write(f"💧 **{event['date']}** · {event['gross_mm']:.1f} mm by {event['method']}")
    for obs in observations:
        st.write(f"🌱 **{obs['date']}** · Soil felt {obs['state']}")
else:
    st.caption("No notes yet. Add a watering or soil note when you visit the field.")
