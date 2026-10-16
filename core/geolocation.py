"""Small browser geolocation component; only returns coordinates after a click."""
from pathlib import Path
import streamlit.components.v1 as components

_COMPONENT = components.declare_component(
    "jalrakshak_browser_location",
    path=str(Path(__file__).resolve().parents[1] / "components" / "geolocation"),
)

def browser_location(key="jalrakshak_location"):
    return _COMPONENT(key=key, default=None)
