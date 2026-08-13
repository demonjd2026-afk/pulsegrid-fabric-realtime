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
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                             │
│   ENTSO-E API        EIA Open Data        Open-Meteo Weather    │
└────────┬─────────────────┬──────────────────────┬──────────────┘
         │                 │                      │
         └─────────────────┴──────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   Fabric Eventstream   │  ← Python poller (rate-gated)
              └────────────┬───────────┘
                           │
                           ▼
         ┌─────────────────────────────────┐
         │  BRONZE — KQL Database          │
         │  pulsegrid_bronze               │
         │  raw_electricity_prices         │
         │  Append-only · Schema-on-read   │
         └─────────────────┬───────────────┘
                           │
                           ▼
         ┌─────────────────────────────────┐
         │  SILVER — Lakehouse (Delta)     │
         │  PySpark cleansing              │
         │  Dedup · Nulls · Schema enforce │
         │  Repartition by region + hour   │
         └─────────────────┬───────────────┘
                           │
                           ▼
         ┌─────────────────────────────────┐
         │  GOLD — Lakehouse (Delta)       │
         │  Window functions · Aggregates  │
         │  ML feature table               │
         │  Spike predictions (XGBoost)    │
         │  Delta OPTIMIZE + ZORDER        │
         └──────────┬──────────────────────┘
                    │
         ┌──────────┴──────────────┐
         │                         │
         ▼                         ▼
┌─────────────────┐    ┌────────────────────────┐
│ Power BI        │    │ Claude API + Streamlit  │
│ Semantic Model  │    │ AI Agent                │
│ Direct Lake     │    │ Natural language → SQL  │
└─────────────────┘    └────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Platform | Microsoft Fabric Trial |
| Real-Time Ingestion | Fabric Eventstream |
| Bronze Store | KQL Database (Eventhouse) |
| Silver / Gold Store | Lakehouse — Delta tables |
| Transformations | PySpark (Fabric Notebooks) |
| ML Framework | XGBoost + MLflow + SHAP |
| Orchestration | Fabric Data Pipeline |
| BI Layer | Power BI Semantic Model (Direct Lake) |
| AI Agent | Claude API + Streamlit |

---

## Data Sources

| Source | Data | API Limit | Pull Frequency |
|---|---|---|---|
| [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/) | European day-ahead electricity prices + grid load | Free, registration required | Every 5 min |
| [EIA Open Data](https://www.eia.gov/opendata/) | US hourly electricity prices | Free API key | Every 5 min |
| [Open-Meteo](https://open-meteo.com/) | Temperature (weather correlation feature) | 10,000 calls/day, no auth | Every 5 min |

> **Rate Limiting Strategy:** Python poller notebook uses exponential backoff with jitter. All three APIs are polled every 5 minutes — well within free tier limits. Fabric Pipeline schedules the poller with built-in retry logic.

---

## Medallion Layers

### Bronze — Raw Ingestion
- **Storage:** KQL Database (`pulsegrid_bronze`)
- **Table:** `raw_electricity_prices`
- **Pattern:** Append-only, no transformations, schema-on-read
- **Retention:** 90 days

### Silver — Cleansed
- **Storage:** Lakehouse Delta (`silver.electricity_prices`)
- **Transformations:** Deduplication, null handling, unit normalization, schema enforcement
- **Spark Optimizations:** Predicate pushdown, native functions (no UDFs), repartition by `region` + `hour`

### Gold — Curated + ML-Ready
- **Storage:** Lakehouse Delta (`gold.electricity_features`, `gold.price_predictions`)
- **Features:** Lag-12h price, rolling volatility, load factor, temperature delta, hour-of-week, is-holiday flag
- **Spark Optimizations:** Window functions, AQE, broadcast join (holidays), Delta OPTIMIZE + ZORDER
- **Predictions:** XGBoost binary classifier results written back with SHAP values

---

## ML — Price Spike Predictor

| Attribute | Detail |
|---|---|
| Problem | Binary classification — will price exceed 90th percentile in next 2 hours? |
| Algorithm | XGBoost |
| Features | Lag-12h price, rolling mean/volatility, temperature delta, hour-of-week, is-holiday |
| Explainability | SHAP values stored in Gold for AI agent consumption |
| Tracking | MLflow experiment tracking (Fabric-native) |
| Retraining | Weekly via Fabric Pipeline |

---

## AI Agent

A **Claude API + Streamlit** application that lets users query the Gold lakehouse in plain English.

**Example queries:**
- *"Why is a price spike predicted for tonight at 6 PM?"*
- *"Which region had the highest price volatility this week?"*
- *"Show me the top 5 hours with predicted spikes for tomorrow"*

Claude translates the question into Spark SQL, queries the Gold Delta table, retrieves SHAP values, and explains the prediction in plain English.

---

## Project Structure

```
pulsegrid-fabric-realtime/
│
├── screenshots/                        # Phase-wise progress screenshots
│
├── notebooks/
│   ├── 01_bronze_poller.ipynb         # Python poller — API ingestion
│   ├── 02_silver_cleansing.ipynb      # PySpark Silver transformations
│   ├── 03_gold_features.ipynb         # Gold feature engineering
│   └── 04_ml_spike_predictor.ipynb    # XGBoost training + SHAP
│
├── streamlit/
│   └── app.py                         # Claude + Streamlit AI agent
│
├── README.md                          # Project overview (this file)
└── TECHSPEC.md                        # Phase-by-phase technical specification
```

---

## Phases

| Phase | Description | Status |
|---|---|---|
| 1 | Bronze Layer — Workspace, Eventhouse, KQL table, Eventstream | ✅ Done |
| 2 | Silver Layer — PySpark cleansing + Spark optimizations | 🔄 In Progress |
| 3 | Gold Layer — Feature engineering, Delta OPTIMIZE + ZORDER | ⬜ Pending |
| 4 | ML — XGBoost spike predictor, MLflow tracking, SHAP | ⬜ Pending |
| 5 | Power BI Semantic Model + real-time dashboard | ⬜ Pending |
| 6 | AI Agent — Claude API + Streamlit | ⬜ Pending |

---

## Author

**Jayanth Dolai**
Senior Data Engineer — Azure · Databricks · Microsoft Fabric
Certifications: Databricks DE Associate · DP-900 · DP-700 · DP-600 · Generative AI Associate

[LinkedIn](https://www.linkedin.com/in/jayanth-dolai-7b115213a/) · [GitHub](https://github.com/demonjd2026-afk)
