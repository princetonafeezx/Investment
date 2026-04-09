# Schema package

This folder centralizes schema-related artifacts for **LL Investment**.

## Contents

- `scenario_types.py` — Python `TypedDict` and `Literal` definitions for scenario input
- `projection_types.py` — Python `TypedDict` definitions for yearly rows and projection output
- `json/investment_scenario.schema.json` — JSON Schema for a single scenario object
- `json/projection_result.schema.json` — JSON Schema for the projection result structure
- `json/persisted_scenarios_v2.schema.json` — JSON Schema for the on-disk v2 JSON file

## Why this folder exists

The repository already had a flat `schemas.py` module. This folder turns schema definitions into a first-class part of the project while keeping `schemas.py` as a backward-compatible import shim.
