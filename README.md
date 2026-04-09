# LL Investment

Standalone **compound interest projector** CLI: year-by-year balances, optional inflation-adjusted columns, up to four named scenarios side-by-side, and a text growth chart. Arithmetic uses Python’s **`decimal.Decimal`**.

## Requirements

- **Python 3.10+**
- **Runtime:** no third-party packages (stdlib only).
- **Development / CI:** see [Development](#development) or `requirements.txt`.

## Run

From the repo root:

```bash
python investment.py
```

Or install in editable mode and use the console script:

```bash
pip install -e .
ll-investment
```

## Data directory

Scenarios are saved to `investment_scenarios.json`.

- **Default directory:** `./ll_investment_data/` under the current working directory.
- **Override:** set **`LL_INVESTMENT_DATA_DIR`** to an absolute or relative path (the directory is created if needed).
- **Legacy:** **`LEDGERLOGIC_DATA_DIR`** is still read if `LL_INVESTMENT_DATA_DIR` is unset.

## Persistence format (schema v2)

New saves write a small metadata object plus one JSON object per scenario:

- Key **`__ll_investment__`** holds `{"schema_version": 2}`.
- Monetary fields (`initial_principal`, `annual_rate`, `contribution_amount`, `inflation_rate`) are stored as **decimal strings** (e.g. `"10000.00"`) so values round-trip exactly—no binary float in the file for those fields.
- **`years`** remains a JSON integer.

Older files without `__ll_investment__` (plain map of scenario name → object with JSON numbers) still load; re-saving upgrades them to v2.

## Project layout (standalone, flat modules)

| Module | Role |
|--------|------|
| `investment.py` | Entry point and re-exports for tests / scripts |
| `investment_engine.py` | Validation and projection |
| `investment_reporting.py` | Formatted table, comparison, chart |
| `investment_persist.py` | Load/save versioned JSON |
| `investment_cli.py` | Interactive menu and prompts |
| `schemas.py` | `TypedDict` shapes |
| `storage.py` | Data path, atomic JSON, `format_money` / `format_percent` |
| `parsing.py` | `parse_amount` / `parse_date` (shared helpers) |

## Tests

From the repo root (with dev dependencies installed):

```bash
pytest
```

`tests/test_cli.py` exercises the interactive menu by monkeypatching **`builtins.input`** with a fixed script and stubbing **`load_persisted_scenarios`** / **`save_persisted_scenarios`**. Other modules have unit tests for the engine, persistence, storage, and parsing.

## Development

Recommended (matches `pyproject.toml` optional **`dev`** extra):

```bash
pip install -e ".[dev]"
```

Alternatively:

```bash
pip install -r requirements.txt
pip install -e .
```

Then:

```bash
pytest
ruff check .
mypy
```

**CI:** `.github/workflows/ci.yml` runs **ruff**, **mypy**, and **pytest** on Python **3.10** and **3.12** for pushes and pull requests to `main` / `master`.

## Modeling note

With **annual compounding** and **monthly** contributions, the engine applies **twelve monthly payments as one lump** in the yearly period (documented in `investment_engine.py`). Use **monthly compounding** if you want each contribution aligned with its own accrual interval.
