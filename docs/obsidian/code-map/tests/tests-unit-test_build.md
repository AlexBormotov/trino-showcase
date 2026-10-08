---
title: tests/unit/test_build.py
tags:
  - code-map
  - tests
---

# `tests/unit/test_build.py`

Section: [[Testing]]

## Purpose

Unit tests of seed/build.py on a tiny fixture: tenant assignment, schema version split, gender codes, CDC replay, cents, soft deletes, code dictionary, missing months, expected block.

## Contents

- `src()` -> `dict[str, pd.DataFrame]` — A small source in the shape read_synthea() returns.
- `rng()` -> `np.random.Generator` — test helper
- `test_tenant_assignment_is_stable_and_uses_every_tenant()` — checks that tenant assignment is stable and uses every tenant
- `test_claim_status_marks_recent_claims_pending(src)` — checks that claim status marks recent claims pending
- `test_clinic_a_splits_by_schema_version(src)` — checks that clinic a splits by schema version
- `test_clinic_a_legacy_gender_codes_only_for_patients_registered_before_v2(src)` — checks that clinic a legacy gender codes only for patients registered before v2
- `test_clinic_a_change_log_replays_to_current_address(src, monkeypatch)` — checks that clinic a change log replays to current address
- `test_clinic_b_money_is_in_cents_before_mid_2023(src)` — checks that clinic b money is in cents before mid 2023
- `test_clinic_b_soft_deleted_duplicates_and_code_dictionary(src, monkeypatch)` — checks that clinic b soft deleted duplicates and code dictionary
- `test_clinic_c_drops_missing_months_but_keeps_their_claims(src)` — checks that clinic c drops missing months but keeps their claims
- `test_clinic_c_codes_are_prefixed_or_missing(src, monkeypatch)` — checks that clinic c codes are prefixed or missing
- `test_expected_comes_from_the_clean_source(src)` — checks that expected comes from the clean source
