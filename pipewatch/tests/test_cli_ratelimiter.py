import pytest
from click.testing import CliRunner
from pipewatch.cli_ratelimiter import ratelimit_cmd, _store


def setup_function():
    _store.clear()


def test_add_rule_success():
    runner = CliRunner()
    result = runner.invoke(ratelimit_cmd, ["add", "etl_main", "error_rate", "--max-alerts", "5", "--window", "600"])
    assert result.exit_code == 0
    assert "etl_main:error_rate" in result.output


def test_list_no_rules():
    runner = CliRunner()
    result = runner.invoke(ratelimit_cmd, ["list"])
    assert result.exit_code == 0
    assert "No rate limit rules" in result.output


def test_list_with_rules():
    runner = CliRunner()
    runner.invoke(ratelimit_cmd, ["add", "pipeline_x", "duration", "--max-alerts", "2"])
    result = runner.invoke(ratelimit_cmd, ["list"])
    assert "pipeline_x:duration" in result.output
    assert "max=2" in result.output


def test_clear_rules():
    runner = CliRunner()
    runner.invoke(ratelimit_cmd, ["add", "p", "m"])
    result = runner.invoke(ratelimit_cmd, ["clear"])
    assert result.exit_code == 0
    assert "cleared" in result.output
    list_result = runner.invoke(ratelimit_cmd, ["list"])
    assert "No rate limit rules" in list_result.output
