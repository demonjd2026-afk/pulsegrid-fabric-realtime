# PulseGrid ⚡

### Real-Time Energy Market Intelligence Platform on Microsoft Fabric

> A production-grade medallion lakehouse that ingests live electricity prices from European and US energy markets, predicts price spikes with XGBoost, explains every prediction with SHAP, and serves it all through a Power BI semantic model and a Claude-powered Streamlit analyst.

**🔗 Live app —** https://pulsegrid-energy.streamlit.app/
**📦 Repository —** https://github.com/demonjd2026-afk/pulsegrid-fabric-realtime

---

## Overview

PulseGrid is an end-to-end real-time data engineering project built entirely on **Microsoft Fabric Trial**. It covers the full platform lifecycle — raw API ingestion, medallion refinement, feature engineering, model training, explainability, BI serving, orchestration, alerting and an AI analyst — using only Fabric-native components and free public APIs.

The platform answers one core question:

> *"Will electricity prices spike in the next 2 hours, and why?"*

Six scheduled Fabric Data Pipelines move data from four public APIs through Bronze, Silver and Gold, retrain a spike classifier nightly, and publish a Gold snapshot that the public Streamlit app reads.

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
              ┌────────────────▼────────────────┐
              │   3 Scheduled Poller Notebooks  │
              │  01a — Daily price poller       │
              │  01b — 15-min realtime poller   │
              │  01c — 30-min weather/EIA poller│
              └────────────────┬────────────────┘
                               │
         ┌─────────────────────▼──────────────────────┐
         │         BRONZE — KQL Database               │
         │         pulsegrid_bronze (Eventhouse)       │
         │                                             │
         │  raw_electricity_prices                     │
         │  raw_electricity_load                       │
         │  raw_generation_mix                         │
         │  raw_cross_border_flows                     │
         │  raw_weather                                │
         │                                             │
         │  Append-only · Schema-on-read · 90d retain  │
         └─────────────────────┬──────────────────────┘
                               │  02_silver_cleansing (every 30 min)
         ┌─────────────────────▼──────────────────────┐
         │         SILVER — Lakehouse (Delta)          │
         │  Parallel PySpark cleansing — 5 tables      │
         │  Dedup · Nulls · Units · Schema enforce     │
         │  Predicate pushdown · Repartition · MERGE   │
         └─────────────────────┬──────────────────────┘
                               │  03_gold_features (hourly)
         ┌─────────────────────▼──────────────────────┐
         │         GOLD — Lakehouse (Delta)            │
         │  6 curated tables                           │
         │  Window features · Aggregates               │
         │  Predictions · SHAP values                  │
         │  Delta OPTIMIZE + ZORDER                    │
         └──────────┬──────────────────────┬───────────┘
                    │                      │  04_ml_spike_predictor
                    │                      │  (daily 02:00 CET)
         ┌──────────┴──────────┐  ┌────────▼─────────────────┐
         ▼                     ▼  │  XGBoost + MLflow + SHAP │
┌─────────────────┐  ┌───────────────────────────┐
│   Power BI      │  │  Streamlit + Plotly       │
│ Semantic Model  │  │  + Claude analyst         │
│  Direct Lake    │  │  JSON Gold snapshot       │
└─────────────────┘  └───────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Platform | Microsoft Fabric Trial (`PulseGrid` workspace) |
| Real-Time Ingestion | KQL Database (Eventhouse) + scheduled Fabric Notebooks |
| Bronze Store | KQL Database — 5 append-only tables |
| Silver / Gold Store | Lakehouse — Delta tables, OPTIMIZE + ZORDER |
| Transformations | PySpark — AQE, broadcast joins, window functions, no UDFs |
| Secret Management | Fabric Environment Spark properties (`pulsegrid_env`) |
| ML Framework | XGBoost + MLflow + SHAP |
| Orchestration | 6 Fabric Data Pipelines with schedules + failure email |
| Monitoring | Fabric Activator rule on Bronze data freshness |
| BI Layer | Power BI Semantic Model (Direct Lake over OneLake) |
| AI Analyst | Claude API + Streamlit + Plotly |
| Hosting | Streamlit Community Cloud |

---

## Data Sources

