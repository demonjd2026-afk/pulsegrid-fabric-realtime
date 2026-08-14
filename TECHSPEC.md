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
| Spark network restrictions | Open-Meteo blocked — replaced with Visual Crossing Weather API |
| Trial Spark capacity (430 limit) | Pollers run sequentially, not simultaneously |
| Free API tier limits | Event-aligned polling — each source polled at its actual update frequency |
| API key security | Fabric Environment Spark properties — keys never hardcoded in notebooks or Git |
| Trial storage limits | 90-day retention, recoverability disabled on all KQL tables |

---

## Phase 1 — Bronze Layer (Data Ingestion)

### Objective

Establish the real-time ingestion foundation. Raw electricity market data from four public APIs lands into a KQL Database as the Bronze layer — append-only, no transformations, schema-on-read. Five dedicated tables capture prices, load, generation mix, cross-border flows, and weather. Three event-aligned poller notebooks feed the tables at different cadences matching each source's actual update frequency.

---

### 1.1 Fabric Workspace Setup

**Workspace:** `PulseGrid` — created on Microsoft Fabric Trial (54 days remaining at project start).

**Items provisioned:**

| Item | Type | Role |
|---|---|---|
| `pulsegrid_eventhouse` | Eventhouse | Container for KQL databases |
| `pulsegrid_bronze` | KQL Database | Bronze raw data store |
| `pulsegrid_eventstream` | Eventstream | Real-time ingestion pipeline (reserved) |
| `pulsegrid_lakehouse` | Lakehouse | Silver + Gold Delta store |
| `pulsegrid_env` | Environment | API key store + library management |

![Workspace Overview](screenshots/phase1_workspace_overview.png)

---

### 1.2 Fabric Environment — Secret Management

**Environment:** `pulsegrid_env` — stores all API credentials as Spark properties. Keys read at runtime via `spark.conf.get()`. Never hardcoded in notebooks or committed to Git.

**Spark properties configured:**

| Property | Source |
|---|---|
| `spark.pulsegrid.entsoe_token` | ENTSO-E Transparency Platform |
| `spark.pulsegrid.eia_key` | EIA Open Data |
| `spark.pulsegrid.visualcrossing_key` | Visual Crossing Weather API |

![Environment Keys](screenshots/phase1_env_keys_added.png)

---

### 1.3 API Registration & Rate Limits

| Source | Registration | Limit | Daily Usage | Headroom |
|---|---|---|---|---|
| ENTSO-E | Free, email verification | 400 req/min per token | ~6,500 calls | 99% |
| EIA | Free, instant API key | Throttled/hour (unpublished) | ~624 calls | Conservative |
| Visual Crossing | Free, email verification | 1,000 records/day | 960 records | 4% |
| Open-Meteo | No registration | 10,000 calls/day | **Blocked on Fabric** | N/A |

**Open-Meteo finding:** Fabric Trial Spark executors block outbound HTTP to `api.open-meteo.com` (ReadTimeout on all attempts). EIA (`api.eia.gov`) is reachable. Visual Crossing (`weather.visualcrossing.com`) confirmed reachable and used as replacement.

---

### 1.4 Rate Limiting Strategy — Event-Aligned Polling

**Problem:** Naive 5-minute polling fetches the same value repeatedly. ENTSO-E day-ahead prices are published once per day — polling every 5 minutes wastes 287 of 288 daily calls on duplicate data.

**Solution:** Three notebooks, each polling at the source's actual update frequency.

| Notebook | Schedule | Sources | Tables Written |
|---|---|---|---|
| `01a_daily_price_poller` | Once/day at 13:00 CET | ENTSO-E day-ahead prices (27 zones) | `raw_electricity_prices` |
| `01b_realtime_poller` | Every 15 min | ENTSO-E load + generation + cross-border | `raw_electricity_load`, `raw_generation_mix`, `raw_cross_border_flows` |
| `01c_weather_eia_poller` | Every 30 min | Visual Crossing (20 cities) + EIA (13 RTOs) | `raw_weather`, `raw_electricity_prices` |

**Additional protections:**
- Exponential backoff with jitter: `2^attempt + random(0, 1.5)` seconds between retries
- `NoMatchingDataError` skipped immediately — data doesn't exist, retrying wastes quota
- Two-stage fetch in `01b`: narrow 30-min window first, wide 6-hour fallback for slow TSOs
- Temperature fetched once per region per cycle — not once per record
- Arrow optimization disabled for nullable float64 columns — prevents `BufferHolder negative size` error
- Sequential poller execution — Fabric Trial 430 capacity error triggered when running simultaneously

---

### 1.5 Poller Results — First Live Run

**`01a_daily_price_poller`** — 2026-08-14 06:41 UTC

| Metric | Value |
|---|---|
| Zones polled | 27 / 27 |
| Records written | 2,520 |
| Failed regions | None |
| Duration | 246.4s |

![01a Poller Output](screenshots/phase1_poller_01a_output.png)

---

**`01b_realtime_poller`** — 2026-08-14 07:06 UTC

