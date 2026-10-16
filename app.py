import streamlit as st
from core.config import OFFLINE
from core.db import init_db
from core.ui import apply_css

st.set_page_config(
    page_title="JalRakshak AI",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_css()
init_db()

if OFFLINE:
    st.sidebar.warning("Sample weather mode")

navigation = st.navigation(
    {
        "FIELD": [
            st.Page("pages/0_Home.py", title="Home", icon="🏡", default=True),
            st.Page("pages/1_Farm_Setup.py", title="Set up field", icon="🌾"),
            st.Page("pages/2_Dashboard.py", title="Today's field outlook", icon="✅"),
            st.Page("pages/7_Hardware_Setup.py", title="Hardware setup", icon="🔌"),
        ],
        "FIELD NOTES": [
            st.Page("pages/6_Water_Usage.py", title="Log watering or soil condition", icon="💧"),
        ],
    },
    position="sidebar",
)
navigation.run()
