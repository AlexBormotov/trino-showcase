---
title: seed/synthea.py
tags:
  - code-map
  - seed
---

# `seed/synthea.py`

Section: [[Data-Generation]]

## Purpose

Runs Synthea 4.0 in an eclipse-temurin:17 container with fixed seeds and reference date; downloads and caches the jar; exports only the CSVs the seeder uses.

## Contents

- `main(population: int=6000)` -> `None` — Downloads the jar if missing and runs Synthea in Docker for the given population
