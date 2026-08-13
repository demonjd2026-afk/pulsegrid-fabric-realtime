# PulseGrid — Technical Specification

> Phase-by-phase engineering implementation journal for the PulseGrid Real-Time Energy Market Intelligence Platform on Microsoft Fabric.

---

## Document Purpose

This document serves as the authoritative technical reference for the PulseGrid project. It records every implementation decision, configuration, code, and validation step across all phases — providing full traceability from raw ingestion to AI-powered analytics.

---

## Platform Constraints & Design Decisions

| Constraint | Decision |
|---|---|
| Microsoft Fabric Trial | All components scoped to Trial-available features only |
| No Fabric Data Agent | Claude API + Streamlit used as the AI agent layer |
| Free API tier limits | Event-aligned polling strategy — each source polled at its actual update frequency |
| API key security | Fabric Environment (Spark properties) — keys never hardcoded in notebooks or Git |
| Trial capacity limits | Delta OPTIMIZE run post-load only; no continuous VACUUM |

---

## Phase 1 — Bronze Layer (Data Ingestion)

### Objective

Establish the real-time ingestion foundation. Raw electricity market data from three public APIs lands into a KQL Database as the Bronze layer — append-only, no transformations, schema-on-read. Five dedicated tables capture prices, load, generation mix, cross-border flows, and weather.

---

### 1.1 Fabric Workspace Setup

A new Fabric workspace named **PulseGrid** was created under the Trial license with the following description:

> *Real-time energy market intelligence platform on Microsoft Fabric. Medallion lakehouse (Bronze/Silver/Gold) with live electricity price ingestion, PySpark Spark optimizations, XGBoost price-spike prediction, and a Claude + Streamlit AI agent for natural language analytics.*

**Workspace items provisioned:**

| Item Name | Type | Role |
|---|---|---|
| `pulsegrid_eventhouse` | Eventhouse | Container for KQL databases |
| `pulsegrid_bronze` | KQL Database | Bronze raw data store |
| `pulsegrid_eventstream` | Eventstream | Real-time ingestion pipeline |
| `pulsegrid_lakehouse` | Lakehouse | Silver + Gold Delta store |
| `pulsegrid_env` | Environment | API key store + library management |

![Workspace Overview](screenshots/phase1_workspace_overview.png)

---

### 1.2 Fabric Environment — Secret Management

A Fabric Environment (`pulsegrid_env`) was created to store API credentials securely as Spark properties. This ensures API keys are never hardcoded in notebook source or committed to Git.

**Spark properties configured:**

| Property | Purpose |
|---|---|
| `spark.pulsegrid.entsoe_token` | ENTSO-E Transparency Platform API token |
| `spark.pulsegrid.eia_key` | EIA Open Data API key |

Keys are read at runtime in notebooks via:
```python
ENTSOE_API_TOKEN = spark.conf.get("spark.pulsegrid.entsoe_token")
EIA_API_KEY      = spark.conf.get("spark.pulsegrid.eia_key")
```

Environment published and attached to all poller notebooks.

![Environment Keys](screenshots/phase1_env_keys_added.png)

---

### 1.3 API Registration & Rate Limits

| Source | Registration | Limit | Our Usage |
|---|---|---|---|
| ENTSO-E | Free — email verification + token generation | 400 req/min per token | ~2 req/min avg |
| EIA | Free — instant API key via email | Throttled per hour (unpublished) | ~1 req/min avg |
| Open-Meteo | No registration — no API key needed | 10,000 calls/day | ~1,440 calls/day |

---

### 1.4 Rate Limiting Strategy — Event-Aligned Polling

**Problem with naive 5-minute polling:**
ENTSO-E day-ahead prices are published once per day. Polling every 5 minutes fetches the same value 288 times — wasting rate limit budget on duplicate data.

**Solution — Poll each source at its actual update frequency:**

