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

def create_or_edit_scenario(
    existing: InvestmentScenario | None = None,
) -> InvestmentScenario | None:
    base = dict(existing) if existing is not None else default_scenario()
    name = prompt_with_default("Scenario name", str(base["name"]))
    principal_raw = prompt_with_default("Initial principal", str(base["initial_principal"]))
    rate_raw = prompt_with_default("Annual interest rate (%)", str(base["annual_rate"]))
    years_raw = prompt_with_default("Years", str(base["years"]))
    compounding = prompt_with_default("Compounding (monthly/annual)", str(base["compounding"]))
    contribution_raw = prompt_with_default("Contribution amount", str(base["contribution_amount"]))
    contribution_frequency = prompt_with_default(
        "Contribution frequency (monthly/annual)", str(base["contribution_frequency"])
    )
    contribution_timing = prompt_with_default(
        "Contribution timing (start/end)",
        str(base["contribution_timing"]),
    )
    inflation_raw = prompt_with_default("Inflation rate (%)", str(base["inflation_rate"]))

    principal = _parse_decimal_field("Initial principal", principal_raw)
    rate = _parse_decimal_field("Annual interest rate (%)", rate_raw)
    years = _parse_years_field("Years", years_raw)
    contribution = _parse_decimal_field("Contribution amount", contribution_raw)
    inflation = _parse_decimal_field("Inflation rate (%)", inflation_raw)
    if (
        principal is None
        or rate is None
        or years is None
        or contribution is None
        or inflation is None
    ):
        return None

    candidate = cast(
        InvestmentScenario,
        {
            "name": name,
            "initial_principal": principal,
            "annual_rate": rate,
            "years": years,
            "compounding": compounding.strip().lower(),
            "contribution_amount": contribution,
            "contribution_frequency": contribution_frequency.strip().lower(),
            "contribution_timing": contribution_timing.strip().lower(),
            "inflation_rate": inflation,
        },
    )

    errors = validate_scenario(candidate)
    if errors:
        print("Scenario had validation issues:")
        for error in errors:
            print(f"- {error}")
        return None
    return candidate
