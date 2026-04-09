from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import cast

from investment_engine import default_scenario, project_scenario, validate_scenario
from investment_persist import load_persisted_scenarios, save_persisted_scenarios
from investment_reporting import build_growth_chart, compare_scenarios, format_single_projection
from schemas import InvestmentScenario

def prompt_with_default(prompt: str, default_value: str) -> str:
    entered = input(f"{prompt} [{default_value}]: ").strip()
    return entered if entered else default_value

def _parse_decimal_field(label: str, raw: str) -> Decimal | None:
    try:
        return Decimal(raw.strip())
    except (InvalidOperation, ValueError, TypeError):
        print(f"{label} must be a valid number (got {raw!r}).")
        return None

def _parse_years_field(label: str, raw: str) -> int | None:
    try:
        return int(raw, 10)
    except ValueError:
        print(f"{label} must be a whole number (got {raw!r}).")
        return None