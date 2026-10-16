import streamlit as st
from pathlib import Path
from .config import ROOT
from .config import DISCLAIMER

def apply_css():
    # st.markdown sanitizes <style> blocks on current Streamlit releases. st.html
    # inserts CSS directly into the app document, so global theme selectors work.
    st.html(ROOT/"assets"/"styles.css")

def banner(message,kind="info"):
    getattr(st,kind if kind in ("info","warning","success","error") else "info")(message)
def disclaimer(): st.caption(DISCLAIMER)
def page_header(title,subtitle=None):
    st.title(title)
    if subtitle: st.write(subtitle)
def metric_card(label,value,help=None): st.metric(label,value,help=help)
