---
title: Semantic Layer
tags:
  - semantic
  - metrics
---

# Semantic Layer

Hub: [[INDEX]]

**Stack:** Apache Ossie 0.2.0.dev0 + apache-ossie-dbt (pinned commit, direct git refs), dbt-metricflow 0.15.0.

## Architecture

- `semantic/clinic_analytics.yaml` is the only place metrics are defined: `encounter_count`, `active_patients`, `avg_length_of_stay_days`, `readmission_rate_30d`, `claim_denial_rate`. Catalog: `docs/metrics.md`.
- `uv run poe semantic` = `dbt parse` + `semantic/compile.py` → `target/semantic_manifest.json` → `mf query` on Trino. `dbt parse` alone overwrites the manifest without metrics.
- Converter gaps filled in `compile.py` or the YAML: no time spine; no agg_time_dimension (DBT custom extension); DateTime not a time dimension by default (`is_time: true`); entity named after the key field. See [[Decisions]] (ADR 0003).
- Row-level logic across rows (30-day readmission) lives in marts; Ossie only aggregates.
- The same YAML feeds [[BI]].

## Code map

- [[models-marts-dim_patient]] — `models/marts/dim_patient.sql`
- [[models-marts-fct_claim]] — `models/marts/fct_claim.sql`
- [[models-marts-fct_encounter]] — `models/marts/fct_encounter.sql`
- [[models-semantic-_time_spine]] — `models/semantic/_time_spine.yml`
- [[models-semantic-metricflow_time_spine]] — `models/semantic/metricflow_time_spine.sql`
- [[semantic-clinic_analytics]] — `semantic/clinic_analytics.yaml`
- [[semantic-compile]] — `semantic/compile.py`
