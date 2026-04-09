"""File helpers for the ll_investment CLI: data directory and atomic JSON writes."""

from __future__ import annotations

import json
import os
import uuid
import warnings
from collections.abc import Callable
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, cast


def _atomic_write_file(path: Path, write: Callable[[Path], None]) -> None:
    """Write to a unique temp file in the same directory, then replace ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.name}.tmp.{uuid.uuid4().hex}"
    try:
        write(tmp)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    try:
        os.replace(tmp, path)
    except OSError:
        tmp.unlink(missing_ok=True)
        raise


def get_data_dir(base_dir: str | Path | None = None) -> Path:
    """Return the data directory and create it if needed.

    If ``base_dir`` is omitted, uses ``LL_INVESTMENT_DATA_DIR`` when set; otherwise
    ``./ll_investment_data`` under the current working directory.

    ``LEDGERLOGIC_DATA_DIR`` is still honored for backward compatibility with older installs.
    """
    if base_dir is not None:
        root = Path(base_dir)
    else:
        env = (os.environ.get("LL_INVESTMENT_DATA_DIR") or "").strip()
        if not env:
            env = (os.environ.get("LEDGERLOGIC_DATA_DIR") or "").strip()
        if env:
            root = Path(env).expanduser()
        else:
            root = Path.cwd() / "ll_investment_data"
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_investment_profile_path(base_dir: str | Path | None = None) -> Path:
    return get_data_dir(base_dir) / "investment_scenarios.json"


def format_money(amount: Decimal) -> str:
    """Format a dollar amount for display (commas and two decimals, no float conversion)."""
    q = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    sign = "-" if q.is_signed() else ""
    q = abs(q)
    text = format(q, "f")
    if "." in text:
        whole, frac = text.split(".", 1)
        frac = (frac + "00")[:2]
    else:
        whole, frac = text, "00"
    n = len(whole)
    parts: list[str] = []
    for i, ch in enumerate(whole):
        if i > 0 and (n - i) % 3 == 0:
            parts.append(",")
        parts.append(ch)
    return f"${sign}{''.join(parts)}.{frac}"


def format_percent(rate: Decimal, *, decimal_places: int = 2) -> str:
    """Format a percentage value (e.g. annual rate) without using float."""
    exp = Decimal(10) ** -decimal_places
    q = rate.quantize(exp, rounding=ROUND_HALF_UP)
    return format(q, "f")


def _json_default(obj: Any) -> float | str:
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def save_json(data: dict[str, Any], path: str | Path) -> Path:
    """Save JSON data with readable indentation. :class:`~decimal.Decimal` values become floats."""
    output_path = Path(path)

    def write_json(tmp: Path) -> None:
        with tmp.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, default=_json_default)

    _atomic_write_file(output_path, write_json)
    return output_path


def load_json(path: str | Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load JSON object data or return a default if missing, invalid, or not a JSON object."""
    input_path = Path(path)
    if not input_path.exists():
        return {} if default is None else default
    fallback = {} if default is None else default
    try:
        with input_path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except json.JSONDecodeError as exc:
        warnings.warn(f"Invalid JSON in {input_path}: {exc}; using default.", stacklevel=2)
        return fallback.copy()
    if not isinstance(raw, dict):
        warnings.warn(
            f"JSON in {input_path} is not an object (got {type(raw).__name__}); using default.",
            stacklevel=2,
        )
        return fallback.copy()
    return cast(dict[str, Any], raw)
