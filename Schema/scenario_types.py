"""Scenario input types for the compound-interest projector."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal, TypedDict

CompoundingLiteral = Literal["monthly", "annual"]
ContributionFrequencyLiteral = Literal["monthly", "annual"]
ContributionTimingLiteral = Literal["start", "end"]


class InvestmentScenario(TypedDict):
    """Fields expected by the investment projection engine."""

    name: str
    initial_principal: Decimal
    annual_rate: Decimal
    years: int
    compounding: CompoundingLiteral
    contribution_amount: Decimal
    contribution_frequency: ContributionFrequencyLiteral
    contribution_timing: ContributionTimingLiteral
    inflation_rate: Decimal
