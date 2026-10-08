---
title: models/marts/fct_claim.sql
tags:
  - code-map
  - dbt
---

# `models/marts/fct_claim.sql`

Section: [[Semantic-Layer]]

## Purpose

Claim facts for metrics: denied_claim and adjudicated_claim (pending excluded).

## Contents

- reads `ref('claim')` → [[models-canonical-claim]]
