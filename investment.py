"""LL Investment: standalone compound-interest CLI.

This module is the **public entry point** (`python investment.py`, console script
``ll-investment``). Implementation is split across sibling modules for clarity:

- :mod:`investment_engine` — validation and projection
- :mod:`investment_reporting` — tables and charts
- :mod:`investment_persist` — versioned JSON on disk (string decimals)
- :mod:`investment_cli` — interactive menu

Money and rates use :class:`~decimal.Decimal` in memory. New saves use **schema
version 2**: monetary fields in JSON are **decimal strings** for exact
round-trip; legacy files (plain nested objects with JSON numbers) still load.
"""

from __future__ import annotations

from investment_cli import (
    _parse_decimal_field,
    _parse_years_field,
    create_or_edit_scenario,
    menu,
    prompt_with_default,
)
from investment_engine import (
    contribution_for_period,
    default_scenario,
    project_scenario,
    scenario_from_storage,
    validate_scenario,
)
from investment_persist import load_persisted_scenarios, save_persisted_scenarios
from investment_reporting import build_growth_chart, compare_scenarios, format_single_projection

__all__ = [
    "build_growth_chart",
    "compare_scenarios",
    "contribution_for_period",
    "create_or_edit_scenario",
    "default_scenario",
    "format_single_projection",
    "load_persisted_scenarios",
    "menu",
    "project_scenario",
    "prompt_with_default",
    "save_persisted_scenarios",
    "scenario_from_storage",
    "validate_scenario",
    "_parse_decimal_field",
    "_parse_years_field",
]


def main() -> None:
    menu()


if __name__ == "__main__":
    main()
