---
title: tests/integration/test_federation.py
tags:
  - code-map
  - tests
---

# `tests/integration/test_federation.py`

Section: [[Testing]]

## Purpose

Trino counts vs manifest tables, federated union, pushdown to PostgreSQL and MySQL, Iceberg month partitions with gaps.

## Contents

- `query()` — test helper
- `test_row_counts_match_manifest(query, tenant, table)` — checks that row counts match manifest
- `test_federated_patient_count(query)` — checks that federated patient count
- `test_filter_and_aggregate_push_down_to_relational_sources(query, sql, remote)` — checks that filter and aggregate push down to relational sources
- `test_archive_encounters_are_partitioned_by_month_with_gaps(query)` — checks that archive encounters are partitioned by month with gaps
