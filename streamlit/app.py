"""
PulseGrid — real-time electricity market intelligence.

Entry point. Registers the three pages and renders the persistent sidebar.
Run locally with:  streamlit run streamlit/app.py
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import data as D          # noqa: E402
from lib import theme as T         # noqa: E402

st.set_page_config(
    page_title="PulseGrid — Electricity Market Intelligence",
    page_icon="◤",
    layout="wide",
    initial_sidebar_state="expanded",
)

T.inject_css()

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    T.brand()

    frames = D.load_all()
    stamp, age = D.freshness(frames)
    loaded = sum(1 for f in frames.values() if not f.empty)

    if age is None:
        dot, note = T.MUTED, "No snapshot found"
    elif age <= 24:
        dot, note = T.MINT, "Snapshot current"
    else:
        dot, note = T.AMBER, f"{age:,.0f}h since last export"

    st.markdown(
        f'<div style="font-family:{T.FONT_MONO};font-size:.66rem;'
        f'letter-spacing:.07em;color:{T.MUTED};line-height:1.9">'
        f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;'
        f'background:{dot};margin-right:.5rem"></span>{note.upper()}<br>'
        f'<span style="color:{T.TEXT}">{stamp}</span><br>'
        f'{loaded}/4 GOLD TABLES LOADED</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    if st.button("Reload snapshot", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# Navigation
# ─────────────────────────────────────────────────────────────────────────────
from views import about, agent, dashboard      # noqa: E402

# url_path must be set explicitly: all three view functions are named `render`,
# so Streamlit would otherwise infer the same pathname for each and raise.
pages = [
    st.Page(dashboard.render, title="Dashboard",    icon=":material/bolt:",
            url_path="dashboard", default=True),
    st.Page(agent.render,     title="Ask analyst",  icon=":material/forum:",
            url_path="analyst"),
    st.Page(about.render,     title="Architecture", icon=":material/schema:",
            url_path="architecture"),
]

st.navigation(pages).run()

st.markdown(
    f'<div style="margin-top:3.5rem;padding-top:1.2rem;border-top:1px solid {T.LINE};'
    f'font-family:{T.FONT_MONO};font-size:.62rem;letter-spacing:.07em;color:{T.MUTED}">'
    f'PULSEGRID · MICROSOFT FABRIC MEDALLION LAKEHOUSE · '
    f'ENTSO-E · EIA · VISUAL CROSSING · XGBOOST + SHAP</div>',
    unsafe_allow_html=True,
)
