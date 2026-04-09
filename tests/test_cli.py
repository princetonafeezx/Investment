"""Tests for interactive CLI (scripted ``input()`` via monkeypatch)."""

from __future__ import annotations

from collections import deque
from decimal import Decimal

import investment_cli
from investment_engine import default_scenario


def _scripted_input(responses: list[str]):
    """Return a callable for ``builtins.input`` that consumes ``responses`` in order."""
    q = deque(responses)

    def _fake(prompt: str = "") -> str:  # noqa: ARG001
        if not q:
            msg = f"No scripted reply left; last prompt was {prompt!r}"
            raise AssertionError(msg)
        return q.popleft()

    return _fake


def test_prompt_with_default_empty_uses_default(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _p: "")
    assert investment_cli.prompt_with_default("X", "fallback") == "fallback"


def test_prompt_with_default_non_empty(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _p: "  typed  ")
    assert investment_cli.prompt_with_default("X", "fallback") == "typed"


def test_menu_quit_immediately(monkeypatch, capsys) -> None:
    monkeypatch.setattr("investment_cli.load_persisted_scenarios", lambda: {})
    monkeypatch.setattr("investment_cli.save_persisted_scenarios", lambda _s: None)
    monkeypatch.setattr("builtins.input", _scripted_input(["7"]))
    investment_cli.menu()
    out = capsys.readouterr().out
    assert "Exiting investment projector" in out


def test_menu_invalid_choice_then_quit(monkeypatch, capsys) -> None:
    monkeypatch.setattr("investment_cli.load_persisted_scenarios", lambda: {})
    monkeypatch.setattr("investment_cli.save_persisted_scenarios", lambda _s: None)
    monkeypatch.setattr("builtins.input", _scripted_input(["invalid", "7"]))
    investment_cli.menu()
    out = capsys.readouterr().out
    assert "Please choose a valid menu item" in out
    assert "Exiting investment projector" in out


def test_menu_compare_empty_scenarios(monkeypatch, capsys) -> None:
    monkeypatch.setattr("investment_cli.load_persisted_scenarios", lambda: {})
    monkeypatch.setattr("investment_cli.save_persisted_scenarios", lambda _s: None)
    monkeypatch.setattr("builtins.input", _scripted_input(["3", "7"]))
    investment_cli.menu()
    assert "No scenarios are saved yet" in capsys.readouterr().out


def test_menu_view_scenario_not_found(monkeypatch, capsys) -> None:
    monkeypatch.setattr("investment_cli.load_persisted_scenarios", lambda: {})
    monkeypatch.setattr("investment_cli.save_persisted_scenarios", lambda _s: None)
    monkeypatch.setattr("builtins.input", _scripted_input(["2", "missing", "7"]))
    investment_cli.menu()
    assert "not found" in capsys.readouterr().out


def test_menu_chart_not_found(monkeypatch, capsys) -> None:
    monkeypatch.setattr("investment_cli.load_persisted_scenarios", lambda: {})
    monkeypatch.setattr("investment_cli.save_persisted_scenarios", lambda _s: None)
    monkeypatch.setattr("builtins.input", _scripted_input(["6", "ghost", "7"]))
    investment_cli.menu()
    assert "not found" in capsys.readouterr().out.lower()


def test_menu_delete_not_found(monkeypatch, capsys) -> None:
    monkeypatch.setattr("investment_cli.load_persisted_scenarios", lambda: {})
    monkeypatch.setattr("investment_cli.save_persisted_scenarios", lambda _s: None)
    monkeypatch.setattr("builtins.input", _scripted_input(["5", "nope", "7"]))
    investment_cli.menu()
    assert "not found" in capsys.readouterr().out.lower()


def test_menu_delete_success_persists(monkeypatch, capsys) -> None:
    state = {"Go": default_scenario("Go")}
    snapshots: list[dict] = []

    def capture(scenarios: dict) -> None:
        snapshots.append(dict(scenarios))

    monkeypatch.setattr("investment_cli.load_persisted_scenarios", lambda: dict(state))
    monkeypatch.setattr("investment_cli.save_persisted_scenarios", capture)
    monkeypatch.setattr("builtins.input", _scripted_input(["5", "Go", "7"]))
    investment_cli.menu()
    assert "Deleted Go" in capsys.readouterr().out
    assert len(snapshots) == 1
    assert snapshots[0] == {}


def test_menu_edit_scenario_not_found(monkeypatch, capsys) -> None:
    monkeypatch.setattr("investment_cli.load_persisted_scenarios", lambda: {})
    monkeypatch.setattr("investment_cli.save_persisted_scenarios", lambda _s: None)
    monkeypatch.setattr("builtins.input", _scripted_input(["4", "nobody", "7"]))
    investment_cli.menu()
    assert "does not exist" in capsys.readouterr().out


