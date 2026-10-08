---
title: models/staging/clinic_c/stg_clinic_c__conditions.sql
tags:
  - code-map
  - dbt
---

# `models/staging/clinic_c/stg_clinic_c__conditions.sql`

Section: [[dbt-Models]]

## Purpose

Staging view for clinic_c (Iceberg archive): renames source columns to canonical names, fixes types and applies transform macros. Column order must match the other staging views of the same entity.

## Contents

- reads source `clinic_c.conditions`
