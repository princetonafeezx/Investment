"""Typed shapes for the compound-interest projector (stdlib only)."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal, TypedDict

CompoundingLiteral = Literal["monthly", "annual"]
ContributionFrequencyLiteral = Literal["monthly", "annual"]
ContributionTimingLiteral = Literal["start", "end"]


class InvestmentScenario(TypedDict):
    """Fields expected by :func:`investment.project_scenario`."""

    name: str
    initial_principal: Decimal
    annual_rate: Decimal
    years: int
    compounding: CompoundingLiteral
    contribution_amount: Decimal
    contribution_frequency: ContributionFrequencyLiteral
    contribution_timing: ContributionTimingLiteral
    inflation_rate: Decimal


class ProjectionYearRow(TypedDict):
    """One year of output from :func:`investment.project_scenario`."""

    year: int
    starting_balance: Decimal
    contributions: Decimal
    interest_earned: Decimal
    ending_balance: Decimal
    real_balance: Decimal
    principal_portion: Decimal
    interest_portion: Decimal


class ProjectionResult(TypedDict):
    """Return value of :func:`investment.project_scenario`."""

    scenario: InvestmentScenario
    rows: list[ProjectionYearRow]
    ending_balance: Decimal
    total_contributed: Decimal
    total_earned: Decimal
    real_ending_balance: Decimal
    purchasing_power_loss: Decimal
    warning: str  # empty string when no high-rate warning
