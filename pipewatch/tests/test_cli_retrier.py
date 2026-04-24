"""Tests for pipewatch.cli_retrier."""
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from pipewatch.cli_retrier import retry_cmd
from pipewatch.retrier import RetryStore
from pipewatch.checker import Alert


def _store(tmp_path: Path) -> RetryStore:
    return RetryStore(path=tmp_path / "retries.json")


def _alert() -> Alert:
    return Alert(pipeline="etl", metric="duration", value=120, threshold=60, severity="warning")


def setup_function():
    """Ensure a clean state by patching the default store path per test."""


def test_list_no_retries(tmp_path: Path) -> None:
    runner = CliRunner()
    with patch("pipewatch.cli_retrier.RetryStore", lambda: _store(tmp_path)):
        result = runner.invoke(retry_cmd, ["list"])
    assert result.exit_code == 0
    assert "No pending retries" in result.output


def test_list_with_retries(tmp_path: Path) -> None:
    s = _store(tmp_path)
    s.enqueue(_alert())
    runner = CliRunner()
    with patch("pipewatch.cli_retrier.RetryStore", lambda: s):
        result = runner.invoke(retry_cmd, ["list"])
    assert result.exit_code == 0
    assert "etl/duration" in result.output


def test_due_no_entries(tmp_path: Path) -> None:
    runner = CliRunner()
    with patch("pipewatch.cli_retrier.RetryStore", lambda: _store(tmp_path)):
        result = runner.invoke(retry_cmd, ["due"])
    assert result.exit_code == 0
    assert "No retries due" in result.output


def test_clear_retries(tmp_path: Path) -> None:
    s = _store(tmp_path)
    s.enqueue(_alert())
    runner = CliRunner()
    with patch("pipewatch.cli_retrier.RetryStore", lambda: s):
        result = runner.invoke(retry_cmd, ["clear"])
    assert result.exit_code == 0
    assert "cleared" in result.output
    assert s.all() == []
