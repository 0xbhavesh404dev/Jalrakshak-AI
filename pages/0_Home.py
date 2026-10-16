import streamlit as st
from core.config import OFFLINE
from core.db import init_db, list_farms
from core.ui import apply_css, disclaimer

apply_css()
init_db()
farms = list_farms()

st.markdown(
    """
    <section class="hero">
      <div class="hero-kicker">JALRAKSHAK AI · SMART IRRIGATION GUIDE</div>
      <h1>Know when it may be time to water.</h1>
      <p>Set up your field once. Get a simple, explainable estimate for today and know when to check again.</p>
      <div class="hero-tagline">Predict the Need. Save Every Drop.</div>
    </section>
    """,
    unsafe_allow_html=True,
)
if OFFLINE:
    st.warning("Demo mode is on. The weather shown is sample data, not today's actual forecast.")
else:
    st.info("Weather is fetched for your saved field. If live weather and its saved copy are unavailable, the app will explain that it cannot calculate today's advice.")

st.markdown("### Start in two steps")
left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.markdown("#### 1 · Tell us about your field")
        st.write("Choose its location, crop, soil, size and watering method.")
        st.page_link("pages/1_Farm_Setup.py", label="Set up a farm", icon="🌾")
with right:
    with st.container(border=True):
        st.markdown("#### 2 · Read today's advice")
        st.write("See whether to water, wait, or check again after expected rain.")
        if farms:
            st.page_link("pages/2_Dashboard.py", label="See today's advice", icon="✅")
        else:
            st.button("Set up a farm first", disabled=True, width="stretch")

if farms:
    names = ", ".join(f["name"] for f in farms[:3])
    st.success(f"Your saved field{'s' if len(farms) != 1 else ''}: {names}{'…' if len(farms) > 3 else ''}")

with st.expander("What does the advice mean?"):
    st.markdown(
        "- **Water now / soon:** the estimate says the crop may be near its water limit.\n"
        "- **Wait:** the estimate says there is room to check again later.\n"
        "- **Rain expected — recheck:** rain may help, so check the field after it rains.\n\n"
        "This app has no physical sensors. It estimates water near the crop roots from weather, "
        "crop and soil assumptions, and your notes. It cannot see or measure the soil."
    )

st.caption("Use this as a guide. Check the soil in the field and follow local agricultural advice.")
disclaimer()
