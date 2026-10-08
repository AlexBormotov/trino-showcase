---
title: models/marts/fct_encounter.sql
tags:
  - code-map
  - dbt
---

# `models/marts/fct_encounter.sql`

Section: [[Semantic-Layer]]

## Purpose

Encounter facts for metrics: inpatient_stay, length_of_stay_days, readmitted_30d (first inpatient admission after discharge within 30 days; not lead(), because stays overlap).

## Contents

- reads `ref('encounter')` → [[models-canonical-encounter]]
