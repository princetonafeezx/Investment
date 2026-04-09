"""Interactive menu and prompts for the standalone CLI."""

# Enable postponed evaluation of annotations for type hinting
from __future__ import annotations

# Import Decimal for high-precision arithmetic and InvalidOperation for error handling
from decimal import Decimal, InvalidOperation
# Import cast to clarify types for the static type checker
from typing import cast

# Import core logic functions from the investment engine module
from investment_engine import default_scenario, project_scenario, validate_scenario
# Import storage functions to handle loading and saving data to disk
from investment_persist import load_persisted_scenarios, save_persisted_scenarios
# Import reporting functions to generate formatted text outputs and charts
from investment_reporting import build_growth_chart, compare_scenarios, format_single_projection
# Import the TypedDict definition for a scenario structure
from schemas import InvestmentScenario


def prompt_with_default(prompt: str, default_value: str) -> str:
    """Helper to display a prompt and return a default value if the user input is empty."""
    # Display the prompt with the default value in brackets
    entered = input(f"{prompt} [{default_value}]: ").strip()
    # Return user input if provided, otherwise return the default
    return entered if entered else default_value


def _parse_decimal_field(label: str, raw: str) -> Decimal | None:
    """Attempt to parse a string into a Decimal, returning None and printing an error on failure."""
    try:
        # Convert the trimmed string to a Decimal object
        return Decimal(raw.strip())
    except (InvalidOperation, ValueError, TypeError):
        # Notify the user if the input was not a valid numeric value
        print(f"{label} must be a valid number (got {raw!r}).")
        return None


def _parse_years_field(label: str, raw: str) -> int | None:
    """Attempt to parse a string into an integer (base 10), returning None on failure."""
    try:
        # Standard integer conversion
        return int(raw, 10)
    except ValueError:
        # Notify the user if the input was not a valid whole number
        print(f"{label} must be a whole number (got {raw!r}).")
        return None


def create_or_edit_scenario(
    existing: InvestmentScenario | None = None,
) -> InvestmentScenario | None:
    """Collect scenario fields from user input via interactive prompts."""
    # Use existing scenario data if editing, otherwise start with system defaults
    base = dict(existing) if existing is not None else default_scenario()
    # Prompt for each field, showing the current/default value
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

    # Convert the raw string inputs into their appropriate numeric types
    principal = _parse_decimal_field("Initial principal", principal_raw)
    rate = _parse_decimal_field("Annual interest rate (%)", rate_raw)
    years = _parse_years_field("Years", years_raw)
    contribution = _parse_decimal_field("Contribution amount", contribution_raw)
    inflation = _parse_decimal_field("Inflation rate (%)", inflation_raw)
    
    # If any numeric parsing failed, abort and return None
    if (
        principal is None
        or rate is None
        or years is None
        or contribution is None
        or inflation is None
    ):
        return None

    # Construct the candidate scenario dictionary with sanitized inputs
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

    # Validate the logic of the scenario (e.g., no negative interest) using the engine
    errors = validate_scenario(candidate)
    if errors:
        # If errors exist, print them for the user and return None
        print("Scenario had validation issues:")
        for error in errors:
            print(f"- {error}")
        return None
    # Return the valid scenario
    return candidate


def menu() -> None:
    """Interactive investment menu loop."""
    # Load any previously saved scenarios from the JSON file on startup
    scenarios = load_persisted_scenarios()
    # Inform the user how many scenarios were successfully loaded
    if scenarios:
        print(f"Loaded {len(scenarios)} scenario(s) from disk.")
    # Set of valid menu options
    valid_choices = {"1", "2", "3", "4", "5", "6", "7"}

    def persist() -> None:
        """Internal helper to save the current state of scenarios to disk."""
        try:
            save_persisted_scenarios(scenarios)
        except OSError as exc:
            # Handle file system errors gracefully
            print(f"Could not save scenarios to disk: {exc}")

    # Main interactive loop
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
        # Get user choice
        choice = input("Choose an option: ").strip()
        # Validate that the choice is one of the numbered options
        if choice not in valid_choices:
            print("Please choose a valid menu item.")
            continue

        # Handle Scenario Creation
        if choice == "1":
            # Limit the number of scenarios to prevent UI/reporting clutter
            if len(scenarios) >= 4:
                print("The comparison view is capped at four scenarios, so I'll stop there.")
                continue
            scenario = create_or_edit_scenario()
            if scenario:
                # Check for name collisions
                if scenario["name"] in scenarios:
                    confirm = input(
                        "That name exists already. Overwrite it? (y/n): ",
                    ).strip().lower()
                    if confirm != "y":
                        continue
                # Add/Update the scenario in the local dictionary and save to disk
                scenarios[scenario["name"]] = scenario
                persist()
                print(f"Saved scenario {scenario['name']}.")

        # Handle Viewing a Single Projection
        elif choice == "2":
            name = input("Scenario name: ").strip()
            if name not in scenarios:
                print("That scenario name was not found.")
                continue
            # Run the engine calculation and print the formatted table
            result = project_scenario(scenarios[name])
            print(format_single_projection(result))

        # Handle Side-by-Side Comparison
        elif choice == "3":
            # Print a comparison table of all current scenarios
            print(compare_scenarios(scenarios))

        # Handle Scenario Editing
        elif choice == "4":
            old_name = input("Scenario to edit: ").strip()
            if old_name not in scenarios:
                print("That scenario does not exist.")
                continue
            # Prompt user to update fields based on existing data
            updated = create_or_edit_scenario(scenarios[old_name])
            if updated is None:
                continue
            new_name = updated["name"]
            # Handle potential name changes during editing
            if new_name != old_name and new_name in scenarios:
                prompt = f"Overwrite existing scenario '{new_name}'? (y/n): "
                if input(prompt).strip().lower() != "y":
                    continue
            # If the name changed, remove the old key
            if new_name != old_name:
                scenarios.pop(old_name, None)
            # Update and save
            scenarios[new_name] = updated
            persist()
            print(f"Updated scenario {new_name}.")

        # Handle Scenario Deletion
        elif choice == "5":
            name = input("Scenario to delete: ").strip()
            if name in scenarios:
                scenarios.pop(name)
                persist()
                print(f"Deleted {name}.")
            else:
                print("That scenario was not found.")

        # Handle Growth Chart Visualization
        elif choice == "6":
            name = input("Scenario name for chart: ").strip()
            if name not in scenarios:
                print("That scenario was not found.")
                continue
            # Generate calculation results and display as an ASCII bar chart
            result = project_scenario(scenarios[name])
            print(build_growth_chart(result))

        # Handle Program Exit
        elif choice == "7":
            print("Exiting investment projector.")
            break