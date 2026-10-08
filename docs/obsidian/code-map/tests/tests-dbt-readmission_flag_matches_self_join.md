---
title: tests/dbt/readmission_flag_matches_self_join.sql
tags:
  - code-map
  - tests
---

# `tests/dbt/readmission_flag_matches_self_join.sql`

Section: [[Testing]]

## Purpose

dbt singular test: readmitted_30d equals the same rule written with EXISTS.

## Contents

- reads `ref('encounter')` → [[models-canonical-encounter]]
- reads `ref('fct_encounter')` → [[models-marts-fct_encounter]]
