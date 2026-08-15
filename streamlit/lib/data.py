"""
Data access layer.

Gold tables are exported from the Fabric lakehouse as JSON and committed to
this repo, so the app has no runtime dependency on a Fabric bearer token
(those expire after roughly an hour and would break a deployed app).

Refresh path: notebook `03_gold_features` Cell 11 → GitHub API → this repo.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

# Every Gold table the app reads, and the timestamp column it is indexed by.
TABLES: dict[str, str] = {
    "gold_price_aggregates":   "period_start",
    "gold_price_predictions":  "event_time",
    "gold_shap_values":        "event_time",
    "gold_generation_summary": "event_time",
}

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _candidate_paths(table: str) -> list[str]:
    return [
        os.path.join(_HERE, "data", f"{table}.json"),
        os.path.join(os.getcwd(), "streamlit", "data", f"{table}.json"),
        os.path.join(os.getcwd(), "data", f"{table}.json"),
        f"streamlit/data/{table}.json",
    ]


@st.cache_data(ttl=600, show_spinner=False)
def load_table(table: str) -> pd.DataFrame:
    """
    Read one Gold table. Returns an empty frame if the file is missing or
    malformed — callers render an empty state rather than raising.
    """
    for path in _candidate_paths(table):
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                records = json.load(fh)
            df = pd.DataFrame(records)
        except (json.JSONDecodeError, ValueError):
            # A truncated export produces invalid JSON. Skip it rather than
            # crash the page; the freshness banner will show the stale date.
            continue

        ts_col = TABLES.get(table)
        if ts_col and ts_col in df.columns:
            df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
            df = df.dropna(subset=[ts_col]).sort_values(ts_col)
        return df.reset_index(drop=True)

    return pd.DataFrame()


@st.cache_data(ttl=600, show_spinner=False)
def load_all() -> dict[str, pd.DataFrame]:
    return {name: load_table(name) for name in TABLES}


# ─────────────────────────────────────────────────────────────────────────────
# Derived views
# ─────────────────────────────────────────────────────────────────────────────
def hourly_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Hourly granularity rows only, with a usable average price."""
    if prices.empty or "granularity" not in prices.columns:
        return pd.DataFrame()
    df = prices[prices["granularity"] == "hourly"].copy()
    return df[df["avg_price"].notna()]


def latest_zone_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """
    One row per bidding zone at its most recent hour, with a price percentile
    across zones. Drives the zone strip and the price ranking.
    """
    df = hourly_prices(prices)
    if df.empty:
        return pd.DataFrame()
    latest = (
        df.sort_values("period_start")
          .groupby("region", as_index=False)
          .last()[["region", "period_start", "avg_price", "min_price", "max_price"]]
    )
    latest["percentile"] = latest["avg_price"].rank(pct=True)
    return latest.sort_values("avg_price", ascending=False).reset_index(drop=True)


def latest_predictions(preds: pd.DataFrame) -> pd.DataFrame:
    """Most recent prediction per zone, highest spike probability first."""
    if preds.empty or "spike_probability" not in preds.columns:
        return pd.DataFrame()
    latest = (
        preds.sort_values("event_time")
             .groupby("region", as_index=False)
             .last()
    )
    return latest.sort_values("spike_probability", ascending=False).reset_index(drop=True)


def active_generation(gen: pd.DataFrame) -> pd.DataFrame:
    """
    Latest generation mix per zone, excluding zones reporting zero output.

    ENTSO-E publishes a row for every zone on every interval, but many TSOs
    report nothing for the current window — those arrive as 0 MW across all
    fuels and would otherwise render as a wall of empty bars.
    """
    if gen.empty or "total_generation_mw" not in gen.columns:
        return pd.DataFrame()
    latest = (
        gen.sort_values("event_time")
           .groupby("region", as_index=False)
           .last()
    )
    return (
        latest[latest["total_generation_mw"] > 0]
        .sort_values("renewable_pct", ascending=False)
        .reset_index(drop=True)
    )


def shap_importance(shap: pd.DataFrame, region: str | None = None) -> pd.DataFrame:
    """Mean |SHAP| per feature — how much each driver moves the prediction."""
    if shap.empty or "shap_value" not in shap.columns:
        return pd.DataFrame()
    df = shap if region in (None, "All zones") else shap[shap["region"] == region]
    if df.empty:
        return pd.DataFrame()
    out = (
        df.assign(impact=df["shap_value"].abs())
          .groupby("feature_name", as_index=False)["impact"]
          .mean()
          .sort_values("impact", ascending=False)
    )
    return out[out["impact"] > 0].reset_index(drop=True)


