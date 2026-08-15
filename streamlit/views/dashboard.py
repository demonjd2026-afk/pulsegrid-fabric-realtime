"""Market dashboard — the operator view."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib import data as D
from lib import theme as T


# ─────────────────────────────────────────────────────────────────────────────
# Charts
# ─────────────────────────────────────────────────────────────────────────────
def _price_curve(prices: pd.DataFrame, picked: list[str]) -> None:
    df = D.hourly_prices(prices)
    if df.empty:
        T.empty("No price curve yet",
                "The day-ahead poller writes prices once daily at 13:00 CET.")
        return
    if picked:
        df = df[df["region"].isin(picked)]
    if df.empty:
        T.empty("No zones selected", "Choose at least one bidding zone above.")
        return

    fig = px.line(df, x="period_start", y="avg_price", color="region")
    for tr in fig.data:
        tr.hovertemplate = (f"{D.zone_label(tr.name)} — "
                            "%{y:,.1f} EUR/MWh<extra></extra>")
    fig.update_traces(line=dict(width=2.1))
    st.plotly_chart(T.style_fig(fig, 372, "EUR / MWh"), use_container_width=True, theme=None)


def _spread(zones: pd.DataFrame) -> None:
    """Min–max band per zone with the average marked — intraday volatility."""
    if zones.empty:
        T.empty("No zone comparison yet", "Needs one completed price poll.")
        return
    z = zones.head(16).iloc[::-1]
    fig = go.Figure()
    for _, r in z.iterrows():
        fig.add_trace(go.Scatter(
            x=[r["min_price"], r["max_price"]], y=[r["region"], r["region"]],
            mode="lines", line=dict(color=T.LINE, width=7),
            hoverinfo="skip", showlegend=False,
        ))
    fig.add_trace(go.Scatter(
        x=z["avg_price"], y=z["region"], mode="markers",
        customdata=[D.zone_name(r) for r in z["region"]],
        marker=dict(size=10, color=[T.price_colour(p) for p in z["percentile"]],
                    line=dict(width=0)),
        hovertemplate="%{y} · %{customdata} — %{x:,.1f} EUR/MWh<extra></extra>",
        showlegend=False,
    ))
    st.plotly_chart(T.style_fig(fig, 372, ""), use_container_width=True, theme=None)


def _generation(gen: pd.DataFrame) -> None:
    if gen.empty:
        T.empty("No generation reported",
                "Zones publish output every 15 minutes. None are reporting "
                "for the current interval.")
        return
    df = gen.head(18)
    fig = go.Figure()
    for name, col, colour in [("Renewable", "renewable_pct", T.TEAL),
                              ("Nuclear",   "nuclear_pct",   T.BLUE),
                              ("Fossil",    "fossil_pct",    T.CORAL)]:
        if col in df.columns:
            fig.add_bar(x=df["region"], y=df[col], name=name,
                        marker_color=colour, marker_line_width=0,
                        hovertemplate=f"%{{x}} · {name} %{{y:.1f}}%<extra></extra>")
    fig.update_layout(barmode="stack", bargap=0.36)
    st.plotly_chart(T.style_fig(fig, 330, "% of output"), use_container_width=True, theme=None)
    st.caption(f"{len(gen)} zones reporting output. Zones publishing nothing for "
               "this interval are excluded rather than drawn as empty bars.")


def _drivers(shap: pd.DataFrame, region: str) -> None:
    imp = D.shap_importance(shap, region)
    if imp.empty:
        T.empty("No model explanations yet",
                "SHAP values are written when the ML pipeline runs, daily at 02:00 CET.")
        return
    df = imp.head(9).iloc[::-1]
    fig = go.Figure(go.Bar(
        x=df["impact"], y=df["feature_name"], orientation="h",
        marker=dict(color=T.SKY, line=dict(width=0)),
        hovertemplate="%{y} · %{x:.3f}<extra></extra>",
    ))
    st.plotly_chart(T.style_fig(fig, 330, ""), use_container_width=True, theme=None)


# ─────────────────────────────────────────────────────────────────────────────
# Page
# ─────────────────────────────────────────────────────────────────────────────
def render() -> None:
    frames = D.load_all()
    prices, preds = frames["gold_price_aggregates"], frames["gold_price_predictions"]
    gen, shap = frames["gold_generation_summary"], frames["gold_shap_values"]

    stamp, _ = D.freshness(frames)
    zones = D.latest_zone_prices(prices)
    lpred = D.latest_predictions(preds)
    agen = D.active_generation(gen)

    T.hero(
        badge="Live",
        eyebrow="Day-ahead market · 27 bidding zones",
        title="Electricity Market",
        accent="Dashboard",
        subtitle="Day-ahead prices, generation mix and cross-border flows across "
                 "European bidding zones and US balancing authorities, scored for "
                 "price-spike risk by a gradient-boosted model.",
    )

    # ── KPIs ─────────────────────────────────────────────────────────────
    n_zones = zones["region"].nunique() if not zones.empty else 0
    avg = f"{zones['avg_price'].mean():,.0f}" if not zones.empty else "—"
    peak = f"{zones['avg_price'].max():,.0f}" if not zones.empty else "—"
    spikes = int(lpred["predicted_spike"].sum()) if not lpred.empty and "predicted_spike" in lpred else 0
    scored = len(lpred) if not lpred.empty else 0
    ren = f"{agen['renewable_pct'].mean():.0f}" if not agen.empty else "—"
    shap_n = f"{len(shap):,}" if not shap.empty else "0"

    T.kpis(
        [
            {"value": n_zones, "label": "Bidding zones", "foot": "ENTSO-E + EIA",
             "accent": T.SKY},
            {"value": avg, "unit": "€", "label": "Mean price", "foot": "EUR/MWh, latest hour",
             "accent": T.AMBER},
            {"value": peak, "unit": "€", "label": "Peak zone", "foot": "highest clearing price",
             "accent": T.CORAL},
            {"value": spikes, "label": "Spike alerts", "foot": f"of {scored} zones scored",
             "accent": T.CORAL if spikes else T.TEAL},
            {"value": ren, "unit": "%", "label": "Renewable share",
             "foot": f"{len(agen)} zones generating", "accent": T.TEAL},
            {"value": shap_n, "label": "SHAP records", "foot": "model explanations",
             "accent": T.VIOLET},
        ],
        synced=stamp,
    )

    # ── hero panel: zone board ───────────────────────────────────────────
    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
    with st.container(border=True, key=f"pg_panel_1"):
        T.panel_header("Zone price board", "ranked high → low · latest hour")
        if zones.empty:
            T.empty("No prices loaded",
                    "Run the Gold pipeline, then Cell 11 in 03_gold_features "
                    "to publish a fresh snapshot to this repo.")
        else:
            T.zone_board([
                (r, D.zone_name(r), p, q)
                for r, p, q in zip(zones["region"], zones["avg_price"], zones["percentile"])
            ])
            with st.expander("Zone code reference"):
                st.markdown(
                    '<div class="pg-zoneref">'
                    + "".join(
                        f"<div><b>{c}</b>{D.zone_name(c)}</div>"
                        for c in sorted(zones["region"].unique())
                    )
                    + "</div>",
                    unsafe_allow_html=True,
                )

    all_zones = sorted(zones["region"].unique()) if not zones.empty else []

    # ── price movement + watchlist ───────────────────────────────────────
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    left, right = st.columns([1.62, 1], gap="medium")

    with left:
        with st.container(border=True, key=f"pg_panel_2"):
            T.panel_header("Price movement", "hourly averages")
            picked = st.multiselect(
                "Bidding zones",
                all_zones,
                default=list(zones.head(5)["region"]) if not zones.empty else [],
                format_func=D.zone_label,
                label_visibility="collapsed",
                placeholder="Filter bidding zones",
            )
            _price_curve(prices, picked)

    with right:
        with st.container(border=True, key=f"pg_panel_3"):
            T.panel_header("Spike watchlist", "xgboost · 2h horizon")
            if lpred.empty:
                T.empty("No predictions scored",
                        "The model runs daily at 02:00 CET and writes back to Gold.")
            else:
                T.watchlist([
                    (r["region"], D.zone_name(r["region"]),
                     float(r["spike_probability"]),
                     int(r.get("predicted_spike", 0)))
                    for _, r in lpred.head(9).iterrows()
                ])
                ok = lpred.get("prediction_correct")
                if ok is not None and ok.notna().any():
                    st.caption(f"Latest run scored {int(ok.sum())} of {len(lpred)} "
                               "zones correctly against realised prices.")

    # ── spread + generation ──────────────────────────────────────────────
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    a, b = st.columns(2, gap="medium")

    with a:
        with st.container(border=True, key=f"pg_panel_4"):
            T.panel_header("Zone spread", "min — max band, average marked")
            _spread(zones)

    with b:
        with st.container(border=True, key=f"pg_panel_5"):
            T.panel_header("Generation mix", "updated every 15 min")
            _generation(agen)

    # ── model drivers ────────────────────────────────────────────────────
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    with st.container(border=True, key=f"pg_panel_6"):
        T.panel_header("What drives the prediction", "mean absolute shap")
        pick = st.selectbox("Zone", ["All zones"] + all_zones,
                            format_func=lambda z: z if z == "All zones" else D.zone_label(z),
                            label_visibility="collapsed")
        _drivers(shap, pick)
        st.caption("Higher bars move the spike probability further from its baseline. "
                   "Open the analyst to ask why a specific zone was flagged.")
