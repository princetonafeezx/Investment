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
