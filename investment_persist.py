"""Versioned JSON persistence for investment scenarios (string decimals for round-trip)."""

# Enable postponed evaluation of annotations to allow for type hinting classes before they are defined
from __future__ import annotations

# Import Mapping for abstract dictionary-like type hints
from collections.abc import Mapping
# Import Decimal for high-precision math and ROUND_HALF_UP for standard rounding behavior
from decimal import ROUND_HALF_UP, Decimal
# Import Any to represent values of any type in generic containers
from typing import Any

# Import internal helper to convert stored raw data back into a valid InvestmentScenario object
from investment_engine import scenario_from_storage
# Import the TypedDict definition for investment scenario structures
from schemas import InvestmentScenario
# Import storage utilities for file paths and atomic JSON reading/writing
from storage import get_investment_profile_path, load_json, save_json

# Define the current schema version to manage data migrations or compatibility
SCHEMA_VERSION = 2
# Define a unique internal key used to store metadata within the JSON file
META_KEY = "__ll_investment__"

# Identify specific fields that must be handled as Decimals to avoid floating-point errors
_DECIMAL_FIELDS = (
    "initial_principal",
    "annual_rate",
    "contribution_amount",
    "inflation_rate",
)


def _decimal_to_json_str(d: Decimal) -> str:
    """Canonical two-decimal string for JSON (no binary float)."""
    # Force the Decimal to two decimal places using standard rounding (e.g., 1.235 becomes 1.24)
    q = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    # Return the decimal as a fixed-point string (prevents scientific notation like 1E+2)
    return format(q, "f")


def _scenario_to_storable(scenario: InvestmentScenario) -> dict[str, Any]:
    """Prepare a scenario object for JSON serialization by converting Decimals to strings."""
    # Create a shallow copy of the scenario dictionary to avoid mutating the original
    out: dict[str, Any] = dict(scenario)
    # Loop through the known numeric fields
    for key in _DECIMAL_FIELDS:
        # Replace the Decimal object with its string representation for safe storage
        out[key] = _decimal_to_json_str(out[key])
    # Return the dictionary now containing only JSON-serializable types
    return out


def load_persisted_scenarios() -> dict[str, InvestmentScenario]:
    """Load named scenarios from ``investment_scenarios.json`` under the data directory."""
    # Read the JSON file from the resolved profile path, defaulting to an empty dict if missing
    raw = load_json(get_investment_profile_path(), default={})
    # Attempt to retrieve the version metadata
    meta = raw.get(META_KEY)
    # Initialize version tracker
    meta_version: int | None = None
    # If metadata exists and is a dictionary, extract the schema version
    if isinstance(meta, dict):
        try:
            # Convert the version to an integer for comparison
            meta_version = int(meta["schema_version"])
        except (KeyError, TypeError, ValueError):
            # If metadata is malformed, treat it as an unversioned file
            meta_version = None
    # If the file matches the current version, extract everything except the metadata key
    if meta_version == SCHEMA_VERSION:
        scenario_entries = {k: v for k, v in raw.items() if k != META_KEY}
    else:
        # If unversioned or legacy, treat the entire dictionary as scenario data
        scenario_entries = dict(raw)

    # Initialize the output collection
    out: dict[str, InvestmentScenario] = {}
    # Iterate through each item in the loaded data
    for key, val in scenario_entries.items():
        # Safety check: skip the metadata key if it leaked into the entry list
        if key == META_KEY:
            continue
        # Ensure the value is a dictionary (a valid scenario structure)
        if not isinstance(val, dict):
            print(f"Skipped non-object scenario entry {key!r}.")
            continue
        # Use the engine helper to validate and convert raw data into a TypedDict
        scenario = scenario_from_storage(str(key), val)
        # Skip entries that failed validation (e.g., negative years or non-numeric strings)
        if scenario is None:
            print(f"Skipped invalid scenario stored under {key!r}.")
            continue
        # Store the valid scenario in the output map, indexed by its actual name
        out[scenario["name"]] = scenario
    # Return the dictionary of validated InvestmentScenario objects
    return out


def save_persisted_scenarios(scenarios: Mapping[str, InvestmentScenario]) -> None:
    """Write scenarios as v2 JSON (string decimals + schema marker)."""
    # Construct the final JSON payload
    payload: dict[str, Any] = {
        # Include the version marker so future loads know how to parse the data
        META_KEY: {"schema_version": SCHEMA_VERSION},
        # Use dictionary unpacking to merge in all scenarios converted to storable format
        **{name: _scenario_to_storable(scenario) for name, scenario in scenarios.items()},
    }
    # Persist the payload to the disk using the profile path
    save_json(payload, get_investment_profile_path())