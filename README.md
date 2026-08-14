# PulseGrid ⚡

### Real-Time Energy Market Intelligence Platform on Microsoft Fabric

> A production-grade medallion lakehouse that ingests live electricity prices from European and US energy markets, predicts price spikes using XGBoost, and serves insights through a Claude-powered AI agent with natural language analytics.

---

## Overview

PulseGrid is an end-to-end real-time data engineering project built entirely on **Microsoft Fabric Trial**. It demonstrates a complete data platform lifecycle — from raw API ingestion through to ML-powered predictions and an AI agent interface — using only Fabric-native components and free public APIs.

The platform answers one core question:

> *"Will electricity prices spike in the next 2 hours, and why?"*

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          DATA SOURCES                               │
│  ENTSO-E Transparency    EIA Open Data       Visual Crossing        │
│  27 European zones       13 US RTOs          20 cities worldwide    │
└──────────┬───────────────────┬──────────────────────┬──────────────┘
           │                   │                      │
           └───────────────────┴──────────────────────┘
                               │
              ┌────────────────▼───────────────┐
              │     3 Scheduled Notebooks       │
              │  01a — Daily price poller       │
              │  01b — 15-min realtime poller   │
              │  01c — 30-min weather/EIA poller│
              └────────────────┬───────────────┘
                               │
         ┌─────────────────────▼──────────────────────┐
         │         BRONZE — KQL Database               │
         │         pulsegrid_bronze (Eventhouse)        │
         │                                             │
         │  raw_electricity_prices  (2,556 records)    │
         │  raw_electricity_load    (120 records)      │
         │  raw_generation_mix      (1,669 records)    │
         │  raw_cross_border_flows  (90 records)       │
         │  raw_weather             (20 records)       │
         │                                             │
         │  Append-only · Schema-on-read · 90d retain  │
         └─────────────────────┬──────────────────────┘
                               │
         ┌─────────────────────▼──────────────────────┐
         │         SILVER — Lakehouse (Delta)          │
         │  PySpark cleansing + Spark optimizations    │
         │  Dedup · Nulls · Schema enforce             │
         │  Repartition · Native functions only        │
         └─────────────────────┬──────────────────────┘
                               │
         ┌─────────────────────▼──────────────────────┐
         │         GOLD — Lakehouse (Delta)            │
         │  Window functions · Aggregates              │
         │  ML feature table                           │
         │  Spike predictions (XGBoost)                │
         │  Delta OPTIMIZE + ZORDER                    │
         └──────────┬──────────────────────────────────┘
                    │
         ┌──────────┴──────────────────┐
         │                             │
         ▼                             ▼
┌─────────────────┐       ┌────────────────────────────┐
│   Power BI      │       │  Claude API + Streamlit     │
│ Semantic Model  │       │  AI Agent                   │
│  Direct Lake    │       │  Natural language → SQL     │
└─────────────────┘       └────────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Platform | Microsoft Fabric Trial |
| Real-Time Ingestion | KQL Database (Eventhouse) + Scheduled Notebooks |
| Bronze Store | KQL Database — 5 tables |
| Silver / Gold Store | Lakehouse — Delta tables |
| Transformations | PySpark (Fabric Notebooks) |
| Secret Management | Fabric Environment (Spark properties) |
| ML Framework | XGBoost + MLflow + SHAP |
| Orchestration | Fabric Data Pipeline |
| BI Layer | Power BI Semantic Model (Direct Lake) |
| AI Agent | Claude API + Streamlit |

---

## Data Sources