def test_menu_create_with_all_defaults_saves_and_quits(monkeypatch, capsys) -> None:
    saved: list[dict] = []

    def capture(scenarios: dict) -> None:
        saved.append(dict(scenarios))

    monkeypatch.setattr("investment_cli.load_persisted_scenarios", lambda: {})
    monkeypatch.setattr("investment_cli.save_persisted_scenarios", capture)
    # 1 = create, nine prompts accept defaults, 7 = quit
    replies = ["1", *([""] * 9), "7"]
    monkeypatch.setattr("builtins.input", _scripted_input(replies))
    investment_cli.menu()
    out = capsys.readouterr().out
    assert "Saved scenario Starter" in out
    assert len(saved) == 1
    assert "Starter" in saved[0]
    assert saved[0]["Starter"]["initial_principal"] == Decimal("10000")


def test_menu_create_validation_failure_returns_to_menu(monkeypatch, capsys) -> None:
    saved: list[dict] = []

    def capture(scenarios: dict) -> None:
        saved.append(dict(scenarios))

    monkeypatch.setattr("investment_cli.load_persisted_scenarios", lambda: {})
    monkeypatch.setattr("investment_cli.save_persisted_scenarios", capture)
    # name, principal, rate, years=0 invalid, compounding, contrib, freq, timing, inflation
    replies = [
        "1",
        "Bad",
        "1000",
        "5",
        "0",
        "monthly",
        "0",
        "monthly",
        "end",
        "0",
        "7",
    ]
    monkeypatch.setattr("builtins.input", _scripted_input(replies))
    investment_cli.menu()
    out = capsys.readouterr().out
    assert "Scenario had validation issues" in out
    assert saved == []


def test_menu_create_overwrite_declined(monkeypatch, capsys) -> None:
    existing = {"Dup": default_scenario("Dup")}
    saved: list[dict] = []

    def capture(scenarios: dict) -> None:
        saved.append(dict(scenarios))

    monkeypatch.setattr("investment_cli.load_persisted_scenarios", lambda: dict(existing))
    monkeypatch.setattr("investment_cli.save_persisted_scenarios", capture)
    # create with same name "Dup" (defaults use Starter - need custom name "Dup" first prompt)
    # Actually default base from None is Starter - we need name Dup to collide. First prompt "Dup"
    replies = [
        "1",
        "Dup",
        "5000",
        "6",
        "10",
        "monthly",
        "100",
        "monthly",
        "end",
        "2",
        "n",  # decline overwrite
        "7",
    ]
    monkeypatch.setattr("builtins.input", _scripted_input(replies))
    investment_cli.menu()
    assert saved == []  # persist not called on decline
    out = capsys.readouterr().out
    assert "Saved scenario Dup" not in out


def test_menu_stops_create_when_four_scenarios(monkeypatch, capsys) -> None:
    four = {f"S{i}": default_scenario(f"S{i}") for i in range(4)}

    monkeypatch.setattr("investment_cli.load_persisted_scenarios", lambda: dict(four))
    monkeypatch.setattr("investment_cli.save_persisted_scenarios", lambda _s: None)
    monkeypatch.setattr("builtins.input", _scripted_input(["1", "7"]))
    investment_cli.menu()
    assert "capped at four" in capsys.readouterr().out.lower()


def test_menu_view_scenario_shows_table(monkeypatch, capsys) -> None:
    one = {"T": default_scenario("T")}
    one["T"]["years"] = 1
    one["T"]["contribution_amount"] = Decimal("0")

    monkeypatch.setattr("investment_cli.load_persisted_scenarios", lambda: dict(one))
    monkeypatch.setattr("investment_cli.save_persisted_scenarios", lambda _s: None)
    monkeypatch.setattr("builtins.input", _scripted_input(["2", "T", "7"]))
    investment_cli.menu()
    out = capsys.readouterr().out
    assert "Scenario: T" in out
    assert "Year" in out


def test_menu_loaded_message_when_disk_has_scenarios(monkeypatch, capsys) -> None:
    one = {"Only": default_scenario("Only")}

    monkeypatch.setattr("investment_cli.load_persisted_scenarios", lambda: dict(one))
    monkeypatch.setattr("investment_cli.save_persisted_scenarios", lambda _s: None)
    monkeypatch.setattr("builtins.input", _scripted_input(["7"]))
    investment_cli.menu()
    assert "Loaded 1 scenario(s) from disk" in capsys.readouterr().out
