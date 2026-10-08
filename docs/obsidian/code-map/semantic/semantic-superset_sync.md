---
title: semantic/superset_sync.py
tags:
  - code-map
  - semantic
---

# `semantic/superset_sync.py`

Section: [[BI]]

## Purpose

Publishes the Ossie model to Superset through its REST API: Trino database with impersonation, datasets, metrics translated with sqlglot, six charts and the dashboard. Idempotent.

## Contents

- `translate_metric(expression: str)` -> `tuple[str, str]` — Ossie metric expression -> (dataset name, Trino SQL over that dataset's table).
- `extension(obj: dict, vendor: str)` -> `dict` — Parsed data of an object's custom extension for a vendor
- `datasets_from_ossie(model: dict)` -> `dict[str, dict]` — {dataset name: {schema, table, time_columns, main_dttm_col, metrics: [...]}}.
- `layout(charts: list[tuple[int, str, int]])` -> `dict` — Dashboard v2 layout: charts fill rows of width 12 in the given order.
- class `Superset` — Minimal Superset REST client with JWT and CSRF
  - `__init__(self, url: str, username: str, password: str)` — Logs in and fetches a CSRF token
  - `call(self, method: str, path: str, **kw)` — Any API request; raises on non-2xx
  - `get(self, path: str)` — GET helper
  - `find(self, resource: str, field: str, value: str)` — First object of a resource whose field equals the value
- `sync(client: Superset)` -> `dict` — Upserts database, datasets with metrics, charts and the dashboard layout
- `main()` -> `int` — Runs sync as admin and prints the object ids