| Notebook | Schedule | Sources | Tables Written |
|---|---|---|---|
| `01a_daily_price_poller` | Once/day at 13:00 CET | ENTSO-E day-ahead prices (26 zones) | `raw_electricity_prices` |
| `01b_realtime_poller` | Every 15 min | ENTSO-E load + generation + cross-border | `raw_electricity_load`, `raw_generation_mix`, `raw_cross_border_flows` |
| `01c_weather_eia_poller` | Every 30 min | Open-Meteo (30 cities) + EIA (13 RTOs) | `raw_weather`, `raw_electricity_prices` (US) |

**Additional protections:**
- Exponential backoff with jitter on every API call (`2^attempt + random(0, 1.0)` seconds)
- Poll guard — skips cycle if last run was less than minimum interval ago (state stored in Lakehouse Files)
- Temperature fetched once per region per cycle — not once per record
- All API calls wrapped in `call_with_retry()` with `MAX_RETRIES = 3`

**Daily API call budget:**

| Source | Calls/Day | Limit | Headroom |
|---|---|---|---|
| ENTSO-E total | ~6,500 | 576,000 (400/min) | 99% |
| EIA | ~312 | Unpublished | Conservative |
| Open-Meteo | ~1,440 | 10,000 | 85% |

---

### 1.5 Eventhouse & KQL Database

An **Eventhouse** (`pulsegrid_eventhouse`) was created as the managed container for KQL databases. The default KQL database was renamed to `pulsegrid_bronze`.

**Design rationale:** Eventhouse is the correct Fabric-native store for real-time append-only workloads. KQL Database provides sub-second query latency on time-series data — ideal for raw electricity ticks before promotion to Silver Delta tables.

---

### 1.6 Bronze Tables — Schema & Design

All 5 tables created in `pulsegrid_bronze` with 90-day retention and recoverability disabled.

![All Bronze Tables Created](screenshots/phase1_bronze_all_tables_created.png)

---

#### Table 1 — `raw_electricity_prices`

```kql
.create table raw_electricity_prices (
    ingestion_time : datetime,
    event_time     : datetime,
    region         : string,
    price_eur_mwh  : real,
    load_mw        : real,
    temperature_c  : real,
    source         : string
)
```

| Column | Rationale |
|---|---|
| `ingestion_time` | System timestamp — when record landed in Fabric |
| `event_time` | Market timestamp from API — used for dedup in Silver |
| `region` | Market zone (DE, FR, US-ERCOT etc.) |
| `price_eur_mwh` | Day-ahead price EUR/MWh (USD/MWh for EIA — tagged via source) |
| `source` | API lineage tag (ENTSO-E / EIA-ERCOT etc.) |

---

#### Table 2 — `raw_electricity_load`

```kql
.create table raw_electricity_load (
    ingestion_time : datetime,
    event_time     : datetime,
    region         : string,
    load_mw        : real,
    source         : string
)
```

Actual grid load in MW — updated every 15 minutes. Key demand-side feature for ML spike predictor.

---

#### Table 3 — `raw_generation_mix`

```kql
.create table raw_generation_mix (
    ingestion_time : datetime,
    event_time     : datetime,
    region         : string,
    fuel_type      : string,
    generation_mw  : real,
    source         : string
)
```

Generation by fuel type (solar, wind, nuclear, gas, hydro etc.) — one row per fuel type per region per timestamp. Wind % and solar % are strong negative price predictors (renewables suppress prices).

---

#### Table 4 — `raw_cross_border_flows`

```kql
.create table raw_cross_border_flows (
    ingestion_time : datetime,
    event_time     : datetime,
    from_region    : string,
    to_region      : string,
    flow_mw        : real,
    source         : string
)
```

Power flows between countries — positive = export, negative = import. Net import position is a strong price spike indicator.

---

#### Table 5 — `raw_weather`

