
from __future__ import annotations

import sys
from collections.abc import Mapping
from decimal import Decimal

from investment_engine import project_scenario
from schemas import InvestmentScenario, ProjectionResult
from storage import format_money, format_percent


def format_single_projection(result: ProjectionResult) -> str:
    lines = []
    scenario = result["scenario"]
    lines.append(f"Scenario: {scenario['name']}")
    lines.append(
        f"Principal {format_money(scenario['initial_principal'])} | "
        f"Rate {format_percent(scenario['annual_rate'])}% | "
        f"Years {scenario['years']} | "
        f"Compounding {scenario['compounding']}"
    )
    if result["warning"]:
        lines.append(result["warning"])
    lines.append("-" * 108)
    lines.append(
        f"{'Year':<6}"
        f"{'Start':>14}"
        f"{'Contrib':>14}"
        f"{'Interest':>14}"
        f"{'End':>16}"
        f"{'Real End':>16}"
        f"{'Note':>10}"
    )
    lines.append("-" * 108)

    for row in result["rows"]:
        milestone_note = "milestone" if row["year"] % 5 == 0 else ""
        lines.append(
            f"{row['year']:<6}"
            f"{format_money(row['starting_balance']):>14}"
            f"{format_money(row['contributions']):>14}"
            f"{format_money(row['interest_earned']):>14}"
            f"{format_money(row['ending_balance']):>16}"
            f"{format_money(row['real_balance']):>16}"
            f"{milestone_note:>10}"
        )

    lines.append("-" * 108)
    lines.append(
        f"Total contributed: {format_money(result['total_contributed'])} | "
        f"Total earned: {format_money(result['total_earned'])}"
    )
    lines.append(
        f"Ending balance: {format_money(result['ending_balance'])} | "
        f"Inflation-adjusted ending balance: {format_money(result['real_ending_balance'])}"
    )
    lines.append(f"Purchasing power loss estimate: {format_money(result['purchasing_power_loss'])}")
    return "\n".join(lines)

