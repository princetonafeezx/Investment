"""Tests for data directory resolution and JSON helpers."""

from __future__ import annotations

import warnings

import storage


def test_get_data_dir_env_override_ll_investment(tmp_path, monkeypatch) -> None:
    data = tmp_path / "mydata"
    monkeypatch.setenv("LL_INVESTMENT_DATA_DIR", str(data))
    monkeypatch.delenv("LEDGERLOGIC_DATA_DIR", raising=False)
    resolved = storage.get_data_dir()
    assert resolved == data
    assert resolved.is_dir()


def test_get_data_dir_legacy_ledgerlogic_env(tmp_path, monkeypatch) -> None:
    data = tmp_path / "legacy"
    monkeypatch.delenv("LL_INVESTMENT_DATA_DIR", raising=False)
    monkeypatch.setenv("LEDGERLOGIC_DATA_DIR", str(data))
    resolved = storage.get_data_dir()
    assert resolved == data


def test_get_data_dir_explicit_base(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("LL_INVESTMENT_DATA_DIR", raising=False)
    monkeypatch.delenv("LEDGERLOGIC_DATA_DIR", raising=False)
    explicit = tmp_path / "explicit"
    resolved = storage.get_data_dir(base_dir=explicit)
    assert resolved == explicit


def test_load_json_corrupt_returns_default(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    default = {"ok": True}
    with warnings.catch_warnings(record=True) as wrec:
        warnings.simplefilter("always")
        out = storage.load_json(path, default=default)
    assert out == default
    assert len(wrec) == 1
    assert "Invalid JSON" in str(wrec[0].message)


def test_load_json_array_returns_default(tmp_path) -> None:
    path = tmp_path / "list.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    default = {"x": 1}
    with warnings.catch_warnings(record=True) as wrec:
        warnings.simplefilter("always")
        out = storage.load_json(path, default=default)
    assert out == default
    assert len(wrec) == 1
    assert "not an object" in str(wrec[0].message)


def test_save_json_atomic_no_leftover_tmp(tmp_path) -> None:
    path = tmp_path / "data.json"
    storage.save_json({"a": 1}, path)
    assert path.read_text(encoding="utf-8").strip().startswith("{")
    assert not list(tmp_path.glob(".*.tmp.*"))


def test_investment_profile_path_under_data_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LL_INVESTMENT_DATA_DIR", str(tmp_path / "d"))
    p = storage.get_investment_profile_path()
    assert p.name == "investment_scenarios.json"
    assert p.parent == tmp_path / "d"


def test_format_money_uses_commas_no_float_damage() -> None:
    from decimal import Decimal

    s = storage.format_money(Decimal("123456789012345678901234.99"))
    assert s == "$123,456,789,012,345,678,901,234.99"
