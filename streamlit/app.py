"""
PulseGrid — electricity market intelligence.

Entry point: registers the three pages and renders the persistent sidebar.
Run locally with:  streamlit run streamlit/app.py
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import data as D   # noqa: E402
from lib import theme as T  # noqa: E402

st.set_page_config(
    page_title="PulseGrid — Electricity Market Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

T.inject_css()

# ─────────────────────────────────────────────────────────────────────────────
# Navigation
# ─────────────────────────────────────────────────────────────────────────────
from views import about, agent, dashboard  # noqa: E402

# url_path is explicit: all three view functions are named `render`, so
# Streamlit would otherwise infer the same pathname for each and raise.
nav = st.navigation([
    st.Page(dashboard.render, title="Dashboard",    icon=":material/monitoring:",
            url_path="dashboard", default=True),
    st.Page(agent.render,     title="AI Analyst",   icon=":material/neurology:",
            url_path="analyst"),
    st.Page(about.render,     title="Architecture", icon=":material/account_tree:",
            url_path="architecture"),
])

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    T.sidebar_brand()

    frames = D.load_all()
    stamp, age = D.freshness(frames)
    loaded = sum(1 for f in frames.values() if not f.empty)

    if age is None:
        dot, status = T.MUTED, "No snapshot found"
    elif age <= 24:
        dot, status = T.TEAL, "Snapshot current"
    else:
        dot, status = T.AMBER, f"{age:,.0f}h since last export"

    T.sidebar_meta([
        ("Data sources", "ENTSO-E transparency<br>EIA open data<br>Visual Crossing"),
        ("Pipeline", "Microsoft Fabric<br><span>Bronze → Silver → Gold</span>"),
        ("Model", "XGBoost + SHAP<br><span>retrained daily 02:00 CET</span>"),
        ("Snapshot", f'<span style="color:{dot}">●</span> {status}<br>'
                     f"<span>{stamp}</span><br>"
                     f"<span>{loaded} of 4 Gold tables loaded</span>"),
    ])

    if st.button("Reload snapshot", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(
        f'<div class="pg-divider"></div>'
        f'<div style="font-size:.72rem;color:{T.MUTED};line-height:1.65">'
        f"Built by Jayanth Dolai<br>"
        f'<a href="https://github.com/demonjd2026-afk/pulsegrid-fabric-realtime" '
        f'style="color:{T.AMBER};text-decoration:none">Source on GitHub →</a></div>',
        unsafe_allow_html=True,
    )

nav.run()
