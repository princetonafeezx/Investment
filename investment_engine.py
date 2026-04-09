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
