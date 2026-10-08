---
title: tests/integration/test_metrics.py
tags:
  - code-map
  - tests
---

# `tests/integration/test_metrics.py`

Section: [[Testing]]

## Purpose

Each metric from `mf query` vs the manifest or independent SQL over the canonical model; join to patient; time grain.

## Contents

- `mf(tmp_path: Path, metrics: list[str], group_by: str)` -> `dict[str, dict[str, float]]` — Run `mf query` and return {group value: {metric: value}}.
- `sql()` — test helper
- `by_tenant(tmp_path_factory)` — test helper
- `test_encounter_count_matches_manifest(by_tenant)` — checks that encounter count matches manifest
- `test_claim_denial_rate_matches_manifest(tmp_path)` — checks that claim denial rate matches manifest
- `test_active_patients(by_tenant, sql)` — checks that active patients
- `test_avg_length_of_stay(by_tenant, sql)` — checks that avg length of stay
- `test_readmission_rate(by_tenant, sql)` — checks that readmission rate
- `test_join_to_patient_dimension(tmp_path, sql)` — checks that join to patient dimension
- `test_time_grain_adds_up(tmp_path)` — checks that time grain adds up
