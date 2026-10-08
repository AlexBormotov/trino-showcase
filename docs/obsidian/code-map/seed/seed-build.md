---
title: seed/build.py
tags:
  - code-map
  - seed
---

# `seed/build.py`

Section: [[Data-Generation]]

## Purpose

Pure pandas: cuts the Synthea export to the 5-year window, splits patients across tenants, reshapes each tenant into its dialect with injected drift, and builds the manifest (`expected` clean truth, `injected` drift, table counts).

## Contents

- class `Tenant` — Tables of one tenant plus what was injected into them
- `read_synthea(csv_dir: Path)` -> `dict[str, pd.DataFrame]` — Synthea CSVs, cut to the 5-year window, with typed columns.
- `tenant_of(patient_id: str)` -> `str` — Stable assignment of a patient to a tenant.
- `split(base: dict[str, pd.DataFrame])` -> `dict[str, dict[str, pd.DataFrame]]` — Partitions every Synthea frame by patient owner tenant
- `claim_status(claims: pd.DataFrame, rng: np.random.Generator)` -> `pd.Series` — Synthea closes every claim; inject denials and recent pending claims.
- `address_changes(pat: pd.DataFrame, first_seen: pd.Series, rng: np.random.Generator)` -> `pd.DataFrame` — One address move for a share of patients, at a random time after first contact.
- `clinic_a(src: dict[str, pd.DataFrame], rng: np.random.Generator)` -> `Tenant` — PostgreSQL. Schema app_v1 until 2023, app_v2 after; patients only in v2.
- `clinic_b(src: dict[str, pd.DataFrame], rng: np.random.Generator)` -> `Tenant` — MySQL. camelCase, soft-deleted duplicates, cents before mid-2023, local codes.
- `clinic_c(src: dict[str, pd.DataFrame], rng: np.random.Generator)` -> `Tenant` — Iceberg archive. Missing months of encounters; prefixed or missing codes.
- `build(csv_dir: Path, seed: int=42)` -> `tuple[dict[str, Tenant], dict]` — Entry point: builds all three tenants and the manifest
- `expected(src: dict[str, pd.DataFrame], tenant: Tenant)` -> `dict` — What the canonical model must show for a tenant, from the clean source.
- `_utc_naive(s: pd.Series)` -> `pd.Series` — Parses ISO timestamps to naive UTC
