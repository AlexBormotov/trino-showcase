---
title: semantic/compile.py
tags:
  - code-map
  - semantic
---

# `semantic/compile.py`

Section: [[Semantic-Layer]]

## Purpose

Converts the Ossie model to target/semantic_manifest.json with apache-ossie-dbt and fills two converter gaps: time spine from dbt parse and agg_time_dimension from DBT extensions.

## Contents

- `main()` -> `int` — Converts Ossie, merges the time spine and agg_time_dimension, writes the manifest
