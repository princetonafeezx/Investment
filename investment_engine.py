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


