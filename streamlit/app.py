"""
PulseGrid — electricity market intelligence.

Entry point: renders the sidebar and registers the two pages.
Run locally with:  streamlit run streamlit/app.py

Sidebar ordering note: st.navigation() renders its page-picker widget into
the sidebar at the moment it is called, not at the position implied by
nav.run(). To get the logo above the nav links, the brand block must be
written to the sidebar BEFORE st.navigation() is invoked; everything else
(pipeline metadata, footer) is written after, in a second `with st.sidebar`
block, so it lands below the nav links.
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

from views import agent, dashboard  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — top: brand
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    T.sidebar_brand()

# ─────────────────────────────────────────────────────────────────────────────
# Navigation — registers here so the picker sits directly under the brand
# ─────────────────────────────────────────────────────────────────────────────
nav = st.navigation([
    st.Page(dashboard.render, title="Dashboard",  icon="📊",
            url_path="dashboard", default=True),
    st.Page(agent.render,     title="AI Analyst", icon="🤖",
            url_path="analyst"),
])

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — below nav: pipeline metadata, footer
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
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
