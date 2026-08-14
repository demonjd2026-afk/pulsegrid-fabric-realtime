"""How the platform is built — the page a reviewer opens second."""

import streamlit as st

from lib import data as D
from lib import theme as T

FLOW = [
    ("Sources", T.MUTED,  "ENTSO-E transparency, EIA open data, Visual Crossing weather", "4 public APIs"),
    ("Bronze",  T.AMBER,  "KQL Database, append-only, schema-on-read, 90-day retention", "5 tables"),
    ("Silver",  T.BLUE,   "PySpark cleansing, deduplication, schema enforcement", "5 Delta tables"),
    ("Gold",    T.TEAL,   "Window features, aggregates, predictions, SHAP", "6 Delta tables"),
    ("Serving", T.VIOLET, "Power BI Direct Lake semantic model and this app", "2 surfaces"),
]

CADENCE = [
    ("Daily 13:00 CET", "01a_daily_price_poller", "ENTSO-E day-ahead prices, 27 bidding zones"),
    ("Every 15 min",    "01b_realtime_poller",    "Actual load, generation mix, cross-border flows"),
    ("Every 30 min",    "01c_weather_eia_poller", "Weather for 20 cities, 13 US balancing authorities"),
    ("Every 30 min",    "02_silver_cleansing",    "All five Bronze tables, processed in parallel"),
    ("Hourly",          "03_gold_features",       "Lag and rolling features, curated aggregates"),
    ("Daily 02:00 CET", "04_ml_spike_predictor",  "XGBoost retrain, SHAP, write-back to Gold"),
]

DECISIONS = [
    ("Poll each source on its own cadence", T.AMBER,
     "Day-ahead prices publish once a day; load publishes every fifteen minutes. "
     "Running everything on one fast schedule would spend the rate-limit budget "
     "re-fetching identical values, so each source has its own pipeline.",
     "ENTSO-E usage sits near 2 req/min against a 400 req/min ceiling."),
    ("Process Silver tables in parallel", T.BLUE,
     "The five Bronze tables are independent, so the cleansing notebook submits "
     "them concurrently through a ThreadPoolExecutor. Wall time tracks the "
     "slowest table rather than the sum of all five.",
     "Deduplication uses row_number() over the natural key — deterministic and fully distributed."),
    ("Push predicates down into KQL", T.TEAL,
     "The Silver reader filters on ingestion_time inside the KQL query itself, so "
     "the Kusto engine trims the result before anything crosses into Spark.",
     "Keeps memory pressure low on a Trial capacity."),
    ("Native functions, no UDFs", T.VIOLET,
     "Every transformation uses Spark SQL functions. Python UDFs are opaque to "
     "Catalyst and pay a serialisation cost on every row.",
     "Window functions compute lag and rolling features without collecting to the driver."),
    ("Manage libraries in the Fabric Environment", T.CORAL,
     "%pip magic is disabled in pipeline-triggered notebook runs. Dependencies "
     "moved into pulsegrid_env public libraries, pinned to versions that resolve "
     "against the Spark runtime's Python 3.10.",
     "xgboost 3.3 and above require Python 3.12 and will not install there."),
    ("Ship a JSON snapshot, not a live API call", T.AMBER,
     "Fabric bearer tokens expire after about an hour, which would break a "
     "deployed app inside a single session. The Gold tables are serialised and "
     "committed to this repo, so the app has no runtime auth dependency.",
     "Published by Cell 11 in 03_gold_features straight through the GitHub API."),
]


def render() -> None:
    frames = D.load_all()
    stamp, _ = D.freshness(frames)

    T.hero(
        badge="Reference",
        eyebrow="Medallion lakehouse on Microsoft Fabric",
        title="How PulseGrid is",
        accent="Built",
        subtitle="Six scheduled pipelines move data from four public APIs through "
                 "Bronze, Silver and Gold, train a spike classifier nightly, and "
                 "serve the result to Power BI and this app.",
        kind="build",
    )

    with st.container(border=True):
        T.panel_header("Pipeline", "bronze → silver → gold")
        st.markdown(
            '<div class="pg-flow">'
            + "".join(
                f'<div class="pg-node" style="--n:{c}"><h4>{n}</h4>'
                f"<p>{d}</p><code>{t}</code></div>"
                for n, c, d, t in FLOW
            )
            + "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        T.panel_header("Schedule", "six fabric data pipelines")
        st.markdown(
            "".join(
                f'<div class="pg-spec"><dt>{cad}</dt>'
                f"<dd>{name}<br><em>{what}</em></dd></div>"
                for cad, name, what in CADENCE
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        T.panel_header("Engineering decisions", "what was chosen, and why")
        st.markdown(
            "".join(
                f'<div class="pg-note" style="--n:{c}"><h4>{t}</h4>'
                f"<p>{b}</p><code>{n}</code></div>"
                for t, c, b, n in DECISIONS
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        T.panel_header("Stack", "")
        stack = [
            ("Platform",      "Microsoft Fabric Trial"),
            ("Bronze",        "KQL Database in an Eventhouse, append-only"),
            ("Silver / Gold", "Lakehouse Delta tables, OPTIMIZE with ZORDER"),
            ("Transform",     "PySpark — AQE, broadcast joins, window functions"),
            ("Model",         "XGBoost binary classifier, MLflow tracking, SHAP explanations"),
            ("BI",            "Power BI semantic model over Direct Lake"),
            ("This app",      "Streamlit, Plotly, Claude"),
            ("Snapshot",      stamp),
        ]
        st.markdown(
            "".join(f'<div class="pg-spec"><dt>{k}</dt><dd>{v}</dd></div>'
                    for k, v in stack),
            unsafe_allow_html=True,
        )
