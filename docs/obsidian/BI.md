---
title: BI
tags:
  - bi
  - superset
---

# BI

Hub: [[INDEX]]

## Architecture

- Superset 6.1.0 at http://localhost:18088 (admin/admin; analysts use their name as password).
- `uv run poe superset` publishes the Ossie model: Trino database with `impersonate_user`, datasets, metrics translated by sqlglot (qualifiers dropped, ratios `CAST(.. AS DOUBLE) / NULLIF(.., 0)`, cross-dataset metrics rejected, d3format from SUPERSET extensions), six charts, dashboard "Clinic analytics". Idempotent.
- Authorization stays in Trino: the viewer's identity reaches Trino, so [[Security]] rules apply in dashboards.
- Superset datasets are single tables: relationship-based group-bys exist only in MetricFlow. See [[Decisions]] (ADR 0005).

## Code map

- [[infra-superset-Dockerfile]] — `infra/superset/Dockerfile`
- [[infra-superset-bootstrap]] — `infra/superset/bootstrap.sh`
- [[infra-superset-superset_config]] — `infra/superset/superset_config.py`
- [[semantic-superset_sync]] — `semantic/superset_sync.py`
