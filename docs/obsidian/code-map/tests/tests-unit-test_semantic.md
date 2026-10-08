---
title: tests/unit/test_semantic.py
tags:
  - code-map
  - tests
---

# `tests/unit/test_semantic.py`

Section: [[Testing]]

## Purpose

Ossie -> MetricFlow -> Ossie round trip: forward has no issues, expressions survive except COUNT(encounter.*), known losses reported.

## Contents

- `expressions(doc: dict)` -> `dict[str, str]` — test helper
- `round_trip()` — test helper
- `test_forward_conversion_has_no_issues(round_trip)` — checks that forward conversion has no issues
- `test_metric_expressions_survive_except_row_counts(round_trip)` — checks that metric expressions survive except row counts
- `test_known_losses_are_reported(round_trip)` — checks that known losses are reported