```kql
.create table raw_weather (
    ingestion_time  : datetime,
    event_time      : datetime,
    region          : string,
    temperature_c   : real,
    wind_speed_ms   : real,
    humidity_pct    : real,
    solar_radiation : real,
    source          : string
)
```

Four weather variables per city — temperature drives heating/cooling demand; wind speed and solar radiation directly affect renewable generation output.

---

### 1.7 Retention Policies

Applied to all 5 tables:

```kql
.alter table <table_name> policy retention
@'{"SoftDeletePeriod": "90.00:00:00", "Recoverability": "Disabled"}'
```

90 days provides sufficient history for ML training. Recoverability disabled to conserve Trial storage capacity.

---

### 1.8 Phase 1 Summary

| Item | Status |
|---|---|
| Fabric workspace `PulseGrid` created | ✅ |
| Eventhouse `pulsegrid_eventhouse` provisioned | ✅ |
| KQL Database `pulsegrid_bronze` created | ✅ |
| Eventstream `pulsegrid_eventstream` created | ✅ |
| Lakehouse `pulsegrid_lakehouse` created | ✅ |
| Environment `pulsegrid_env` created + published | ✅ |
| API keys stored as Spark properties | ✅ |
| ENTSO-E API token registered | ✅ |
| EIA API key registered | ✅ |
| `raw_electricity_prices` table + retention | ✅ |
| `raw_electricity_load` table + retention | ✅ |
| `raw_generation_mix` table + retention | ✅ |
| `raw_cross_border_flows` table + retention | ✅ |
| `raw_weather` table + retention | ✅ |

---

## Phase 2 — Silver Layer (PySpark Cleansing + Spark Optimizations)

> 🔄 In Progress — details will be added upon completion.

---

## Phase 3 — Gold Layer (Feature Engineering)

> ⬜ Pending

---

## Phase 4 — ML (XGBoost Spike Predictor)

> ⬜ Pending

---

## Phase 5 — Power BI Semantic Model

> ⬜ Pending

---

## Phase 6 — AI Agent (Claude API + Streamlit)

> ⬜ Pending

---

## Appendix A — Spark Optimization Techniques

| Technique | Phase | Rationale |
|---|---|---|
| Predicate pushdown on `ingestion_date`, `region` | Silver | Avoids full Delta scan; leverages file skipping |
| Native Spark functions only (no UDFs) | Silver | Catalyst can optimize; no serialization overhead |
| `repartition()` by `region` + `hour` | Silver | Aligns write partitions to downstream query patterns |
| `broadcast()` hint on holidays table | Gold | ~300 row table; eliminates shuffle on large price table |
| Window functions for lag features | Gold | Fully distributed; no `collect()` to driver |
| AQE (Adaptive Query Execution) | Gold | Post-shuffle partition coalescing on aggregations |
| `cache()` on feature table | ML | Feature table read twice (train + score); avoids re-scan |
| `persist(MEMORY_AND_DISK)` before train/test split | ML | Split computed twice otherwise |
| Delta `OPTIMIZE` + `ZORDER BY (region, event_time)` | Gold | Improves read performance for Semantic Model + agent queries |
| `partitionBy("year","month","day")` at write | Gold | Avoids over-partitioning; right-sized for data volume |

---

## Appendix B — ENTSO-E Bidding Zone Codes

| Region | Zone Key | Country |
|---|---|---|
| DE | 10Y1001A1001A83F | Germany |
| FR | 10YFR-RTE------C | France |
| ES | 10YES-REE------0 | Spain |
| NL | 10YNL----------L | Netherlands |
| BE | 10YBE----------2 | Belgium |
| IT | 10YIT-GRTN-----B | Italy |
| PL | 10YPL-AREA-----S | Poland |
| AT | 10YAT-APG------L | Austria |
| CH | 10YCH-SWISSGRIDZ | Switzerland |
| PT | 10YPT-REN------W | Portugal |

---

*Last updated: Phase 1 complete — August 2026*
