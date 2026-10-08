---
title: Data Generation
tags:
  - data
  - seed
---

# Data Generation

Hub: [[INDEX]]

## Flow

Synthea (container, fixed seed, reference date 2026-10-01) → `data/synthea/csv` → `seed/build.py` (window 2021-10..2026-10, tenant split by md5 of patient id, drift injection) → `data/manifest.json` → `seed/load.py` → PostgreSQL / MySQL / Iceberg.

## Tenants and injected drift

| Tenant | Store | Drift |
|---|---|---|
| clinic_a | PostgreSQL | `app_v1` until 2024 (DD.MM.YYYY strings, renamed columns, gender 1/2), `app_v2` after; address history as CDC log |
| clinic_b | MySQL | camelCase, soft-deleted duplicates, cents until 2023-07-01 in the same column, local diagnosis codes + dictionary, no history |
| clinic_c | Iceberg | month partitions, 3 months missing (orphan claims and diagnoses remain), `SNOMED:` prefixes, 5% text-only diagnoses |

Claim statuses differ per tenant; about 8% denials injected (Synthea closes every claim).

## Manifest

`data/manifest.json` is the oracle for [[Testing]]: `tables` (loaded row counts), `expected` (clean truth per tenant, computed before drift), `injected` (what drift was added). Any change to injection must update the manifest in the same change.

## Code map

- [[infra-tenants-clinic_a]] — `infra/tenants/clinic_a.sql`
- [[infra-tenants-clinic_b]] — `infra/tenants/clinic_b.sql`
- [[seed-__main__]] — `seed/__main__.py`
- [[seed-build]] — `seed/build.py`
- [[seed-load]] — `seed/load.py`
- [[seed-synthea]] — `seed/synthea.py`
