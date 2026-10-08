---
title: tests/dbt/patient_versions_do_not_overlap.sql
tags:
  - code-map
  - tests
---

# `tests/dbt/patient_versions_do_not_overlap.sql`

Section: [[Testing]]

## Purpose

dbt singular test: SCD2 versions are contiguous and never overlap.

## Contents

- reads `ref('patient')` → [[models-canonical-patient]]
