"""Tests for investment scenario validation and projection."""

from __future__ import annotations

from decimal import Decimal

import pytest

import investment
from schemas import InvestmentScenario


def test_parse_decimal_rejects_non_numeric() -> None:
    assert investment._parse_decimal_field("X", "abc") is None


def test_parse_years_rejects_non_integer() -> None:
    assert investment._parse_years_field("Years", "3.5") is None


def test_validate_scenario_flags_blank_name() -> None:
    scenario = investment.default_scenario("")
    errors = investment.validate_scenario(scenario)
    assert any("name" in e.lower() for e in errors)


def test_project_scenario_one_year_no_contrib_flat_rate() -> None:
    scenario = investment.default_scenario("T")
    scenario["initial_principal"] = Decimal("1000")
    scenario["annual_rate"] = Decimal("0")
    scenario["years"] = 1
    scenario["contribution_amount"] = Decimal("0")
    scenario["inflation_rate"] = Decimal("0")
    result = investment.project_scenario(scenario)
    assert result["ending_balance"] == Decimal("1000")
    assert len(result["rows"]) == 1


def test_project_scenario_rejects_invalid() -> None:
    bad = investment.default_scenario("X")
    bad["years"] = 0
    with pytest.raises(ValueError, match="Years"):
        investment.project_scenario(bad)


def test_project_scenario_high_rate_warning() -> None:
    scenario = investment.default_scenario("Risky")
    scenario["annual_rate"] = Decimal("30")
    scenario["years"] = 1
    scenario["contribution_amount"] = Decimal("0")
    result = investment.project_scenario(scenario)
    assert "High rate warning" in result["warning"]


def test_annual_compounding_monthly_contributions_lump_per_year() -> None:
    """Monthly frequency with annual compounding = 12× monthly as one yearly lump."""
    scenario = investment.default_scenario("Lump")
    scenario["initial_principal"] = Decimal("0")
    scenario["annual_rate"] = Decimal("0")
    scenario["years"] = 1
    scenario["compounding"] = "annual"
    scenario["contribution_amount"] = Decimal("100")
    scenario["contribution_frequency"] = "monthly"
    scenario["contribution_timing"] = "end"
    scenario["inflation_rate"] = Decimal("0")
    result = investment.project_scenario(scenario)
    assert result["rows"][0]["contributions"] == Decimal("1200")
    assert result["ending_balance"] == Decimal("1200")


def test_monthly_compounding_twelve_distinct_contributions() -> None:
    scenario = investment.default_scenario("Monthly")
    scenario["initial_principal"] = Decimal("0")
    scenario["annual_rate"] = Decimal("0")
    scenario["years"] = 1
    scenario["compounding"] = "monthly"
    scenario["contribution_amount"] = Decimal("100")
    scenario["contribution_frequency"] = "monthly"
    scenario["contribution_timing"] = "end"
    scenario["inflation_rate"] = Decimal("0")
    result = investment.project_scenario(scenario)
    assert result["rows"][0]["contributions"] == Decimal("1200")


def test_inflation_reduces_real_balance() -> None:
    scenario = investment.default_scenario("Inf")
    scenario["initial_principal"] = Decimal("1000")
    scenario["annual_rate"] = Decimal("0")
    scenario["years"] = 1
    scenario["contribution_amount"] = Decimal("0")
    scenario["inflation_rate"] = Decimal("10")
    result = investment.project_scenario(scenario)
    assert result["rows"][0]["ending_balance"] == Decimal("1000")
    assert result["rows"][0]["real_balance"] < Decimal("1000")


def test_compare_scenarios_two_names() -> None:
    a: InvestmentScenario = investment.default_scenario("A")
    a["years"] = 1
    b: InvestmentScenario = investment.default_scenario("B")
    b["years"] = 1
    b["initial_principal"] = Decimal("5000")
    text = investment.compare_scenarios({"A": a, "B": b})
    assert "Year" in text
    assert "A" in text and "B" in text


def test_build_growth_chart_smoke() -> None:
    scenario = investment.default_scenario("C")
    scenario["years"] = 2
    scenario["contribution_amount"] = Decimal("0")
    result = investment.project_scenario(scenario)
    chart = investment.build_growth_chart(result)
    assert "Growth chart" in chart


def test_scenario_from_storage_valid_dict() -> None:
    s = investment.default_scenario("Zed")
    assert investment.scenario_from_storage("ignored", dict(s)) == s


def test_scenario_from_storage_rejects_bad_data() -> None:
    assert investment.scenario_from_storage("x", {"years": 0}) is None


def test_save_and_load_persisted_scenarios(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LL_INVESTMENT_DATA_DIR", str(tmp_path))
    one = investment.default_scenario("One")
    one["years"] = 5
    investment.save_persisted_scenarios({"One": one})
    loaded = investment.load_persisted_scenarios()
    assert loaded["One"]["years"] == 5
    assert loaded["One"]["name"] == "One"
    assert loaded["One"]["initial_principal"] == one["initial_principal"]


def test_persist_v2_writes_string_decimals(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LL_INVESTMENT_DATA_DIR", str(tmp_path))
    from storage import get_investment_profile_path

    one = investment.default_scenario("One")
    investment.save_persisted_scenarios({"One": one})
    text = get_investment_profile_path().read_text(encoding="utf-8")
    assert "__ll_investment__" in text
    assert '"schema_version": 2' in text
    assert '"initial_principal": "10000.00"' in text


def test_load_legacy_v1_numeric_json(tmp_path, monkeypatch) -> None:
    """Pre-v2 files: flat map, JSON numbers (still supported)."""
    import json

    monkeypatch.setenv("LL_INVESTMENT_DATA_DIR", str(tmp_path))
    from storage import get_investment_profile_path

    legacy = {
        "Legacy": {
            "name": "Legacy",
            "initial_principal": 1000,
            "annual_rate": 5,
            "years": 1,
            "compounding": "monthly",
            "contribution_amount": 0,
            "contribution_frequency": "monthly",
            "contribution_timing": "end",
            "inflation_rate": 0,
        }
    }
    path = get_investment_profile_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(legacy), encoding="utf-8")
    loaded = investment.load_persisted_scenarios()
    assert loaded["Legacy"]["initial_principal"] == Decimal("1000")
    assert loaded["Legacy"]["annual_rate"] == Decimal("5")
