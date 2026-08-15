"""
PulseGrid — electricity market intelligence.

Entry point: minimal sidebar (logo + manual nav + reload) and page routing.
Run locally with:  streamlit run streamlit/app.py

Navigation is built manually with st.page_link rather than relying on
st.navigation's built-in sidebar widget. The built-in widget always claims
the very top of the sidebar for MPA routing reasons, regardless of when
st.navigation() is called in the script — so there is no way to put a logo
above it by reordering code. Setting position="hidden" and building our own
st.page_link list right after the logo is the documented workaround.
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
    initial_sidebar_state="expanded",
)

T.inject_css()

from views import agent, dashboard  # noqa: E402

pages = [
    st.Page(dashboard.render, title="Dashboard", icon="📊",
            url_path="dashboard", default=True),
    st.Page(agent.render,     title="AI Chat",   icon="🤖",
            url_path="analyst"),
]

# position="hidden" suppresses Streamlit's own sidebar nav widget entirely;
# we render the links ourselves below so the logo can sit above them, and
# style them as one segmented pill (Claude's Home/Code pattern) instead of
# two stacked rows.
nav = st.navigation(pages, position="hidden")

with st.sidebar:
    T.sidebar_brand()

    with st.container(key="pg_segctl"):
        for pg in pages:
            st.page_link(pg, label=pg.title, icon=pg.icon)

    if st.button("Reload snapshot", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

nav.run()