def top_drivers(shap: pd.DataFrame, region: str, n: int = 5) -> pd.DataFrame:
    """Signed SHAP contributions for a zone's most recent scored timestamp."""
    if shap.empty:
        return pd.DataFrame()
    df = shap[shap["region"] == region]
    if df.empty:
        return pd.DataFrame()
    df = df[df["event_time"] == df["event_time"].max()].copy()
    df["magnitude"] = df["shap_value"].abs()
    return df.sort_values("magnitude", ascending=False).head(n).reset_index(drop=True)


def freshness(frames: dict[str, pd.DataFrame]) -> tuple[str, float | None]:
    """Newest timestamp across all tables, as (display string, age in hours)."""
    stamps = []
    for name, df in frames.items():
        col = TABLES.get(name)
        if not df.empty and col in df.columns:
            stamps.append(df[col].max())
    if not stamps:
        return "no data", None
    newest = max(stamps)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # Day-ahead prices carry future delivery timestamps, so the newest record
    # can legitimately sit ahead of now. Clamp to zero rather than report a
    # negative age.
    age = max(0.0, (now - newest.to_pydatetime()).total_seconds() / 3600)
    return newest.strftime("%d %b %Y · %H:%M UTC"), age


def build_context(frames: dict[str, pd.DataFrame], max_rows: int = 40) -> str:
    """
    Compact market summary passed to Claude as grounding context.

    Sends aggregates rather than raw rows — the model needs the current state
    of the market, not 7,700 SHAP records.
    """
    prices = latest_zone_prices(frames.get("gold_price_aggregates", pd.DataFrame()))
    preds  = latest_predictions(frames.get("gold_price_predictions", pd.DataFrame()))
    gen    = active_generation(frames.get("gold_generation_summary", pd.DataFrame()))
    imp    = shap_importance(frames.get("gold_shap_values", pd.DataFrame()))

    parts: list[str] = []

    if not prices.empty:
        parts.append(
            "CURRENT DAY-AHEAD PRICES BY BIDDING ZONE (EUR/MWh, latest hour):\n"
            + prices.head(max_rows)[["region", "period_start", "avg_price", "min_price", "max_price"]]
                    .to_string(index=False)
        )
    if not preds.empty:
        cols = [c for c in ["region", "event_time", "spike_probability", "predicted_spike", "actual_spike"]
                if c in preds.columns]
        parts.append(
            "SPIKE PREDICTIONS (XGBoost, probability price exceeds the zone's 90th percentile):\n"
            + preds.head(max_rows)[cols].to_string(index=False)
        )
    if not gen.empty:
        cols = [c for c in ["region", "renewable_pct", "nuclear_pct", "fossil_pct", "total_generation_mw"]
                if c in gen.columns]
        parts.append(
            "GENERATION MIX BY ZONE (%, zones currently reporting output):\n"
            + gen.head(max_rows)[cols].round(1).to_string(index=False)
        )
    if not imp.empty:
        parts.append(
            "MODEL FEATURE IMPORTANCE (mean absolute SHAP across all scored predictions):\n"
            + imp.head(12).round(4).to_string(index=False)
        )

    return "\n\n".join(parts) if parts else "No market data is currently loaded."


# ─────────────────────────────────────────────────────────────────────────────
# Zone code → human-readable name
# ─────────────────────────────────────────────────────────────────────────────
ZONE_NAMES: dict[str, str] = {
    "AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "CH": "Switzerland",
    "CZ": "Czechia", "DE-LU": "Germany–Lux.", "DK-1": "Denmark West",
    "DK-2": "Denmark East", "EE": "Estonia", "ES": "Spain", "FI": "Finland",
    "FR": "France", "GR": "Greece", "HR": "Croatia", "HU": "Hungary",
    "IT-NO": "Italy North", "LT": "Lithuania", "LV": "Latvia",
    "NL": "Netherlands", "NO-2": "Norway South", "PL": "Poland",
    "PT": "Portugal", "RO": "Romania", "RS": "Serbia", "SE-3": "Sweden Central",
    "SI": "Slovenia", "SK": "Slovakia",
    "US-BPAT": "Bonneville (US)", "US-CISO": "California ISO",
    "US-ERCOT": "Texas ERCOT", "US-ISNE": "New England ISO",
    "US-MISO": "Midcontinent ISO", "US-NYIS": "New York ISO",
    "US-PJM": "PJM Mid-Atlantic", "US-SWPP": "Southwest Power Pool",
    "US-NEVP": "Nevada Power", "US-PACE": "PacifiCorp East",
    "US-PACW": "PacifiCorp West", "US-SRP": "Salt River (AZ)",
}


def zone_name(code: str) -> str:
    """Human-readable name for a bidding-zone code; the code itself if unknown."""
    return ZONE_NAMES.get(code, code)


def zone_label(code: str) -> str:
    """'PL · Poland' — used in pickers and tooltips."""
    name = ZONE_NAMES.get(code)
    return f"{code} · {name}" if name else code
