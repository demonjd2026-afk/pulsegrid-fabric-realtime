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
| No CI/CD / Git Integration | Manual notebook development; Git push after each phase |
| Rate limiting (free APIs) | Python poller with exponential backoff + jitter; 5-min pull cadence |
| Trial capacity limits | Delta OPTIMIZE run post-load only; no continuous VACUUM |

---

## Phase 1 — Bronze Layer (Data Ingestion)

### Objective
Establish the real-time ingestion foundation. Raw electricity price and load data from three public APIs is streamed into a KQL Database as the Bronze layer — append-only, no transformations, schema-on-read.

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

![Workspace Overview](screenshots/phase1_workspace_overview.png)

---

### 1.2 Eventhouse & KQL Database

An **Eventhouse** (`pulsegrid_eventhouse`) was created as the managed container for KQL databases. The default KQL database was renamed to `pulsegrid_bronze` to align with the Bronze layer naming convention.

**Design rationale:** Eventhouse is the correct Fabric-native store for real-time append-only workloads. KQL Database provides sub-second query latency on time-series data, which is ideal for raw electricity price ticks before they are promoted to Silver Delta tables.

---

### 1.3 Bronze Table — `raw_electricity_prices`

The following KQL command was executed in `pulsegrid_bronze_queryset` to create the raw ingestion table:

```kql
.create table raw_electricity_prices (
    ingestion_time: datetime,
    event_time:     datetime,
    region:         string,
    price_eur_mwh:  real,
    load_mw:        real,
    temperature_c:  real,
    source:         string
)
```

**Schema design decisions:**

| Column | Type | Rationale |
|---|---|---|
| `ingestion_time` | datetime | System timestamp — when the record landed in Fabric |
| `event_time` | datetime | Market timestamp from the source API — used for dedup in Silver |
| `region` | string | Market zone identifier (e.g. DE, FR, US-ERCOT) |
| `price_eur_mwh` | real | Day-ahead electricity price in EUR/MWh |
| `load_mw` | real | Grid load in megawatts — key predictor feature |
| `temperature_c` | real | Ambient temperature — weather correlation feature for ML |
| `source` | string | API source tag (ENTSO-E / EIA / Open-Meteo) — for lineage tracking |

---

### 1.4 Retention Policy

A 90-day soft-delete retention policy was applied — suitable for the Trial environment while preserving enough history for ML training:

```kql
.alter table raw_electricity_prices policy retention
@'{"SoftDeletePeriod": "90.00:00:00", "Recoverability": "Disabled"}'
```

**Validation:** Retention policy confirmed via queryset result showing `RetentionPolicy` entity with `SoftDeletePeriod: 90.00:00:00`.

![Bronze Table Created](screenshots/phase1_bronze_table_created.png)

---

### 1.5 Phase 1 Summary

| Item | Status |
|---|---|
| Fabric workspace created | ✅ |
| Eventhouse provisioned | ✅ |
| KQL Database `pulsegrid_bronze` created | ✅ |
| Eventstream `pulsegrid_eventstream` created | ✅ |
| Lakehouse `pulsegrid_lakehouse` created | ✅ |
| `raw_electricity_prices` table created | ✅ |
| 90-day retention policy applied | ✅ |

---

## Phase 2 — Silver Layer (PySpark Cleansing)

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

## Appendix — Spark Optimization Techniques Applied

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

*Last updated: Phase 1 complete — August 2026*
