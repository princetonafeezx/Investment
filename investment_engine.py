"""Compound-interest engine: validation and projection (Decimal arithmetic).

**Modeling note:** When compounding is **annual** (one period per year) but
contributions are **monthly**, the simulator does **not** step month-by-month.
Instead, :func:`contribution_for_period` supplies **twelve monthly payments as
one lump** in that yearly period (timing ``start`` / ``end`` applies to that
lump relative to the single interest accrual for the year). That keeps the
loop simple but is **not** identical to twelve separate monthly deposits with
strict year-end compounding—use **monthly compounding** when you want each
contribution aligned with its own accrual interval.
"""

# Enable postponed evaluation of annotations for self-referencing type hints
from __future__ import annotations

# Import Mapping for read-only dictionary-like objects
from collections.abc import Mapping
# Import Decimal for fixed-point math and InvalidOperation for error handling
from decimal import Decimal, InvalidOperation
# Import Any for generic types and cast to override type checker inferences
from typing import Any, cast

# Import custom schema types for scenario and result structures
from schemas import InvestmentScenario, ProjectionResult, ProjectionYearRow

# Define sets of acceptable configuration values for validation
VALID_COMPOUNDING = {"monthly", "annual"}
VALID_CONTRIBUTION_FREQUENCIES = {"monthly", "annual"}
VALID_CONTRIBUTION_TIMING = {"start", "end"}

# Pre-define constant Decimals for performance and readability
_ZERO = Decimal(0)
_ONE = Decimal(1)
_PERCENT = Decimal(100)


def _coerce_decimal(value: Any) -> Decimal:
    """Safely convert various input types into a Decimal object."""
    # If it's already a Decimal, return it as-is
    if isinstance(value, Decimal):
        return value
    # Explicitly reject booleans as they would otherwise convert to 0 or 1
    if isinstance(value, bool):
        raise ValueError("boolean is not a numeric amount")
    # Convert integers directly
    if isinstance(value, int):
        return Decimal(value)
    # Convert floats to string first to avoid precision artifacts (e.g., 0.1 becoming 0.100000000000000005)
    if isinstance(value, float):
        return Decimal(str(value))
    # Clean whitespace and convert strings
    if isinstance(value, str):
        return Decimal(value.strip())
    # Fail for complex types, lists, etc.
    raise ValueError("unsupported type for Decimal")


def validate_scenario(scenario: Mapping[str, Any]) -> list[str]:
    """Validate a scenario in a very explicit student-y way."""
    # List to collect multiple validation error messages
    errors = []

    # Ensure the scenario has a non-empty name
    if not scenario.get("name"):
        errors.append("Scenario name cannot be blank.")

    # Validate initial_principal: must be numeric and non-negative
    try:
        if _coerce_decimal(scenario.get("initial_principal", 0)) < 0:
            errors.append("Initial principal cannot be negative.")
    except (InvalidOperation, TypeError, ValueError):
        errors.append("Initial principal has to be numeric.")

    # Validate annual_rate: must be numeric and non-negative
    try:
        rate = _coerce_decimal(scenario.get("annual_rate", 0))
        if rate < 0:
            errors.append("Interest rate cannot be negative.")
    except (InvalidOperation, TypeError, ValueError):
        errors.append("Interest rate has to be numeric.")

    # Validate years: must be a whole number greater than zero
    try:
        if int(scenario.get("years", 0)) <= 0:
            errors.append("Years must be greater than zero.")
    except (TypeError, ValueError):
        errors.append("Years must be a whole number.")

    # Validate contribution_amount: must be numeric and non-negative
    try:
        if _coerce_decimal(scenario.get("contribution_amount", 0)) < 0:
            errors.append("Contribution amount cannot be negative.")
    except (InvalidOperation, TypeError, ValueError):
        errors.append("Contribution amount has to be numeric.")

    # Validate inflation_rate: must be numeric and non-negative
    try:
        if _coerce_decimal(scenario.get("inflation_rate", 0)) < 0:
            errors.append("Inflation rate cannot be negative.")
    except (InvalidOperation, TypeError, ValueError):
        errors.append("Inflation rate has to be numeric.")

    # Check if compounding frequency is in the allowed set
    if scenario.get("compounding") not in VALID_COMPOUNDING:
        errors.append("Compounding must be monthly or annual.")

    # Check if contribution frequency is in the allowed set
    if scenario.get("contribution_frequency") not in VALID_CONTRIBUTION_FREQUENCIES:
        errors.append("Contribution frequency must be monthly or annual.")

    # Check if contribution timing (start or end of period) is valid
    if scenario.get("contribution_timing") not in VALID_CONTRIBUTION_TIMING:
        errors.append("Contribution timing must be start or end.")

    # Return the list of strings (empty if everything passed)
    return errors


def default_scenario(name: str = "Starter") -> InvestmentScenario:
    """Return a dictionary with sensible default values for a new investment projection."""
    return cast(
        InvestmentScenario,
        {
            "name": name,
            "initial_principal": Decimal("10000"),
            "annual_rate": Decimal("7"),
            "years": 20,
            "compounding": "monthly",
            "contribution_amount": Decimal("200"),
            "contribution_frequency": "monthly",
            "contribution_timing": "end",
            "inflation_rate": Decimal("2.5"),
        },
    )


