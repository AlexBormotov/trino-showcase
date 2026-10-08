---
title: dbt Models
tags:
  - dbt
  - modeling
---

# dbt Models

Hub: [[INDEX]]

**Stack:** dbt-core 1.12.5, dbt-trino 1.10.6. Every model is a view stored in Polaris as an Iceberg view (`iceberg.staging|canonical|marts|semantic`).

## Architecture

- **staging/**: one view per source table and schema version; canonical names, types, transform macros. Tenant-specific logic only here. Column order must match across the staging views of an entity (canonical uses `select *` in UNION ALL).
- **canonical/**: `patient` (SCD2), `encounter`, `diagnosis`, `claim`; hash keys `<entity>_hk` (Data Vault style); every row has `tenant_id`, `source_system`, `source_schema_version`.
- **marts/**: row-level flags for [[Semantic-Layer]] metrics.
- Federation first, materialize by exception: a `tenant_id` filter prunes the union to one source; the cents `CASE` blocks aggregate pushdown (first materialization candidate). See [[Decisions]] (ADR 0002).
- Iceberg views reject `char(n)`: staging casts to varchar.

## Code map

- [[dbt_project]] — `dbt_project.yml`
- [[macros-generate_schema_name]] — `macros/generate_schema_name.sql`
- [[macros-transforms]] — `macros/transforms.sql`
- [[models-canonical-_canonical]] — `models/canonical/_canonical.yml`
- [[models-canonical-claim]] — `models/canonical/claim.sql`
- [[models-canonical-diagnosis]] — `models/canonical/diagnosis.sql`
- [[models-canonical-encounter]] — `models/canonical/encounter.sql`
- [[models-canonical-patient]] — `models/canonical/patient.sql`
- [[models-marts-_marts]] — `models/marts/_marts.yml`
- [[models-staging-_sources]] — `models/staging/_sources.yml`
- [[models-staging-clinic_a-stg_clinic_a__v1_bill]] — `models/staging/clinic_a/stg_clinic_a__v1_bill.sql`
- [[models-staging-clinic_a-stg_clinic_a__v1_dx]] — `models/staging/clinic_a/stg_clinic_a__v1_dx.sql`
- [[models-staging-clinic_a-stg_clinic_a__v1_visit]] — `models/staging/clinic_a/stg_clinic_a__v1_visit.sql`
- [[models-staging-clinic_a-stg_clinic_a__v2_claims]] — `models/staging/clinic_a/stg_clinic_a__v2_claims.sql`
- [[models-staging-clinic_a-stg_clinic_a__v2_diagnoses]] — `models/staging/clinic_a/stg_clinic_a__v2_diagnoses.sql`
- [[models-staging-clinic_a-stg_clinic_a__v2_encounters]] — `models/staging/clinic_a/stg_clinic_a__v2_encounters.sql`
- [[models-staging-clinic_a-stg_clinic_a__v2_patient_cdc]] — `models/staging/clinic_a/stg_clinic_a__v2_patient_cdc.sql`
- [[models-staging-clinic_a-stg_clinic_a__v2_patients]] — `models/staging/clinic_a/stg_clinic_a__v2_patients.sql`
- [[models-staging-clinic_b-stg_clinic_b__claim]] — `models/staging/clinic_b/stg_clinic_b__claim.sql`
- [[models-staging-clinic_b-stg_clinic_b__patient]] — `models/staging/clinic_b/stg_clinic_b__patient.sql`
- [[models-staging-clinic_b-stg_clinic_b__visit]] — `models/staging/clinic_b/stg_clinic_b__visit.sql`
- [[models-staging-clinic_b-stg_clinic_b__visit_diagnosis]] — `models/staging/clinic_b/stg_clinic_b__visit_diagnosis.sql`
- [[models-staging-clinic_c-stg_clinic_c__claims]] — `models/staging/clinic_c/stg_clinic_c__claims.sql`
- [[models-staging-clinic_c-stg_clinic_c__conditions]] — `models/staging/clinic_c/stg_clinic_c__conditions.sql`
- [[models-staging-clinic_c-stg_clinic_c__encounters]] — `models/staging/clinic_c/stg_clinic_c__encounters.sql`
- [[models-staging-clinic_c-stg_clinic_c__patients]] — `models/staging/clinic_c/stg_clinic_c__patients.sql`
- [[profiles]] — `profiles.yml`
