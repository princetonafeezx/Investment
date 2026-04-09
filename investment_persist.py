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

