---
title: models/marts/dim_patient.sql
tags:
  - code-map
  - dbt
---

# `models/marts/dim_patient.sql`

Section: [[Semantic-Layer]]

## Purpose

Current patient version: the patient dimension for metrics (gender, city, ZIP).

## Contents

- reads `ref('patient')` → [[models-canonical-patient]]