| Source | Data | Zones / Regions | Poll Frequency |
|---|---|---|---|
| [ENTSO-E](https://transparency.entsoe.eu/) | Day-ahead electricity prices | 27 European bidding zones | Once/day, 13:00 CET |
| [ENTSO-E](https://transparency.entsoe.eu/) | Actual load, generation mix, cross-border flows | 27 zones + 15 borders | Every 15 min |
| [EIA Open Data](https://www.eia.gov/opendata/) | RTO electricity demand | 13 US balancing authorities | Every 30 min |
| [Visual Crossing](https://www.visualcrossing.com/) | Temperature, wind, humidity, solar radiation | 20 cities | Every 30 min |

> **Note:** Open-Meteo is blocked on the Fabric Trial Spark network. Visual Crossing is used instead — 1,000 records/day free tier, commercial use allowed.

---

## Rate Limiting Strategy

| Source | Limit | Our Usage | Headroom |
|---|---|---|---|
| ENTSO-E | 400 req/min per token | ~2 req/min average | 99% |
| EIA | Throttled per hour (unpublished) | ~1 req/min average | Conservative |
| Visual Crossing | 1,000 records/day | 960/day (20 cities × 48 cycles) | 4% |

**Protections applied**

- Event-aligned polling — each source is polled at its actual publication frequency, never faster
- Exponential backoff with jitter on every API call (`2^attempt + random jitter`)
- `NoMatchingDataError` skipped immediately — no retries against data that does not exist
- Two-stage fetch in `01b` — narrow 30-min window first, wide 6-hour fallback for slow TSOs
- API keys stored as Fabric Environment Spark properties — never hardcoded, never committed
- Arrow optimization disabled for nullable float64 columns — prevents the `BufferHolder` error
- Pollers run on separate schedules — simultaneous runs trip the Fabric Trial 430 capacity error

---

## Medallion Layers

### Bronze — Raw Ingestion

**Storage:** KQL Database `pulsegrid_bronze` · **Pattern:** append-only, schema-on-read, no transformations · **Retention:** 90 days, recoverability disabled (Trial-optimised).

| Table | Source | Frequency |
|---|---|---|
| `raw_electricity_prices` | ENTSO-E (27 zones) + EIA (13 RTOs) | Once/day + every 30 min |
| `raw_electricity_load` | ENTSO-E | Every 15 min |
| `raw_generation_mix` | ENTSO-E | Every 15 min |
| `raw_cross_border_flows` | ENTSO-E | Every 15 min |
| `raw_weather` | Visual Crossing | Every 30 min |

### Silver — Cleansed

**Storage:** Lakehouse Delta · **Notebook:** `02_silver_cleansing`

Five Bronze tables are read through the KQL connector and processed **concurrently** with a `ThreadPoolExecutor`, so wall time tracks the slowest table rather than the sum of all five.

- Deduplication via `row_number()` over the natural key, ordered by `ingestion_time DESC`
- Physical-plausibility nulling (negative load, out-of-range prices, impossible sensor values)
- Unit and case normalization (`region` upper, `fuel_type` title case)
- Self-flow removal on cross-border data
- Idempotent MERGE on the natural key — safe for pipeline retries
- `partitionBy(year, month, day)` — avoids the small-files problem from tick writes

### Gold — Curated + ML-Ready

**Storage:** Lakehouse Delta · **Notebooks:** `03_gold_features`, `04_ml_spike_predictor`

| Gold Table | Purpose |
|---|---|
| `gold_price_features` | Core ML feature table — lags, rolling stats, calendar, weather, spike label |
| `gold_generation_summary` | Generation mix per zone per hour + renewable / nuclear / fossil % |
| `gold_flow_summary` | Net cross-border position per zone (Exporter / Importer / Balanced) |
| `gold_price_aggregates` | Hourly + daily price aggregates — the Power BI serving layer |
| `gold_price_predictions` | XGBoost spike predictions + probabilities + correctness |
| `gold_shap_values` | Long-format SHAP contributions — one row per (region, time, feature) |

Optimizations: `cache()` on the reused price frame, `broadcast()` on the holidays table, `rangeBetween` rolling windows, `percentile_approx()` for the p90 threshold, AQE on aggregations, and Delta `OPTIMIZE ... ZORDER BY (region, event_time)` on every Gold table.

---

## ML — Price Spike Predictor

| Attribute | Detail |
|---|---|
| Problem | Binary classification — will price exceed the 90th percentile in the next 2 hours? |
| Algorithm | XGBoost (`n_estimators=100`, `max_depth=4`, `learning_rate=0.1`, `min_child_weight=5`, auto `scale_pos_weight`) |
| Features | 14 — price, 1h/12h/24h lags, 6h rolling mean and volatility, hour-of-day, day-of-week, is-weekend, temperature, wind speed, humidity, solar radiation, load |
| Split | Time-aware — older records train, newer records test (no leakage) |
| Explainability | SHAP `TreeExplainer`, long-format values written back to Gold |
| Tracking | MLflow experiment `pulsegrid_spike_predictor` — params, metrics, model artifact |
| Retraining | Daily at 02:00 CET via `pipeline_04_ml` |

### Results — latest scored run

Measured directly from the published Gold snapshot (`model_run_id 9c0e9b3e…`, 530 scored rows across 27 bidding zones):

| Metric | Value |
|---|---|
| Accuracy | **72.3%** (383 of 530) |
| Precision | **73.6%** |
| Recall | **40.7%** |
| F1 score | **0.524** |
| Confusion matrix | TP 81 · FP 29 · FN 118 · TN 302 |

The model is deliberately conservative: when it calls a spike it is right roughly three times in four, at the cost of missing quieter spikes. That trade-off is the right one for an alerting surface, where a false alarm is more expensive than a missed marginal event.

### What drives the prediction

Mean absolute SHAP across all 7,700 scored explanations:

| Feature | Mean \|SHAP\| |
|---|---|
| `price_eur_mwh` | 1.887 |
| `price_rolling_avg_6h` | 1.672 |
| `price_lag_1h` | 0.773 |
| `price_lag_24h` | 0.671 |
| `price_rolling_std_6h` | 0.669 |
| `price_lag_12h` | 0.558 |
| `hour_of_day` | 0.525 |
| `load_mw` | 0.028 |

Price history and recent volatility dominate. Weather features contribute nothing yet — with two days of live data there is not enough seasonal variance for the model to separate on them, and their SHAP values are flat zero. That is a data-volume result, not a modelling error.

---

## Serving Layer

### Power BI — `pulsegrid_semantic_model`

Direct Lake semantic model reading Gold Delta tables straight from OneLake — no import, no scheduled refresh, no data duplication. Three bidirectional region relationships, five visuals on a *Market Overview* page: region slicer, average price by hour of day, hourly vs daily price trend, spike prediction table, and renewable share by region.

### Streamlit — [pulsegrid-energy.streamlit.app](https://pulsegrid-energy.streamlit.app/)

A two-page application built on the published Gold snapshot.

**Dashboard** — six KPI tiles, a zone price board ranked high → low with percentile colouring, a multi-zone hourly price curve, a spike watchlist, a min–max zone spread chart, a stacked generation-mix chart, and a SHAP driver chart filterable by zone.

**AI Chat** — a Claude-powered market analyst. Every turn is grounded in a compact context block assembled from the Gold tables (latest zone prices, spike predictions, generation mix, SHAP importance) so the model quotes real figures and never invents a number. Replies stream token by token.

**Why a JSON snapshot rather than a live Fabric query:** Fabric bearer tokens expire after roughly an hour, which would break a deployed app inside a single session. Cell 11 of `03_gold_features` serialises the four Gold tables the app reads and pushes them straight to this repo through the GitHub contents API — so the app has zero runtime auth dependency.

---

## Orchestration & Monitoring

Six Fabric Data Pipelines, each wrapping one notebook, each with failure email notification enabled.

| Pipeline | Notebook | Schedule |
|---|---|---|
| `pipeline_01a_daily_price` | `01a_daily_price_poller` | Daily 13:00 CET |
| `pipeline_01b_realtime` | `01b_realtime_poller` | Every 15 min |
| `pipeline_01c_weather_eia` | `01c_weather_eia_poller` | Every 30 min |
| `pipeline_02_silver` | `02_silver_cleansing` | Every 30 min |
| `pipeline_03_gold` | `03_gold_features` | Every 1 hour |
| `pipeline_04_ml` | `04_ml_spike_predictor` | Daily 02:00 CET |

**Freshness alert —** a Fabric Activator rule, `pulsegrid_bronze_freshness_alert`, runs a KQL query against `pulsegrid_bronze` every 30 minutes:

```kusto
raw_electricity_prices
| where ingestion_time > ago(2h)
| count
| where Count == 0
```

If no price data has landed in two hours it emails an alert naming the three pollers to check. Silent pipeline failure is the failure mode that actually hurts a real-time platform, so it is the one thing explicitly monitored.

---

## Results at a Glance

From the Gold snapshot published 14 Aug 2026, 22:00 UTC:

| Metric | Value |
|---|---|
| Bidding zones priced | 29 (of 40 tracked across ENTSO-E + EIA) |
| Mean day-ahead price, latest hour | €144 / MWh |
| Peak zone | €186 / MWh — Spain |
| Cheapest zone | ~€0 / MWh — Belgium |
| Zones flagged for spike risk | 13 of 40 scored |
| Renewable share, reporting zones | 80% average across 11 generating zones |
| Price aggregate rows | 857 (789 hourly + 68 daily) |
| Scored predictions | 550 across 40 zones |
| SHAP explanation records | 7,700 (14 features × 550 predictions) |
| Gold tables served | 6 |

---

## Project Structure

```
pulsegrid-fabric-realtime/
│
├── notebooks/
│   ├── 01a_daily_price_poller.ipynb     ENTSO-E day-ahead prices → Bronze
│   ├── 01b_realtime_poller.ipynb        Load, generation, flows → Bronze
│   ├── 01c_weather_eia_poller.ipynb     Weather + US demand → Bronze
│   ├── 02_silver_cleansing.ipynb        Parallel PySpark cleansing → Silver
│   ├── 03_gold_features.ipynb           Features, aggregates, snapshot publish
│   └── 04_ml_spike_predictor.ipynb      XGBoost + MLflow + SHAP → Gold
│
├── streamlit/
│   ├── app.py                           Entry point, top-bar nav, routing
│   ├── lib/
│   │   ├── data.py                      Gold snapshot loader + derived views
│   │   └── theme.py                     Design system, CSS, Plotly template
│   ├── views/
│   │   ├── dashboard.py                 Market dashboard
│   │   ├── agent.py                     Claude analyst chat
│   │   └── about.py                     Architecture reference page
│   ├── data/                            Gold JSON snapshot (published from Fabric)
│   └── requirements.txt
│
├── screenshots/                         Build evidence, phase by phase
├── .streamlit/config.toml               Dark theme tokens
├── README.md
├── TECHSPEC.md                          Phase-by-phase engineering journal
├── PulseGrid — Project Presentation.pdf 18-slide project overview deck
└── PulseGrid — Energy Market Dashboard.pdf   Power BI report export
```

---

## Running Locally

```bash
git clone https://github.com/demonjd2026-afk/pulsegrid-fabric-realtime.git
cd pulsegrid-fabric-realtime

pip install -r requirements.txt
streamlit run streamlit/app.py
```

The dashboard runs entirely from the committed Gold snapshot and needs no credentials. To enable the AI Chat page, add an Anthropic API key:

```toml
# .streamlit/secrets.toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

On Streamlit Community Cloud the same key goes under **App settings → Secrets**.

---

## Phases

| Phase | Description | Status |
|---|---|---|
| 1 | Bronze — workspace, Eventhouse, 5 KQL tables, 3 pollers, live data | ✅ Done |
| 2 | Silver — parallel PySpark cleansing + Spark optimizations | ✅ Done |
| 3 | Gold — feature engineering, aggregates, OPTIMIZE + ZORDER | ✅ Done |
| 4 | ML — XGBoost spike predictor, MLflow tracking, SHAP write-back | ✅ Done |
| 5 | Power BI Direct Lake semantic model + dashboard | ✅ Done |
| 6 | AI analyst — Claude API + Streamlit, deployed publicly | ✅ Done |
| 7 | Orchestration — 6 Fabric pipelines + Bronze freshness alert | ✅ Done |

---

## Author

**Jayanth Dolai**
Senior Data Engineer — Azure · Databricks · Microsoft Fabric
Certifications: Databricks DE Associate · DP-900 · DP-700 · DP-600 · Generative AI Associate

[LinkedIn](https://www.linkedin.com/in/jayanth-dolai-7b115213a/) · [GitHub](https://github.com/demonjd2026-afk)
