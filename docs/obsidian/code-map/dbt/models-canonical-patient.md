---
title: models/canonical/patient.sql
tags:
  - code-map
  - dbt
---

# `models/canonical/patient.sql`

Section: [[dbt-Models]]

## Purpose

Canonical patient with SCD2 on address: clinic_a versions replayed from the CDC log with lead() over lsn; snapshot tenants get one open version; patient_hk durable, patient_version_hk per version.

## Contents

- reads `ref('stg_clinic_a__v2_patient_cdc')` → [[models-staging-clinic_a-stg_clinic_a__v2_patient_cdc]]
- reads `ref('stg_clinic_a__v2_patients')` → [[models-staging-clinic_a-stg_clinic_a__v2_patients]]
- reads `ref('stg_clinic_b__patient')` → [[models-staging-clinic_b-stg_clinic_b__patient]]
- reads `ref('stg_clinic_c__patients')` → [[models-staging-clinic_c-stg_clinic_c__patients]]
