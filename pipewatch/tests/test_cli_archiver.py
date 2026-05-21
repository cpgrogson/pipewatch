"""Tests for pipewatch.cli_archiver."""

import pytest
from click.testing import CliRunner

from pipewatch.cli_archiver import archive_cmd
import pipewatch.cli_archiver as cli_archiver_module
from pipewatch.archiver import ArchiveStore


@pytest.fixture(autouse=True)
def setup_function(tmp_path):
    cli_archiver_module._STORE = ArchiveStore(path=str(tmp_path / "archive.json"))


@pytest.fixture
def runner():
    return CliRunner()


def test_add_archive_success(runner):
    result = runner.invoke(
        archive_cmd,
        ["add", "--pipeline", "my_pipe", "--metric", "error_rate", "--severity", "critical"],
    )
    assert result.exit_code == 0
    assert "Archived" in result.output
    assert "my_pipe" in result.output


def test_list_no_archives(runner):
    result = runner.invoke(archive_cmd, ["list"])
    assert result.exit_code == 0
    assert "No archived alerts" in result.output


def test_list_with_archives(runner):
    runner.invoke(
        archive_cmd,
        ["add", "--pipeline", "pipe_a", "--metric", "duration", "--reason", "resolved"],
    )
    result = runner.invoke(archive_cmd, ["list"])
    assert "pipe_a" in result.output
    assert "resolved" in result.output


def test_list_filter_by_pipeline(runner):
    runner.invoke(archive_cmd, ["add", "--pipeline", "pipe_a", "--metric", "m1"])
    runner.invoke(archive_cmd, ["add", "--pipeline", "pipe_b", "--metric", "m2"])
    result = runner.invoke(archive_cmd, ["list", "--pipeline", "pipe_a"])
    assert "pipe_a" in result.output
    assert "pipe_b" not in result.output


def test_clear_archives(runner):
    runner.invoke(archive_cmd, ["add", "--pipeline", "p", "--metric", "m"])
    result = runner.invoke(archive_cmd, ["clear"])
    assert result.exit_code == 0
    assert "cleared" in result.output
    list_result = runner.invoke(archive_cmd, ["list"])
    assert "No archived alerts" in list_result.output
