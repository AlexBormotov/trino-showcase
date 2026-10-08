---
title: models/canonical/diagnosis.sql
tags:
  - code-map
  - dbt
---

# `models/canonical/diagnosis.sql`

Section: [[dbt-Models]]

## Purpose

Canonical diagnosis: UNION ALL of diagnosis staging views; diagnosis_hk hashes the description because some archive rows have no code; is_coded flag.

## Contents

- reads `ref('stg_clinic_a__v1_dx')` → [[models-staging-clinic_a-stg_clinic_a__v1_dx]]
- reads `ref('stg_clinic_a__v2_diagnoses')` → [[models-staging-clinic_a-stg_clinic_a__v2_diagnoses]]
- reads `ref('stg_clinic_b__visit_diagnosis')` → [[models-staging-clinic_b-stg_clinic_b__visit_diagnosis]]
- reads `ref('stg_clinic_c__conditions')` → [[models-staging-clinic_c-stg_clinic_c__conditions]]
