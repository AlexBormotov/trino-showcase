---
title: macros/generate_schema_name.sql
tags:
  - code-map
  - dbt
---

# `macros/generate_schema_name.sql`

Section: [[dbt-Models]]

## Purpose

Uses the configured schema name as is (staging, canonical, marts, semantic) without the target prefix.

## Contents

- macro `generate_schema_name(custom_schema_name, node)` — Custom schema name as is, else target schema