def scenario_from_storage(storage_key: str, data: Mapping[str, Any]) -> InvestmentScenario | None:
    """Build a scenario from JSON-loaded dict; return None if it cannot be validated."""
    try:
        # Create a base object using defaults and the provided name or storage key
        base = default_scenario(name=str(data.get("name", storage_key)))
        # Copy base into a mutable dictionary
        merged: dict[str, Any] = dict(base)
        # Overwrite defaults with any existing values found in the loaded data
        for k in base:
            if k in data:
                merged[k] = data[k]
        # Clean up the name and ensure it isn't an empty string
        merged["name"] = str(data.get("name", storage_key)).strip() or str(storage_key)
        # Ensure all numeric types are strictly coerced to Decimal or int
        merged["initial_principal"] = _coerce_decimal(merged["initial_principal"])
        merged["annual_rate"] = _coerce_decimal(merged["annual_rate"])
        merged["years"] = int(merged["years"])
        merged["contribution_amount"] = _coerce_decimal(merged["contribution_amount"])
        merged["inflation_rate"] = _coerce_decimal(merged["inflation_rate"])
        # Normalize strings to lowercase and stripped whitespace
        merged["compounding"] = str(merged["compounding"]).strip().lower()
        merged["contribution_frequency"] = str(merged["contribution_frequency"]).strip().lower()
        merged["contribution_timing"] = str(merged["contribution_timing"]).strip().lower()
    except (InvalidOperation, TypeError, ValueError):
        # Return None if data conversion failed
        return None
    # Perform logic validation (e.g. non-negativity)
    errors = validate_scenario(merged)
    # Return None if logic validation failed
    if errors:
        return None
    # Return the final validated and typed scenario
    return cast(InvestmentScenario, merged)


def contribution_for_period(
    scenario: Mapping[str, Any], period_index: int, periods_per_year: int
) -> Decimal:
    """Calculate the specific cash flow for a single compounding period."""
    # Get frequency and base amount from the scenario
    frequency = scenario["contribution_frequency"]
    amount = _coerce_decimal(scenario["contribution_amount"])
    # Logic for monthly contributions
    if frequency == "monthly":
        # If we compound monthly, pay the single amount
        if periods_per_year == 12:
            return amount
        # If we compound annually, pay the full year's worth in one period
        return amount * Decimal(12)
    # Logic for annual contributions
    if frequency == "annual":
        # For monthly compounding, only pay the lump sum in the first month (period 1)
        if periods_per_year == 12:
            return amount if period_index == 1 else _ZERO
        # For annual compounding, pay the amount in the only period available
        return amount
    # Fallback for unexpected frequency strings
    return _ZERO


def project_scenario(scenario: Mapping[str, Any]) -> ProjectionResult:
    """Calculate year-by-year compound growth based on the provided scenario."""
    # Check for errors before starting the loop
    errors = validate_scenario(scenario)
    if errors:
        raise ValueError(" | ".join(errors))

    # Convert inputs into local Decimal variables for the loop
    years = int(scenario["years"])
    balance = _coerce_decimal(scenario["initial_principal"])
    annual_rate = _coerce_decimal(scenario["annual_rate"]) / _PERCENT # Convert % to decimal
    inflation_rate = _coerce_decimal(scenario["inflation_rate"]) / _PERCENT # Convert % to decimal
    # Determine how many internal loops per year based on compounding
    periods_per_year = 12 if scenario["compounding"] == "monthly" else 1
    contribution_timing = scenario["contribution_timing"]
    periods_dec = Decimal(periods_per_year)

    # Initialize accumulation lists and variables
    rows: list[ProjectionYearRow] = []
    running_contributions = _ZERO
    total_interest = _ZERO
    initial_principal = _coerce_decimal(scenario["initial_principal"])
    annual_rate_pct = _coerce_decimal(scenario["annual_rate"])

    # Start outer loop for each year
    for year_number in range(1, years + 1):
        # Capture the starting state of the current year
        year_start_balance = balance
        year_contributions = _ZERO
        year_interest = _ZERO

        # Start inner loop for each compounding period (1 or 12)
        for period_index in range(1, periods_per_year + 1):
            # Get the deposit for this specific period
            contribution = contribution_for_period(scenario, period_index, periods_per_year)
            # If timing is 'start', add contribution before calculating interest
            if contribution_timing == "start":
                balance += contribution
                year_contributions += contribution

            # Calculate periodic interest rate and interest amount
            period_rate = annual_rate / periods_dec
            interest = balance * period_rate
            balance += interest
            year_interest += interest

            # If timing is 'end', add contribution after interest has accrued
            if contribution_timing == "end":
                balance += contribution
                year_contributions += contribution

        # Accumulate totals for the final report
        running_contributions += year_contributions
        total_interest += year_interest

        # Calculate inflation factor for real purchasing power (Future Value / (1 + i)^n)
        inflation_factor = (_ONE + inflation_rate) ** year_number if inflation_rate > 0 else _ONE
        real_balance = balance / inflation_factor
        # Calculate how much of the balance is just the money put in
        principal_so_far = initial_principal + running_contributions

        # Build the structured row for the current year
        rows.append(
            cast(
                ProjectionYearRow,
                {
                    "year": year_number,
                    "starting_balance": year_start_balance,
                    "contributions": year_contributions,
                    "interest_earned": year_interest,
                    "ending_balance": balance,
                    "real_balance": real_balance,
                    "principal_portion": principal_so_far,
                    "interest_portion": max(_ZERO, balance - principal_so_far),
                },
            )
        )

    # Return the full projection results dictionary
    return cast(
        ProjectionResult,
        {
            "scenario": cast(InvestmentScenario, dict(scenario)),
            "rows": rows,
            "ending_balance": balance,
            "total_contributed": initial_principal + running_contributions,
            "total_earned": total_interest,
            "real_ending_balance": rows[-1]["real_balance"] if rows else balance,
            "purchasing_power_loss": balance - (rows[-1]["real_balance"] if rows else balance),
            "warning": (
                "High rate warning: annual rate is above 25%."
                if annual_rate_pct > Decimal("25")
                else ""
            ),
        },
    )