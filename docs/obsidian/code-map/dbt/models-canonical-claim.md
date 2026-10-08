---
title: models/canonical/claim.sql
tags:
  - code-map
  - dbt
---

# `models/canonical/claim.sql`

Section: [[dbt-Models]]

## Purpose

Canonical claim: UNION ALL of claim staging views plus claim_hk, encounter_hk, patient_hk.

## Contents

- reads `ref('stg_clinic_a__v1_bill')` → [[models-staging-clinic_a-stg_clinic_a__v1_bill]]
- reads `ref('stg_clinic_a__v2_claims')` → [[models-staging-clinic_a-stg_clinic_a__v2_claims]]
- reads `ref('stg_clinic_b__claim')` → [[models-staging-clinic_b-stg_clinic_b__claim]]
- reads `ref('stg_clinic_c__claims')` → [[models-staging-clinic_c-stg_clinic_c__claims]]
