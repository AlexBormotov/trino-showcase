---
title: seed/load.py
tags:
  - code-map
  - seed
---

# `seed/load.py`

Section: [[Data-Generation]]

## Purpose

Loads tenant tables: PostgreSQL via COPY, MySQL via batched inserts, Iceberg via PyIceberg straight to Polaris (month partitioning for encounters). Drops and recreates every time.

## Contents

- `records(df: pd.DataFrame)` -> `list[tuple]` — Rows as tuples of plain Python values, with NaN/NaT as None.
- `load_clinic_a(tables: dict[str, pd.DataFrame])` -> `None` — Runs clinic_a DDL and COPYs every table into PostgreSQL
- `load_clinic_b(tables: dict[str, pd.DataFrame])` -> `None` — Runs clinic_b DDL and inserts every table into MySQL in batches
- `load_clinic_c(tables: dict[str, pd.DataFrame])` -> `None` — Recreates clinic_c tables in Polaris and appends Arrow data; encounters partitioned by month