| Metric | Value |
|---|---|
| Load records | 120 (23 narrow + 4 wide window) |
| Generation records | 1,669 (22 narrow + 5 wide window) |
| Flow records | 90 (14 pairs — SE-3→DK-2 unavailable) |
| Total written | 1,879 |
| Duration | 207.3s |

> SE-3→DK-2 cross-border flow not published by ENTSO-E — `NoMatchingDataError`, skipped immediately without retry.

![01b Poller Output](screenshots/phase1_poller_01b_output.png)

---

**`01c_weather_eia_poller`** — 2026-08-14 08:29 UTC

| Metric | Value |
|---|---|
| Weather records | 20 / 20 cities |
| EIA records | 36 (13 RTOs × 3 hourly records) |
| Total written | 56 |
| Duration | 220.2s |

![01c Poller Output](screenshots/phase1_poller_01c_output.png)

---

### 1.6 Bronze Tables — Schema & Live Record Counts

![All Bronze Tables](screenshots/phase1_bronze_all_tables_created.png)
![Live Data Verified](screenshots/phase1_bronze_live_data_verified.png)

| Table | Records | Update Frequency |
|---|---|---|
| `raw_electricity_prices` | 2,556 | Once/day (EU) + every 30 min (US) |
| `raw_electricity_load` | 120 | Every 15 min |
| `raw_generation_mix` | 1,669 | Every 15 min |
| `raw_cross_border_flows` | 90 | Every 15 min |
| `raw_weather` | 20 | Every 30 min |
| **Total** | **4,455** | |

All tables created with 90-day soft-delete retention, recoverability disabled.

---

### 1.7 Phase 1 Summary

| Item | Status |
|---|---|
| Fabric workspace `PulseGrid` created | ✅ |
| Eventhouse + KQL Database `pulsegrid_bronze` | ✅ |
| Lakehouse `pulsegrid_lakehouse` | ✅ |
| Environment `pulsegrid_env` + 3 API keys | ✅ |
| All 5 Bronze KQL tables + retention policies | ✅ |
| `01a_daily_price_poller` — 2,520 records live | ✅ |
| `01b_realtime_poller` — 1,879 records live | ✅ |
| `01c_weather_eia_poller` — 56 records live | ✅ |
| Open-Meteo blocked → Visual Crossing substituted | ✅ |
| Total Bronze records: 4,455 | ✅ |

---

## Phase 2 — Silver Layer (Parallel PySpark Cleansing)

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
| Predicate pushdown on `ingestion_date`, `region` | Silver | Avoids full Delta scan; leverages KQL + Delta file skipping |
| Native Spark functions only (no UDFs) | Silver | Catalyst can optimize; no Python↔JVM serialization overhead |
| `repartition()` by `region` + `hour` | Silver | Aligns write partitions to Gold aggregation access patterns |
| Parallel processing via `ThreadPoolExecutor` | Silver | All 5 tables cleansed simultaneously; total time ≈ slowest table |
| `broadcast()` hint on holidays table | Gold | ~300 row table; eliminates shuffle on large price table |
| Window functions for lag features | Gold | Fully distributed; no `collect()` to driver |
| AQE (Adaptive Query Execution) | Gold | Post-shuffle partition coalescing on aggregations |
| `cache()` on feature table | ML | Feature table read twice (train + score); avoids re-scan |
| `persist(MEMORY_AND_DISK)` before train/test split | ML | Split computed twice otherwise |
| Delta `OPTIMIZE` + `ZORDER BY (region, event_time)` | Gold | Improves read performance for Semantic Model + agent queries |
| `partitionBy("year","month","day")` at write | Silver/Gold | Right-sized partitioning; avoids small-files problem |

---

## Appendix B — ENTSO-E Bidding Zone Codes (27 Zones)

| Region | Zone Key |
|---|---|
| FR | 10YFR-RTE------C |
| ES | 10YES-REE------0 |
| NL | 10YNL----------L |
| BE | 10YBE----------2 |
| PL | 10YPL-AREA-----S |
| AT | 10YAT-APG------L |
| CH | 10YCH-SWISSGRIDZ |
| PT | 10YPT-REN------W |
| FI | 10YFI-1--------U |
| CZ | 10YCZ-CEPS-----N |
| SK | 10YSK-SEPS-----K |
| HU | 10YHU-MAVIR----U |
| RO | 10YRO-TEL------P |
| BG | 10YCA-BULGARIA-R |
| HR | 10YHR-HEP------M |
| GR | 10YGR-HTSO-----Y |
| SI | 10YSI-ELES-----O |
| RS | 10YCS-SERBIATSOV |
| LT | 10YLT-1001A0008Q |
| LV | 10YLV-1001A00074 |
| DE-LU | 10Y1001A1001A82H |
| IT-NO | 10Y1001A1001A73I |
| DK-1 | 10YDK-1--------W |
| DK-2 | 10YDK-2--------M |
| SE-3 | 10Y1001A1001A46L |
| NO-2 | 10YNO-2--------T |
| EE | 10Y1001A1001A39I |

---

*Last updated: Phase 1 complete — August 2026*
