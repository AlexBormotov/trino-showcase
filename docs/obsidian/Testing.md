---
title: Testing
tags:
  - testing
  - ci
---

# Testing

Hub: [[INDEX]]

## Oracles

A check never repeats the logic it checks.

| Checked | Against |
|---|---|
| Source loads | manifest `tables` |
| Canonical model | manifest `expected` (clean truth before drift) |
| Archive orphans | manifest `injected`, exactly |
| Readmission flag | same rule written with EXISTS |
| MetricFlow metrics | manifest or independent SQL over canonical |
| Superset metrics | `mf query` per tenant |
| Security | queries per role, bypass attempts, audit log |
| Ossie round trip | msi-to-ossie back conversion |

Every stage had a negative control (break the rule, the expected tests fail, restore). Never loosen a reconciliation assertion to make it pass.

## Commands

`uv run pytest tests/unit` (no stack); `uv run pytest` (needs stack, seed, dbt build, poe semantic, poe superset). CI (`.github/workflows/ci.yml`) runs everything on every push with 300 patients, about 7 minutes.

## Code map

- [[github-workflows-ci]] — `.github/workflows/ci.yml`
- [[tests-dbt-patient_has_one_current_version]] — `tests/dbt/patient_has_one_current_version.sql`
- [[tests-dbt-patient_versions_do_not_overlap]] — `tests/dbt/patient_versions_do_not_overlap.sql`
- [[tests-dbt-readmission_flag_matches_self_join]] — `tests/dbt/readmission_flag_matches_self_join.sql`
- [[tests-integration-test_canonical]] — `tests/integration/test_canonical.py`
- [[tests-integration-test_federation]] — `tests/integration/test_federation.py`
- [[tests-integration-test_metrics]] — `tests/integration/test_metrics.py`
- [[tests-integration-test_security]] — `tests/integration/test_security.py`
- [[tests-integration-test_superset]] — `tests/integration/test_superset.py`
- [[tests-unit-test_build]] — `tests/unit/test_build.py`
- [[tests-unit-test_semantic]] — `tests/unit/test_semantic.py`
- [[tests-unit-test_superset_sync]] — `tests/unit/test_superset_sync.py`
