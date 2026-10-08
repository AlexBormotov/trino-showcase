---
title: tests/dbt/patient_has_one_current_version.sql
tags:
  - code-map
  - tests
---

# `tests/dbt/patient_has_one_current_version.sql`

Section: [[Testing]]

## Purpose

dbt singular test: every patient_hk has exactly one current version.

## Contents

- reads `ref('patient')` → [[models-canonical-patient]]
