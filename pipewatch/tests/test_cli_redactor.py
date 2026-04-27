"""Tests for CLI redaction commands."""

from __future__ import annotations

from click.testing import CliRunner

from pipewatch.cli_redactor import redactor_cmd, _RULES_FILE


def setup_function() -> None:
    if _RULES_FILE.exists():
        _RULES_FILE.unlink()


def test_add_rule_success() -> None:
    runner = CliRunner()
    result = runner.invoke(redactor_cmd, ["add", r"token=\w+"])
    assert result.exit_code == 0
    assert "Added redaction rule" in result.output


def test_add_rule_custom_replacement() -> None:
    runner = CliRunner()
    result = runner.invoke(redactor_cmd, ["add", r"secret=\w+", "--replacement", "***"])
    assert result.exit_code == 0
    assert "Added redaction rule" in result.output


def test_list_no_rules() -> None:
    runner = CliRunner()
    result = runner.invoke(redactor_cmd, ["list"])
    assert result.exit_code == 0
    assert "No redaction rules" in result.output


def test_list_with_rules() -> None:
    runner = CliRunner()
    runner.invoke(redactor_cmd, ["add", r"token=\w+", "--apply-to", "message"])
    result = runner.invoke(redactor_cmd, ["list"])
    assert result.exit_code == 0
    assert "token=" in result.output
    assert "message" in result.output


def test_clear_rules() -> None:
    runner = CliRunner()
    runner.invoke(redactor_cmd, ["add", r"token=\w+"])
    result = runner.invoke(redactor_cmd, ["clear"])
    assert result.exit_code == 0
    assert "cleared" in result.output
    list_result = runner.invoke(redactor_cmd, ["list"])
    assert "No redaction rules" in list_result.output
