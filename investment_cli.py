from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import cast

from investment_engine import default_scenario, project_scenario, validate_scenario
from investment_persist import load_persisted_scenarios, save_persisted_scenarios
from investment_reporting import build_growth_chart, compare_scenarios, format_single_projection
from schemas import InvestmentScenario

def prompt_with_default(prompt: str, default_value: str) -> str:
    entered = input(f"{prompt} [{default_value}]: ").strip()
    return entered if entered else default_value

def _parse_decimal_field(label: str, raw: str) -> Decimal | None:
    try:
        return Decimal(raw.strip())
    except (InvalidOperation, ValueError, TypeError):
        print(f"{label} must be a valid number (got {raw!r}).")
        return None

def _parse_years_field(label: str, raw: str) -> int | None:
    try:
        return int(raw, 10)
    except ValueError:
        print(f"{label} must be a whole number (got {raw!r}).")
        return None

def create_or_edit_scenario(
    existing: InvestmentScenario | None = None,
) -> InvestmentScenario | None:
    base = dict(existing) if existing is not None else default_scenario()
    name = prompt_with_default("Scenario name", str(base["name"]))
    principal_raw = prompt_with_default("Initial principal", str(base["initial_principal"]))
    rate_raw = prompt_with_default("Annual interest rate (%)", str(base["annual_rate"]))
    years_raw = prompt_with_default("Years", str(base["years"]))
    compounding = prompt_with_default("Compounding (monthly/annual)", str(base["compounding"]))
    contribution_raw = prompt_with_default("Contribution amount", str(base["contribution_amount"]))
    contribution_frequency = prompt_with_default(
        "Contribution frequency (monthly/annual)", str(base["contribution_frequency"])
    )
    contribution_timing = prompt_with_default(
        "Contribution timing (start/end)",
        str(base["contribution_timing"]),
    )
    inflation_raw = prompt_with_default("Inflation rate (%)", str(base["inflation_rate"]))

    principal = _parse_decimal_field("Initial principal", principal_raw)
    rate = _parse_decimal_field("Annual interest rate (%)", rate_raw)
    years = _parse_years_field("Years", years_raw)
    contribution = _parse_decimal_field("Contribution amount", contribution_raw)
    inflation = _parse_decimal_field("Inflation rate (%)", inflation_raw)
    if (
        principal is None
        or rate is None
        or years is None
        or contribution is None
        or inflation is None
    ):
        return None

    candidate = cast(
        InvestmentScenario,
        {
            "name": name,
            "initial_principal": principal,
            "annual_rate": rate,
            "years": years,
            "compounding": compounding.strip().lower(),
            "contribution_amount": contribution,
            "contribution_frequency": contribution_frequency.strip().lower(),
            "contribution_timing": contribution_timing.strip().lower(),
            "inflation_rate": inflation,
        },
    )

    errors = validate_scenario(candidate)
    if errors:
        print("Scenario had validation issues:")
        for error in errors:
            print(f"- {error}")
        return None
    return candidate

def menu() -> None:
    scenarios = load_persisted_scenarios()
    if scenarios:
        print(f"Loaded {len(scenarios)} scenario(s) from disk.")
    valid_choices = {"1", "2", "3", "4", "5", "6", "7"}

    def persist() -> None:
        try:
            save_persisted_scenarios(scenarios)
        except OSError as exc:
            print(f"Could not save scenarios to disk: {exc}")

    while True:
        print()
        print("LL Investment: Compound Interest Projector")
        print("1. Create scenario")
        print("2. View single scenario")
        print("3. Compare scenarios")
        print("4. Edit a scenario")
        print("5. Delete a scenario")
        print("6. Show chart")
        print("7. Quit")
        choice = input("Choose an option: ").strip()
        if choice not in valid_choices:
            print("Please choose a valid menu item.")
            continue

        if choice == "1":
            if len(scenarios) >= 4:
                print("The comparison view is capped at four scenarios, so I'll stop there.")
                continue
            scenario = create_or_edit_scenario()
            if scenario:
                if scenario["name"] in scenarios:
                    confirm = input(
                        "That name exists already. Overwrite it? (y/n): ",
                    ).strip().lower()
                    if confirm != "y":
                        continue
                scenarios[scenario["name"]] = scenario
                persist()
                print(f"Saved scenario {scenario['name']}.")

        elif choice == "2":
            name = input("Scenario name: ").strip()
            if name not in scenarios:
                print("That scenario name was not found.")
                continue
            result = project_scenario(scenarios[name])
            print(format_single_projection(result))

        elif choice == "3":
            print(compare_scenarios(scenarios))

        elif choice == "4":
            old_name = input("Scenario to edit: ").strip()
            if old_name not in scenarios:
                print("That scenario does not exist.")
                continue
            updated = create_or_edit_scenario(scenarios[old_name])
            if updated is None:
                continue
            new_name = updated["name"]
            if new_name != old_name and new_name in scenarios:
                prompt = f"Overwrite existing scenario '{new_name}'? (y/n): "
                if input(prompt).strip().lower() != "y":
                    continue
            if new_name != old_name:
                scenarios.pop(old_name, None)
            scenarios[new_name] = updated
            persist()
            print(f"Updated scenario {new_name}.")

        elif choice == "5":
            name = input("Scenario to delete: ").strip()
            if name in scenarios:
                scenarios.pop(name)
                persist()
                print(f"Deleted {name}.")
            else:
                print("That scenario was not found.")

        elif choice == "6":
            name = input("Scenario name for chart: ").strip()
            if name not in scenarios:
                print("That scenario was not found.")
                continue
            result = project_scenario(scenarios[name])
            print(build_growth_chart(result))

        elif choice == "7":
            print("Exiting investment projector.")
            break
