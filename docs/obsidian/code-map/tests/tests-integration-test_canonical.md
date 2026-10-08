---
title: tests/integration/test_canonical.py
tags:
  - code-map
  - tests
---

# `tests/integration/test_canonical.py`

Section: [[Testing]]

## Purpose

Canonical model vs manifest `expected` per tenant (counts, sums, statuses, gender, coding), SCD2 versions, orphans vs `injected`, union pruning by tenant_id.

## Contents

- `by_tenant()` — test helper
- `close(a, b)` -> `bool` — test helper
- `test_patients(by_tenant)` — checks that patients
- `test_gender_is_harmonized(by_tenant)` — checks that gender is harmonized
- `test_scd2_versions_come_from_the_change_log_only(by_tenant)` — checks that scd2 versions come from the change log only
- `test_encounters_and_cost(by_tenant)` — checks that encounters and cost
- `test_diagnoses_and_coding(by_tenant)` — checks that diagnoses and coding
- `test_claims_amount_and_status(by_tenant)` — checks that claims amount and status
- `test_archive_gap_is_visible_as_orphans(by_tenant)` — checks that archive gap is visible as orphans
- `test_tenant_filter_prunes_the_union_to_one_source()` — checks that tenant filter prunes the union to one source
