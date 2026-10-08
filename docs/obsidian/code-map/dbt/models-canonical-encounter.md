---
title: models/canonical/encounter.sql
tags:
  - code-map
  - dbt
---

# `models/canonical/encounter.sql`

Section: [[dbt-Models]]

## Purpose

Canonical encounter: UNION ALL of encounter staging views plus encounter_hk and patient_hk.

## Contents

- reads `ref('stg_clinic_a__v1_visit')` → [[models-staging-clinic_a-stg_clinic_a__v1_visit]]
- reads `ref('stg_clinic_a__v2_encounters')` → [[models-staging-clinic_a-stg_clinic_a__v2_encounters]]
- reads `ref('stg_clinic_b__visit')` → [[models-staging-clinic_b-stg_clinic_b__visit]]
- reads `ref('stg_clinic_c__encounters')` → [[models-staging-clinic_c-stg_clinic_c__encounters]]
