---
title: models/staging/clinic_a/stg_clinic_a__v1_dx.sql
tags:
  - code-map
  - dbt
---

# `models/staging/clinic_a/stg_clinic_a__v1_dx.sql`

Section: [[dbt-Models]]

## Purpose

Staging view for clinic_a (PostgreSQL): renames source columns to canonical names, fixes types and applies transform macros. Column order must match the other staging views of the same entity.

## Contents

- reads source `clinic_a_v1.dx`
