"""How the platform is built — the page a reviewer opens second."""

import streamlit as st

from lib import data as D
from lib import theme as T

FLOW = [
    ("Sources", T.MUTED,  "ENTSO-E · EIA · Visual Crossing", "4 public APIs"),
    ("Bronze",  T.AMBER,  "KQL Database, append-only, 90-day retention", "5 tables"),
    ("Silver",  T.CYAN,   "PySpark cleansing, dedup, schema enforcement", "5 Delta tables"),
    ("Gold",    T.MINT,   "Window features, aggregates, predictions", "6 Delta tables"),
    ("Serving", T.VIOLET, "Power BI Direct Lake · this app", "2 surfaces"),
]

CADENCE = [
    ("01a_daily_price_poller",  "Daily 13:00 CET",  "ENTSO-E day-ahead prices, 27 zones"),
    ("01b_realtime_poller",     "Every 15 min",     "Load, generation mix, cross-border flows"),
    ("01c_weather_eia_poller",  "Every 30 min",     "Weather for 20 cities, 13 US balancing authorities"),
    ("02_silver_cleansing",     "Every 30 min",     "All 5 Bronze tables, processed in parallel"),
    ("03_gold_features",        "Hourly",           "Lag and rolling features, aggregates"),
    ("04_ml_spike_predictor",   "Daily 02:00 CET",  "XGBoost retrain, SHAP, write-back to Gold"),
]

DECISIONS = [
    ("Event-aligned polling",
     "Day-ahead prices publish once daily; load publishes every 15 minutes. Polling "
     "everything on one fast schedule would spend the rate-limit budget re-fetching "
     "identical values, so each source runs on its own cadence.",
     "ENTSO-E usage sits near 2 req/min against a 400 req/min ceiling."),
    ("Parallel Silver processing",
     "The five Bronze tables are independent, so the cleansing notebook submits them "
     "concurrently through a ThreadPoolExecutor. Wall time tracks the slowest table "
     "rather than the sum of all five.",
     "Deduplication uses row_number() over the natural key — deterministic, fully distributed."),
    ("Predicate pushdown into KQL",
     "The Silver reader filters on ingestion_time inside the KQL query, so the Kusto "
     "engine trims the result before anything crosses into Spark.",
     "Keeps memory pressure low on a Trial capacity."),
    ("Native functions, no UDFs",
     "Every transformation uses Spark SQL functions. Python UDFs are opaque to Catalyst "
     "and pay a serialisation cost per row.",
     "Window functions handle lag and rolling features without collecting to the driver."),
    ("Libraries in the Fabric Environment",
     "%pip magic is disabled in pipeline-triggered notebook runs. Dependencies moved to "
     "pulsegrid_env public libraries, pinned to versions that resolve on the Spark "
     "runtime's Python 3.10.",
     "xgboost 3.3+ requires Python 3.12 and will not install there."),
    ("JSON snapshot instead of a live API call",
     "Fabric bearer tokens expire after about an hour, which would break a deployed app "
     "within one session. The Gold tables are exported to JSON and committed to the repo, "
     "so this page has no runtime auth dependency.",
     "Refreshed by Cell 11 in 03_gold_features, pushed through the GitHub API."),
]


def render() -> None:
    frames = D.load_all()
    stamp, _ = D.freshness(frames)

    T.section("Pipeline", "MEDALLION ARCHITECTURE ON MICROSOFT FABRIC")
    st.markdown(
        '<div class="pg-flow">'
        + "".join(
            f'<div class="pg-flow-node" style="--n:{c}">'
            f'<h4>{name}</h4><p>{desc}</p><code>{tag}</code></div>'
            for name, c, desc, tag in FLOW
        )
        + "</div>",
        unsafe_allow_html=True,
    )

    T.section("Schedule", "SIX FABRIC DATA PIPELINES")
    st.markdown(
        "".join(
            f'<div class="pg-spec"><dt>{cad}</dt>'
            f'<dd>{name}<br><em>{what}</em></dd></div>'
            for name, cad, what in CADENCE
        ),
        unsafe_allow_html=True,
    )

    T.section("Engineering decisions", "WHAT WAS CHOSEN, AND WHY")
    for title, body, note in DECISIONS:
        st.markdown(
            f'<div class="pg-panel" style="margin-bottom:10px">'
            f'<h4 style="font-family:{T.FONT_DISPLAY};font-size:1.02rem;'
            f'text-transform:uppercase;letter-spacing:.04em;margin:0 0 .5rem 0;'
            f'color:{T.TEXT}">{title}</h4>'
            f'<p style="margin:0 0 .55rem 0;font-size:.88rem;line-height:1.6;'
            f'color:{T.TEXT}">{body}</p>'
            f'<p style="margin:0;font-family:{T.FONT_MONO};font-size:.70rem;'
            f'color:{T.MUTED};line-height:1.5">{note}</p></div>',
            unsafe_allow_html=True,
        )

    T.section("Stack", "")
    stack = [
        ("Platform",     "Microsoft Fabric Trial"),
        ("Bronze",       "KQL Database (Eventhouse), append-only"),
        ("Silver / Gold","Lakehouse Delta tables, OPTIMIZE + ZORDER"),
        ("Transform",    "PySpark, AQE, broadcast joins, window functions"),
        ("Model",        "XGBoost binary classifier, MLflow tracking, SHAP"),
        ("BI",           "Power BI semantic model, Direct Lake"),
        ("This app",     "Streamlit, Plotly, Claude"),
        ("Snapshot",     stamp),
    ]
    st.markdown(
        "".join(f'<div class="pg-spec"><dt>{k}</dt><dd>{v}</dd></div>' for k, v in stack),
        unsafe_allow_html=True,
    )
