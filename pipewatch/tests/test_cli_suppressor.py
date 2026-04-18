"""Tests for suppressor CLI commands."""
from click.testing import CliRunner
from pipewatch.cli_suppressor import suppress_cmd, _store


def setup_function():
    _store.rules.clear()
    _store._history.clear()


def test_add_suppression_rule():
    runner = CliRunner()
    result = runner.invoke(suppress_cmd, ["add", "my_pipeline", "duration", "--min-occurrences", "2", "--window", "120"])
    assert result.exit_code == 0
    assert "my_pipeline:duration" in result.output
    assert len(_store.rules) == 1


def test_list_no_rules():
    runner = CliRunner()
    result = runner.invoke(suppress_cmd, ["list"])
    assert result.exit_code == 0
    assert "No suppression rules" in result.output


def test_list_with_rules():
    runner = CliRunner()
    runner.invoke(suppress_cmd, ["add", "pipe_a", "error_rate"])
    result = runner.invoke(suppress_cmd, ["list"])
    assert "pipe_a:error_rate" in result.output


def test_clear_suppressions():
    runner = CliRunner()
    runner.invoke(suppress_cmd, ["add", "pipe_b", "rows_processed"])
    result = runner.invoke(suppress_cmd, ["clear"])
    assert result.exit_code == 0
    assert "cleared" in result.output
    assert len(_store.rules) == 0
