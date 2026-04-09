
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


def compare_scenarios(scenarios: Mapping[str, InvestmentScenario]) -> str:
    if not scenarios:
        return "No scenarios are saved yet."
    if len(scenarios) > 4:
        return "Please compare four scenarios or fewer."

    results: dict[str, ProjectionResult] = {}
    max_years = 0
    for name, scenario in scenarios.items():
        results[name] = project_scenario(scenario)
        max_years = max(max_years, int(scenario["years"]))

    names = list(results)
    lines = []
    header = f"{'Year':<6}"
    for name in names:
        header += f"{name[:16]:>18}"
    lines.append(header)
    lines.append("-" * len(header))

    for year_number in range(1, max_years + 1):
        line = f"{year_number:<6}"
        for name in names:
            rows = results[name]["rows"]
            if year_number <= len(rows):
                line += f"{format_money(rows[year_number - 1]['ending_balance']):>18}"
            else:
                line += f"{'-':>18}"
        lines.append(line)

    lines.append("-" * len(header))
    contributed_line = f"{'Contrib':<6}"
    earned_line = f"{'Earned':<6}"
    for name in names:
        contributed_line += f"{format_money(results[name]['total_contributed']):>18}"
        earned_line += f"{format_money(results[name]['total_earned']):>18}"
    lines.append(contributed_line)
    lines.append(earned_line)
    return "\n".join(lines)

def build_growth_chart(result: ProjectionResult, width: int = 80) -> str:
    rows = result["rows"]
    if not rows:
        return "No chart data available."

    bar_width = max(20, width - 26)
    max_balance = max(row["ending_balance"] for row in rows) or Decimal(1)
    encoding = sys.stdout.encoding or "utf-8"
    try:
        "█".encode(encoding)
        principal_char = "█"
        interest_char = "░"
    except (UnicodeEncodeError, LookupError, TypeError):
        principal_char = "#"
        interest_char = "."

    legend = f"Legend: {principal_char} principal/contributions, {interest_char} growth"
    lines = ["Growth chart", legend]
    lines.append("-" * min(width, 80))
    bar_dec = Decimal(bar_width)

    for row in rows:
        principal_width = int((row["principal_portion"] / max_balance) * bar_dec)
        interest_width = int((row["interest_portion"] / max_balance) * bar_dec)
        if principal_width + interest_width == 0:
            principal_width = 1
        bar = (principal_char * principal_width) + (interest_char * interest_width)
        end_bal = format_money(row["ending_balance"])
        lines.append(f"Year {row['year']:>2} {bar:<{bar_width}} {end_bal}")

    return "\n".join(lines)