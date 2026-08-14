"""Market dashboard — the operator view."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib import data as D
from lib import theme as T


def _kpi_block(frames: dict[str, pd.DataFrame]) -> None:
    zones  = D.latest_zone_prices(frames["gold_price_aggregates"])
    preds  = D.latest_predictions(frames["gold_price_predictions"])
    gen    = D.active_generation(frames["gold_generation_summary"])

    avg_price = f"{zones['avg_price'].mean():,.0f}" if not zones.empty else "—"
    spread = (
        f"{zones['avg_price'].max() - zones['avg_price'].min():,.0f} spread across zones"
        if not zones.empty else "awaiting price data"
    )

    if not preds.empty and "predicted_spike" in preds:
        n_spike = int(preds["predicted_spike"].sum())
        spike_foot = f"of {len(preds)} zones scored"
    else:
        n_spike, spike_foot = "—", "awaiting model run"

    zone_count = f"{zones['region'].nunique()}" if not zones.empty else "—"

    if not gen.empty:
        renewable = f"{gen['renewable_pct'].mean():.0f}"
        ren_foot = f"across {len(gen)} reporting zones"
    else:
        renewable, ren_foot = "—", "awaiting generation data"

    T.kpis([
        {"label": "Mean zone price", "value": avg_price, "unit": "EUR/MWh",
         "foot": spread, "accent": T.AMBER},
        {"label": "Spike alerts", "value": n_spike, "unit": "",
         "foot": spike_foot, "accent": T.FLARE},
        {"label": "Bidding zones", "value": zone_count, "unit": "",
         "foot": "ENTSO-E + EIA coverage", "accent": T.CYAN},
        {"label": "Renewable share", "value": renewable, "unit": "%",
         "foot": ren_foot, "accent": T.MINT},
    ])


def _price_curve(prices: pd.DataFrame, picked: list[str]) -> None:
    df = D.hourly_prices(prices)
    if df.empty:
        T.empty("No price curve yet",
                "The day-ahead poller writes prices once daily at 13:00 CET.")
        return
    if picked:
        df = df[df["region"].isin(picked)]
    if df.empty:
        T.empty("No zones selected", "Pick at least one bidding zone above.")
        return

    fig = px.line(df, x="period_start", y="avg_price", color="region", markers=False)
    fig.update_traces(line=dict(width=1.9), hovertemplate="%{y:,.1f} EUR/MWh<extra>%{fullData.name}</extra>")
    st.plotly_chart(T.style_fig(fig, 380, "EUR / MWh"), use_container_width=True)


def _spread_chart(zones: pd.DataFrame) -> None:
    """Min–max band with the average marked — shows intraday volatility per zone."""
    if zones.empty:
        T.empty("No zone comparison yet", "Needs at least one completed price poll.")
        return
    z = zones.head(18).iloc[::-1]
    fig = go.Figure()
    for _, r in z.iterrows():
        fig.add_trace(go.Scatter(
            x=[r["min_price"], r["max_price"]], y=[r["region"], r["region"]],
            mode="lines", line=dict(color=T.LINE, width=6),
            hoverinfo="skip", showlegend=False,
        ))
    fig.add_trace(go.Scatter(
        x=z["avg_price"], y=z["region"], mode="markers",
        marker=dict(size=9, color=[T.price_colour(p) for p in z["percentile"]],
                    line=dict(width=0)),
        hovertemplate="%{y}: %{x:,.1f} EUR/MWh<extra></extra>", showlegend=False,
    ))
    st.plotly_chart(T.style_fig(fig, 430, ""), use_container_width=True)


def _generation(gen: pd.DataFrame) -> None:
    if gen.empty:
        T.empty("No generation reported",
                "Zones publish output every 15 minutes; none are reporting for this window yet.")
        return
    df = gen.head(20)
    fig = go.Figure()
    for name, col, colour in [
        ("Renewable", "renewable_pct", T.MINT),
        ("Nuclear",   "nuclear_pct",   T.CYAN),
        ("Fossil",    "fossil_pct",    T.FLARE),
    ]:
        if col in df.columns:
            fig.add_bar(x=df["region"], y=df[col], name=name,
                        marker_color=colour, marker_line_width=0,
                        hovertemplate="%{x} · " + name + " %{y:.1f}%<extra></extra>")
    fig.update_layout(barmode="stack", bargap=0.35)
    st.plotly_chart(T.style_fig(fig, 360, "% of output"), use_container_width=True)
    st.caption(f"{len(gen)} zones currently reporting generation. "
               "Zones with no published output for this interval are excluded.")


def _drivers(shap: pd.DataFrame, region: str) -> None:
    imp = D.shap_importance(shap, region)
    if imp.empty:
        T.empty("No model explanations yet",
                "SHAP values are written when the ML pipeline runs, daily at 02:00 CET.")
        return
    df = imp.head(10).iloc[::-1]
    fig = go.Figure(go.Bar(
        x=df["impact"], y=df["feature_name"], orientation="h",
        marker_color=T.AMBER, marker_line_width=0,
        hovertemplate="%{y}: %{x:.4f}<extra></extra>",
    ))
    st.plotly_chart(T.style_fig(fig, 340, ""), use_container_width=True)


def render() -> None:
    frames = D.load_all()
    prices = frames["gold_price_aggregates"]
    preds  = frames["gold_price_predictions"]
    gen    = frames["gold_generation_summary"]
    shap   = frames["gold_shap_values"]

    stamp, age = D.freshness(frames)
    zones = D.latest_zone_prices(prices)

    # ── zone strip ───────────────────────────────────────────────────────
    T.section("Zone price board", f"LATEST HOUR · {stamp}")
    if zones.empty:
        T.empty("No prices loaded",
                "Run the Gold pipeline, then Cell 11 in 03_gold_features to refresh this repo.")
    else:
        T.zone_strip(list(zip(zones["region"], zones["avg_price"], zones["percentile"])))

    # ── KPIs ─────────────────────────────────────────────────────────────
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    _kpi_block(frames)

    # ── filters ──────────────────────────────────────────────────────────
    all_zones = sorted(zones["region"].unique()) if not zones.empty else []
    default = list(zones.head(6)["region"]) if not zones.empty else []

    T.section("Price movement", "HOURLY AVERAGES · DAY-AHEAD MARKET")
    picked = st.multiselect(
        "Bidding zones", all_zones, default=default,
        label_visibility="collapsed",
        placeholder="Filter bidding zones",
    )
    _price_curve(prices, picked)

    # ── watchlist + spread ───────────────────────────────────────────────
    left, right = st.columns([1, 1.35], gap="large")

    with left:
        T.section("Spike watchlist", "XGBOOST · 2H HORIZON")
        lp = D.latest_predictions(preds)
        if lp.empty:
            T.empty("No predictions scored",
                    "The model runs daily at 02:00 CET and writes back to Gold.")
        else:
            T.watchlist([
                (r["region"], float(r["spike_probability"]), int(r.get("predicted_spike", 0)))
                for _, r in lp.head(12).iterrows()
            ])
            hits = lp.get("prediction_correct")
            if hits is not None and hits.notna().any():
                st.caption(f"Latest run scored {int(hits.sum())} of {len(lp)} zones correctly.")

    with right:
        T.section("Zone spread", "MIN — MAX BAND, AVERAGE MARKED")
        _spread_chart(zones)

    # ── generation + drivers ─────────────────────────────────────────────
    g_col, s_col = st.columns([1.2, 1], gap="large")

    with g_col:
        T.section("Generation mix", "UPDATED EVERY 15 MIN")
        _generation(gen)

    with s_col:
        T.section("Prediction drivers", "MEAN ABSOLUTE SHAP")
        opts = ["All zones"] + (all_zones or [])
        pick = st.selectbox("Zone", opts, label_visibility="collapsed")
        _drivers(shap, pick)

    # ── footer note ──────────────────────────────────────────────────────
    if age is not None and age > 24:
        st.markdown(
            f"<div class='pg-tagline' style='margin-top:2rem'>"
            f"SNAPSHOT IS {age:,.0f}H OLD — RERUN 03_GOLD_FEATURES CELL 11 TO REFRESH"
            f"</div>", unsafe_allow_html=True)
