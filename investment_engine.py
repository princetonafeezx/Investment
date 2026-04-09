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
