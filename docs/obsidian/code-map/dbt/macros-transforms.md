---
title: macros/transforms.sql
tags:
  - code-map
  - dbt
---

# `macros/transforms.sql`

Section: [[dbt-Models]]

## Purpose

Harmonization macros reused by staging models across tenants and schema versions.

## Contents

- macro `parse_dmy_ts(col)` — 'DD.MM.YYYY HH:MM:SS' string to timestamp
- macro `parse_dmy_date(col)` — 'DD.MM.YYYY' string to date
- macro `gender_code(col)` — M/F, 1/2, male/female to M/F; anything else U
- macro `cents_to_amount(amount, at, switched_on)` — Divides by 100 before the switch date; decimal(14,2)
- macro `strip_code_prefix(col)` — 'SNOMED:123' to '123'; NULL stays NULL
- macro `hash_key(cols)` — md5 hex of the parts joined with '|', NULLs as ''
