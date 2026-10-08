---
title: tests/unit/test_superset_sync.py
tags:
  - code-map
  - tests
---

# `tests/unit/test_superset_sync.py`

Section: [[Testing]]

## Purpose

Unit tests of the Ossie -> Superset translation and dashboard layout.

## Contents

- `test_translate_metric(ossie, dataset, sql)` — checks that translate metric
- `test_cross_dataset_metric_is_rejected()` — checks that cross dataset metric is rejected
- `test_every_ossie_metric_lands_on_its_dataset()` — checks that every ossie metric lands on its dataset
- `test_layout_wraps_rows_at_twelve()` — checks that layout wraps rows at twelve
