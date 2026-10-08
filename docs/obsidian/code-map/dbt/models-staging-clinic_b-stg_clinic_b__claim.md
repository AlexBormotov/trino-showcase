---
title: models/staging/clinic_b/stg_clinic_b__claim.sql
tags:
  - code-map
  - dbt
---

# `models/staging/clinic_b/stg_clinic_b__claim.sql`

Section: [[dbt-Models]]

## Purpose

Staging view for clinic_b (MySQL): renames source columns to canonical names, fixes types and applies transform macros. Column order must match the other staging views of the same entity.

## Contents

- reads source `clinic_b.claim`
