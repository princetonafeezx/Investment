from __future__ import annotations

from collections.abc import Mapping
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from investment_engine import scenario_from_storage
from schemas import InvestmentScenario
from storage import get_investment_profile_path, load_json, save_json

SCHEMA_VERSION = 2
META_KEY = "__ll_investment__"

_DECIMAL_FIELDS = (
    "initial_principal",
    "annual_rate",
    "contribution_amount",
    "inflation_rate",
)

def _decimal_to_json_str(d: Decimal) -> str:
    q = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return format(q, "f")

def _scenario_to_storable(scenario: InvestmentScenario) -> dict[str, Any]:
    out: dict[str, Any] = dict(scenario)
    for key in _DECIMAL_FIELDS:
        out[key] = _decimal_to_json_str(out[key])
    return out

def load_persisted_scenarios() -> dict[str, InvestmentScenario]:
    raw = load_json(get_investment_profile_path(), default={})
    meta = raw.get(META_KEY)
    meta_version: int | None = None
    if isinstance(meta, dict):
        try:
            meta_version = int(meta["schema_version"])
        except (KeyError, TypeError, ValueError):
            meta_version = None
    if meta_version == SCHEMA_VERSION:
        scenario_entries = {k: v for k, v in raw.items() if k != META_KEY}
    else:
        scenario_entries = dict(raw)

    out: dict[str, InvestmentScenario] = {}
    for key, val in scenario_entries.items():
        if key == META_KEY:
            continue
        if not isinstance(val, dict):
            print(f"Skipped non-object scenario entry {key!r}.")
            continue
        scenario = scenario_from_storage(str(key), val)
        if scenario is None:
            print(f"Skipped invalid scenario stored under {key!r}.")
            continue
        out[scenario["name"]] = scenario
    return out

def save_persisted_scenarios(scenarios: Mapping[str, InvestmentScenario]) -> None:
    payload: dict[str, Any] = {
        META_KEY: {"schema_version": SCHEMA_VERSION},
        **{name: _scenario_to_storable(scenario) for name, scenario in scenarios.items()},
    }
    save_json(payload, get_investment_profile_path())