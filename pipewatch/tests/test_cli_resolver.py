"""Tests for pipewatch.cli_resolver."""

import pytest
from click.testing import CliRunner

import pipewatch.cli_resolver as cli_resolver_module
from pipewatch.cli_resolver import resolver_cmd
from pipewatch.resolver import ResolutionStore


@pytest.fixture(autouse=True)
def setup_function(tmp_path, monkeypatch):
    store = ResolutionStore(path=str(tmp_path / "resolutions.json"))
    monkeypatch.setattr(cli_resolver_module, "_store", store)


def test_add_resolution(tmp_path):
    runner = CliRunner()
    result = runner.invoke(resolver_cmd, ["add", "pipe_a", "error_rate"])
    assert result.exit_code == 0
    assert "Resolved: pipe_a/error_rate" in result.output


def test_add_resolution_with_note(tmp_path):
    runner = CliRunner()
    result = runner.invoke(resolver_cmd, ["add", "pipe_a", "duration", "--note", "fixed"])
    assert result.exit_code == 0
    assert "Note: fixed" in result.output


def test_list_no_resolutions():
    runner = CliRunner()
    result = runner.invoke(resolver_cmd, ["list"])
    assert result.exit_code == 0
    assert "No resolutions recorded" in result.output


def test_list_with_resolutions():
    runner = CliRunner()
    runner.invoke(resolver_cmd, ["add", "pipe_b", "row_count"])
    result = runner.invoke(resolver_cmd, ["list"])
    assert result.exit_code == 0
    assert "pipe_b/row_count" in result.output


def test_clear_resolutions():
    runner = CliRunner()
    runner.invoke(resolver_cmd, ["add", "pipe_a", "error_rate"])
    result = runner.invoke(resolver_cmd, ["clear"])
    assert result.exit_code == 0
    assert "cleared" in result.output
    list_result = runner.invoke(resolver_cmd, ["list"])
    assert "No resolutions recorded" in list_result.output
