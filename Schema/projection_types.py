"""Projection output types for the compound-interest projector."""

from __future__ import annotations

from decimal import Decimal
from typing import TypedDict

from .scenario_types import InvestmentScenario


class ProjectionYearRow(TypedDict):
    """One year of output from the projection engine."""

    year: int
    starting_balance: Decimal
    contributions: Decimal
    interest_earned: Decimal
    ending_balance: Decimal
    real_balance: Decimal
    principal_portion: Decimal
    interest_portion: Decimal


class ProjectionResult(TypedDict):
    """Return value produced by the projection engine."""

    scenario: InvestmentScenario
    rows: list[ProjectionYearRow]
    ending_balance: Decimal
    total_contributed: Decimal
    total_earned: Decimal
    real_ending_balance: Decimal
    purchasing_power_loss: Decimal
    warning: str
