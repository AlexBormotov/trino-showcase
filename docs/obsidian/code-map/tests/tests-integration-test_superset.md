---
title: tests/integration/test_superset.py
tags:
  - code-map
  - tests
---

# `tests/integration/test_superset.py`

Section: [[Testing]]

## Purpose

Superset chart data API vs mf query per tenant, every chart returns data, tenant_a sees only clinic_a, audit shows queries as the viewer.

## Contents

- `login(user: str)` -> `Superset` — test helper
- `dataset_id(client: Superset, table: str)` -> `int` — test helper
- `chart_data(client: Superset, table: str, metrics: list[str], columns: list[str], comment: str='')` -> `list[dict]` — test helper
- `admin()` — test helper
- `test_encounter_metrics_match_metricflow(admin, tmp_path)` — checks that encounter metrics match metricflow
- `test_denial_rate_matches_metricflow(admin, tmp_path)` — checks that denial rate matches metricflow
- `test_every_dashboard_chart_returns_data(admin)` — checks that every dashboard chart returns data
- `test_tenant_analyst_sees_only_own_tenant_in_superset(admin)` — checks that tenant analyst sees only own tenant in superset
- `test_superset_queries_run_as_the_viewer()` — checks that superset queries run as the viewer
