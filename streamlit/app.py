"""
PulseGrid — electricity market intelligence.

Entry point: top header bar (brand, nav, reload) shared by both pages,
followed by page routing. No sidebar is used — see the note below.

Run locally with:  streamlit run streamlit/app.py

Navigation is built manually with st.page_link inside the header row,
with st.navigation(pages, position="hidden") suppressing Streamlit's own
sidebar nav widget. The sidebar itself is hidden via CSS (lib/theme.py)
since this layout puts brand + nav + actions in a top bar instead, the
way most dashboard apps do rather than a collapsible side panel.
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import theme as T  # noqa: E402

st.set_page_config(
    page_title="PulseGrid — Electricity Market Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

T.inject_css()

from views import agent, dashboard  # noqa: E402

pages = [
    st.Page(dashboard.render, title="Dashboard", icon="📊",
            url_path="dashboard", default=True),
    st.Page(agent.render,     title="AI Chat",   icon="🤖",
            url_path="analyst"),
]

nav = st.navigation(pages, position="hidden")

# ─────────────────────────────────────────────────────────────────────────────
# Top header — large brand with the nav pill directly beneath it, reload
# action right-aligned on the same row. Full-bleed bottom rule (CSS).
# ─────────────────────────────────────────────────────────────────────────────
with st.container(key="pg_topbar"):
    left, right = st.columns([5, 1.2], gap="medium", vertical_alignment="bottom")
    with left:
        T.sidebar_brand()
        with st.container(key="pg_segctl"):
            for pg in pages:
                st.page_link(pg, label=pg.title, icon=pg.icon)
    with right:
        with st.container(key="pg_reload"):
            if st.button("Reload snapshot", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

nav.run()
