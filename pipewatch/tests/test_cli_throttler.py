"""Tests for the throttle CLI commands."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from pipewatch.cli_throttler import throttle_cmd

_STORE = "/tmp/pipewatch_test_throttle.json"
_RULES = "/tmp/pipewatch_test_throttle.rules.json"


def setup_function():
    for p in [_STORE, _RULES]:
        path = Path(p)
        if path.exists():
            path.unlink()


def test_add_throttle_rule():
    runner = CliRunner()
    result = runner.invoke(
        throttle_cmd,
        ["add", "etl_main", "error_rate", "120", "--store", _STORE],
    )
    assert result.exit_code == 0
    assert "Throttle rule added" in result.output
    rules = json.loads(Path(_RULES).read_text())
    assert len(rules) == 1
    assert rules[0]["pipeline"] == "etl_main"
    assert rules[0]["interval_seconds"] == 120


def test_list_no_rules():
    runner = CliRunner()
    result = runner.invoke(throttle_cmd, ["list", "--store", _STORE])
    assert result.exit_code == 0
    assert "No throttle rules" in result.output


def test_list_with_rules():
    runner = CliRunner()
    runner.invoke(throttle_cmd, ["add", "etl_main", "duration", "60", "--store", _STORE])
    result = runner.invoke(throttle_cmd, ["list", "--store", _STORE])
    assert result.exit_code == 0
    assert "etl_main/duration" in result.output
    assert "60s" in result.output


def test_clear_throttles():
    runner = CliRunner()
    runner.invoke(throttle_cmd, ["add", "etl_main", "error_rate", "300", "--store", _STORE])
    result = runner.invoke(throttle_cmd, ["clear", "--store", _STORE])
    assert result.exit_code == 0
    assert "cleared" in result.output
    assert not Path(_RULES).exists()
