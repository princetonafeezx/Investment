from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from typing import Any, cast

from schemas import InvestmentScenario, ProjectionResult, ProjectionYearRow

VALID_COMPOUNDING = {"monthly", "annual"}
VALID_CONTRIBUTION_FREQUENCIES = {"monthly", "annual"}
VALID_CONTRIBUTION_TIMING = {"start", "end"}

_ZERO = Decimal(0)
_ONE = Decimal(1)
_PERCENT = Decimal(100)

def _coerce_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise ValueError("boolean is not a numeric amount")
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, str):
        return Decimal(value.strip())
    raise ValueError("unsupported type for Decimal")

def validate_scenario(scenario: Mapping[str, Any]) -> list[str]:
    errors = []

    if not scenario.get("name"):
        errors.append("Scenario name cannot be blank.")

    try:
        if _coerce_decimal(scenario.get("initial_principal", 0)) < 0:
            errors.append("Initial principal cannot be negative.")
    except (InvalidOperation, TypeError, ValueError):
        errors.append("Initial principal has to be numeric.")

    try:
        rate = _coerce_decimal(scenario.get("annual_rate", 0))
        if rate < 0:
            errors.append("Interest rate cannot be negative.")
    except (InvalidOperation, TypeError, ValueError):
        errors.append("Interest rate has to be numeric.")

    try:
        if int(scenario.get("years", 0)) <= 0:
            errors.append("Years must be greater than zero.")
    except (TypeError, ValueError):
        errors.append("Years must be a whole number.")

    try:
        if _coerce_decimal(scenario.get("contribution_amount", 0)) < 0:
            errors.append("Contribution amount cannot be negative.")
    except (InvalidOperation, TypeError, ValueError):
        errors.append("Contribution amount has to be numeric.")

    try:
        if _coerce_decimal(scenario.get("inflation_rate", 0)) < 0:
            errors.append("Inflation rate cannot be negative.")
    except (InvalidOperation, TypeError, ValueError):
        errors.append("Inflation rate has to be numeric.")

    if scenario.get("compounding") not in VALID_COMPOUNDING:
        errors.append("Compounding must be monthly or annual.")

    if scenario.get("contribution_frequency") not in VALID_CONTRIBUTION_FREQUENCIES:
        errors.append("Contribution frequency must be monthly or annual.")

    if scenario.get("contribution_timing") not in VALID_CONTRIBUTION_TIMING:
        errors.append("Contribution timing must be start or end.")

    return errors

def default_scenario(name: str = "Starter") -> InvestmentScenario:
    return cast(
        InvestmentScenario,
        {
            "name": name,
            "initial_principal": Decimal("10000"),
            "annual_rate": Decimal("7"),
            "years": 20,
            "compounding": "monthly",
            "contribution_amount": Decimal("200"),
            "contribution_frequency": "monthly",
            "contribution_timing": "end",
            "inflation_rate": Decimal("2.5"),
        },
    )

def scenario_from_storage(storage_key: str, data: Mapping[str, Any]) -> InvestmentScenario | None:
    try:
        base = default_scenario(name=str(data.get("name", storage_key)))
        merged: dict[str, Any] = dict(base)
        for k in base:
            if k in data:
                merged[k] = data[k]
        merged["name"] = str(data.get("name", storage_key)).strip() or str(storage_key)
        merged["initial_principal"] = _coerce_decimal(merged["initial_principal"])
        merged["annual_rate"] = _coerce_decimal(merged["annual_rate"])
        merged["years"] = int(merged["years"])
        merged["contribution_amount"] = _coerce_decimal(merged["contribution_amount"])
        merged["inflation_rate"] = _coerce_decimal(merged["inflation_rate"])
        merged["compounding"] = str(merged["compounding"]).strip().lower()
        merged["contribution_frequency"] = str(merged["contribution_frequency"]).strip().lower()
        merged["contribution_timing"] = str(merged["contribution_timing"]).strip().lower()
    except (InvalidOperation, TypeError, ValueError):
        return None
    errors = validate_scenario(merged)
    if errors:
        return None
    return cast(InvestmentScenario, merged)

def contribution_for_period(
    scenario: Mapping[str, Any], period_index: int, periods_per_year: int
) -> Decimal:
    frequency = scenario["contribution_frequency"]
    amount = _coerce_decimal(scenario["contribution_amount"])
    if frequency == "monthly":
        if periods_per_year == 12:
            return amount
        return amount * Decimal(12)
    if frequency == "annual":
        if periods_per_year == 12:
            return amount if period_index == 1 else _ZERO
        return amount
    return _ZERO

def project_scenario(scenario: Mapping[str, Any]) -> ProjectionResult:
    errors = validate_scenario(scenario)
    if errors:
        raise ValueError(" | ".join(errors))

    years = int(scenario["years"])
    balance = _coerce_decimal(scenario["initial_principal"])
    annual_rate = _coerce_decimal(scenario["annual_rate"]) / _PERCENT
    inflation_rate = _coerce_decimal(scenario["inflation_rate"]) / _PERCENT
    periods_per_year = 12 if scenario["compounding"] == "monthly" else 1
    contribution_timing = scenario["contribution_timing"]
    periods_dec = Decimal(periods_per_year)

    rows: list[ProjectionYearRow] = []
    running_contributions = _ZERO
    total_interest = _ZERO
    initial_principal = _coerce_decimal(scenario["initial_principal"])
    annual_rate_pct = _coerce_decimal(scenario["annual_rate"])

    for year_number in range(1, years + 1):
        year_start_balance = balance
        year_contributions = _ZERO
        year_interest = _ZERO

        for period_index in range(1, periods_per_year + 1):
            contribution = contribution_for_period(scenario, period_index, periods_per_year)
            if contribution_timing == "start":
                balance += contribution
                year_contributions += contribution

            period_rate = annual_rate / periods_dec
            interest = balance * period_rate
            balance += interest
            year_interest += interest

            if contribution_timing == "end":
                balance += contribution
                year_contributions += contribution

        running_contributions += year_contributions
        total_interest += year_interest

        inflation_factor = (_ONE + inflation_rate) ** year_number if inflation_rate > 0 else _ONE
        real_balance = balance / inflation_factor
        principal_so_far = initial_principal + running_contributions

        rows.append(
            cast(
                ProjectionYearRow,
                {
                    "year": year_number,
                    "starting_balance": year_start_balance,
                    "contributions": year_contributions,
                    "interest_earned": year_interest,
                    "ending_balance": balance,
                    "real_balance": real_balance,
                    "principal_portion": principal_so_far,
                    "interest_portion": max(_ZERO, balance - principal_so_far),
                },
            )
        )

    return cast(
        ProjectionResult,
        {
            "scenario": cast(InvestmentScenario, dict(scenario)),
            "rows": rows,
            "ending_balance": balance,
            "total_contributed": initial_principal + running_contributions,
            "total_earned": total_interest,
            "real_ending_balance": rows[-1]["real_balance"] if rows else balance,
            "purchasing_power_loss": balance - (rows[-1]["real_balance"] if rows else balance),
            "warning": (
                "High rate warning: annual rate is above 25%."
                if annual_rate_pct > Decimal("25")
                else ""
            ),
        },
    )
