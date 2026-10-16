import streamlit as st
from datetime import date
from core.db import init_db,save_farm,list_farms,delete_farm
from core.crops import CROPS
from core.soils import SOILS,EFFICIENCY
from core.weather import search_places,PRESETS
from core.geolocation import browser_location
from core.soil_lookup import lookup_soil
from core.ui import apply_css, page_header
apply_css()
init_db()
page_header("Step 1 · Set up your farm", "This takes about one minute. Your details are saved on this computer.")
st.caption("Start with where the field is, then add the crop and soil details. The estimates are only as good as these inputs.")

st.markdown("#### 1. Choose the field location")
location_mode=st.radio("How do you want to set the location?",["Search for a town or village","Use my current location","Enter coordinates"],horizontal=True,label_visibility="collapsed")
location_ready=True
if location_mode=="Search for a town or village":
    query=st.text_input("Town or village",value=st.session_state.get("place_query","Hyderabad"),help="Enter a name, then press Search. Location search needs an internet connection.")
    st.session_state["place_query"]=query
    if st.button("Search locations",key="search_locations"):
        with st.spinner("Searching places…"):
            st.session_state["place_results"]=search_places(query)
        st.session_state["searched_place_query"]=query
    results=st.session_state.get("place_results",PRESETS)
    if not results:
        selected=None
        location_ready=False
        st.warning("No matching place was found. Check the spelling or switch to Enter coordinates.")
    else:
        if st.session_state.get("searched_place_query")==query and not any(query.casefold() in x["name"].casefold() for x in results):
            st.warning("No exact name match. Choose a nearby result or enter coordinates.")
        selected=st.selectbox("Choose the nearest match",results,format_func=lambda x:f"{x['name']}, {x.get('country','')} · {x['latitude']:.4f}, {x['longitude']:.4f}")
elif location_mode=="Enter coordinates":
    manual_place=st.text_input("Name this location",value=st.session_state.get("place_query","My field location"))
    lat,lon=st.columns(2)
    latitude=lat.number_input("Latitude",min_value=-90.0,max_value=90.0,value=17.385,format="%.5f")
    longitude=lon.number_input("Longitude",min_value=-180.0,max_value=180.0,value=78.4867,format="%.5f")
    selected={"name":manual_place.strip() or "Custom location","country":"Custom coordinates","latitude":latitude,"longitude":longitude}
else:
    location_result=browser_location(key="farm_setup_geolocation")
    if location_result and "latitude" in location_result and "longitude" in location_result:
        selected={"name":"My current location","country":"Browser GPS","latitude":float(location_result["latitude"]),"longitude":float(location_result["longitude"])}
        st.success(f"Current location received (±{float(location_result.get('accuracy',0)):.0f} m): {selected['latitude']:.5f}, {selected['longitude']:.5f}")
    else:
        selected=None
        location_ready=False
        st.info("Press **Use my current location** below and allow location access in your browser. You can also choose a town or enter coordinates instead.")
        if location_result and location_result.get("error"):
            st.warning(location_result["error"])
st.caption("The selected location is saved with this field and used for local weather and soil estimates.")
with st.form("farm"):
    st.markdown("#### 2. Add crop and field details")
    name=st.text_input("Give this field a name",value="My field",help="For example: North field or Demo farm.")
    crop=st.selectbox("What are you growing?",list(CROPS))
    soil_options=["Not sure — estimate from location",*SOILS]
    soil=st.selectbox("What kind of soil is it?",soil_options,help="Choose a soil type, or let the app estimate it from the selected location.")
    if soil!="Not sure — estimate from location": st.caption(SOILS[soil][1])
    area=st.number_input("Field size (acres)",min_value=.01,value=1.0,step=.1)
    method=st.selectbox("How do you water the field?",list(EFFICIENCY))
    sowing=st.date_input("When was this crop planted?",value=date.today())
    harvest=st.date_input("Expected harvest date (optional)",value=None)
    submitted=st.form_submit_button("Save field and continue",type="primary",width="stretch",disabled=not location_ready or selected is None)
if submitted:
    try:
        if soil=="Not sure — estimate from location":
            with st.spinner("Estimating topsoil texture from the location…"):
                mapped=lookup_soil(round(float(selected["latitude"]),5),round(float(selected["longitude"]),5))
            if not mapped:
                st.error("The soil map could not return a result for this location. Choose a soil type above and save again.")
                st.stop()
            saved_soil=mapped["soil"]
        else:
            saved_soil=soil
            mapped=None
        fid=save_farm({"name":name.strip() or "My field","place":selected["name"],"latitude":selected["latitude"],"longitude":selected["longitude"],"crop":crop,"soil":saved_soil,"irrigation_method":method,"area_acres":area,"sowing_date":sowing.isoformat(),"harvest_date":harvest.isoformat() if harvest else None}); st.session_state["farm_id"]=fid
        if mapped: st.success(f"Soil map estimate: {saved_soil} ({mapped['source']}).")
        st.success(f"Field saved at {selected['name']} ({selected['latitude']:.4f}, {selected['longitude']:.4f}).")
        st.page_link("pages/2_Dashboard.py",label="Go to today's advice",icon="✅")
    except Exception: st.error("Could not save this field. Check the dates and details, then try again.")
farms=list_farms()
if farms:
    st.markdown("### Saved fields")
else:
    st.info("No fields saved yet. Fill in the details above, then choose ‘Save field and continue.’")
for farm in farms:
    col1,col2,col3=st.columns([4,1,1])
    col1.write(f"**{farm['name']}** · {farm['place']} · {farm['crop']} · {farm['area_acres']} acres")
    if col2.button("Select",key=f"use{farm['id']}"):
        st.session_state["farm_id"]=farm["id"]
        st.success(f"Selected {farm['name']}.")
    if col3.button("Delete",key=f"delete{farm['id']}"):
        delete_farm(farm['id'])
        st.rerun()