| Source | Data | Zones / Regions | Poll Frequency |
|---|---|---|---|
| [ENTSO-E](https://transparency.entsoe.eu/) | Day-ahead electricity prices | 27 European bidding zones | Once/day |
| [ENTSO-E](https://transparency.entsoe.eu/) | Actual load, generation mix, cross-border flows | 27 zones + 15 borders | Every 15 min |
| [EIA Open Data](https://www.eia.gov/opendata/) | RTO electricity demand | 13 US regions | Every 30 min |
| [Visual Crossing](https://www.visualcrossing.com/) | Temperature, wind, humidity, solar radiation | 20 cities | Every 30 min |

> **Note:** Open-Meteo is blocked on Fabric Trial Spark network. Visual Crossing used as replacement — 1,000 records/day free tier, commercial use allowed.

---

## Rate Limiting Strategy

| Source | Limit | Our Usage | Headroom |
|---|---|---|---|
| ENTSO-E | 400 req/min per token | ~2 req/min average | 99% |
| EIA | Throttled per hour (unpublished) | ~1 req/min average | Conservative |
| Visual Crossing | 1,000 records/day | 960/day (20 cities × 48 cycles) | 4% |

**Protections applied:**
- Event-aligned polling — each source polled at its actual update frequency
- Exponential backoff with jitter on all API calls (`2^attempt + random jitter`)
- `NoMatchingDataError` skipped immediately — no point retrying missing data
- API keys stored in Fabric Environment (Spark properties) — never hardcoded
- Arrow optimization disabled for nullable float64 columns — prevents BufferHolder error

---

## Bronze Layer — 5 KQL Tables

| Table | Source | Frequency | Live Records |
|---|---|---|---|
| `raw_electricity_prices` | ENTSO-E (27 zones) + EIA (13 RTOs) | Once/day + every 30 min | 2,556 |
| `raw_electricity_load` | ENTSO-E | Every 15 min | 120 |
| `raw_generation_mix` | ENTSO-E | Every 15 min | 1,669 |
| `raw_cross_border_flows` | ENTSO-E | Every 15 min | 90 |
| `raw_weather` | Visual Crossing | Every 30 min | 20 |

All tables: 90-day retention, recoverability disabled (Trial-optimised).

---

## Medallion Layers

### Bronze — Raw Ingestion
- **Storage:** KQL Database (`pulsegrid_bronze`)
- **Pattern:** Append-only, no transformations, schema-on-read
- **Retention:** 90 days

### Silver — Cleansed
- **Storage:** Lakehouse Delta
- **Transformations:** Deduplication, null handling, unit normalization, schema enforcement
- **Spark Optimizations:** Predicate pushdown, native functions (no UDFs), repartition by region + hour, parallel processing via ThreadPoolExecutor

### Gold — Curated + ML-Ready
- **Storage:** Lakehouse Delta
- **Features:** Lag-12h price, rolling volatility, load factor, generation mix ratios, weather features, hour-of-week, is-holiday
- **Spark Optimizations:** Window functions, AQE, broadcast join (holidays), Delta OPTIMIZE + ZORDER
- **Predictions:** XGBoost binary classifier results written back with SHAP values

---

## ML — Price Spike Predictor

| Attribute | Detail |
|---|---|
| Problem | Binary classification — will price exceed 90th percentile in next 2 hours? |
| Algorithm | XGBoost |
| Features | Lag-12h price, rolling mean/volatility, load factor, wind %, solar %, nuclear %, cross-border net flow, temperature, hour-of-week, is-holiday |
| Explainability | SHAP values stored in Gold for AI agent consumption |
| Tracking | MLflow experiment tracking (Fabric-native) |
| Retraining | Weekly via Fabric Pipeline |

---

## AI Agent

A **Claude API + Streamlit** application that lets users query the Gold lakehouse in plain English.

**Example queries:**
- *"Why is a price spike predicted for tonight at 6 PM?"*
- *"Which region had the highest price volatility this week?"*
- *"How does wind generation affect German prices?"*
- *"Show me the top 5 hours with predicted spikes for tomorrow"*

---

## Project Structure

```
pulsegrid-fabric-realtime/
│
├── screenshots/
│   ├── phase1_workspace_overview.png
│   ├── phase1_bronze_table_created.png
│   ├── phase1_bronze_all_tables_created.png
│   ├── phase1_env_keys_added.png
│   ├── phase1_poller_01a_output.png
│   ├── phase1_poller_01b_output.png
│   ├── phase1_poller_01c_output.png
│   └── phase1_bronze_live_data_verified.png
│
├── notebooks/
│   ├── 01a_daily_price_poller.ipynb
│   ├── 01b_realtime_poller.ipynb
│   ├── 01c_weather_eia_poller.ipynb
│   ├── 02_silver_cleansing.ipynb
│   ├── 03_gold_features.ipynb
│   └── 04_ml_spike_predictor.ipynb
│
├── streamlit/
│   └── app.py
│
├── README.md
└── TECHSPEC.md
```

---

## Phases

| Phase | Description | Status |
|---|---|---|
| 1 | Bronze Layer — Workspace, Eventhouse, 5 KQL tables, 3 pollers, live data | ✅ Done |
| 2 | Silver Layer — Parallel PySpark cleansing + Spark optimizations | ✅ Done |
| 3 | Gold Layer — Feature engineering, Delta OPTIMIZE + ZORDER | ✅ Done |
| 4 | ML — XGBoost spike predictor, MLflow tracking, SHAP | ✅ Done |
| 5 | Power BI Semantic Model + real-time dashboard | 🔄 In Progress |
| 6 | AI Agent — Claude API + Streamlit | ⬜ Pending |

---

## Author

**Jayanth Dolai**
Senior Data Engineer — Azure · Databricks · Microsoft Fabric
Certifications: Databricks DE Associate · DP-900 · DP-700 · DP-600 · Generative AI Associate

[LinkedIn](https://www.linkedin.com/in/jayanth-dolai-7b115213a/) · [GitHub](https://github.com/demonjd2026-afk)
