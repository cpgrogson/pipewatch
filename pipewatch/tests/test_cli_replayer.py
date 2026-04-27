"""Tests for pipewatch.cli_replayer."""

import json
import pytest
from click.testing import CliRunner
from datetime import datetime

from pipewatch.cli_replayer import replay_cmd
from pipewatch.history import HistoryStore, HistoryEntry
from pipewatch.checker import Alert


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def history_file(tmp_path):
    path = str(tmp_path / "history.json")
    store = HistoryStore(path=path)
    alert = Alert(
        pipeline="etl_main",
        metric="error_rate",
        value=0.3,
        threshold=0.1,
        severity="critical",
    )
    store.record(
        HistoryEntry(
            pipeline="etl_main",
            alerts=[alert],
            timestamp=datetime(2024, 6, 1, 10, 0, 0),
        )
    )
    return path


def test_run_replay_no_entries(runner, tmp_path):
    path = str(tmp_path / "empty.json")
    result = runner.invoke(replay_cmd, ["run", "--store", path])
    assert result.exit_code == 0
    assert "Replayed 0" in result.output


def test_run_replay_with_entries(runner, history_file):
    result = runner.invoke(replay_cmd, ["run", "--store", history_file])
    assert result.exit_code == 0
    assert "etl_main" in result.output
    assert "Replayed 1" in result.output


def test_run_replay_filter_pipeline(runner, history_file):
    result = runner.invoke(
        replay_cmd, ["run", "--store", history_file, "--pipeline", "other_pipe"]
    )
    assert result.exit_code == 0
    assert "Replayed 0" in result.output


def test_run_replay_invalid_since(runner, history_file):
    result = runner.invoke(
        replay_cmd, ["run", "--store", history_file, "--since", "not-a-date"]
    )
    assert result.exit_code != 0


def test_run_replay_limit(runner, tmp_path):
    path = str(tmp_path / "multi.json")
    store = HistoryStore(path=path)
    for i in range(4):
        store.record(
            HistoryEntry(
                pipeline=f"pipe_{i}",
                alerts=[],
                timestamp=datetime(2024, 6, i + 1, 10, 0, 0),
            )
        )
    result = runner.invoke(replay_cmd, ["run", "--store", path, "--limit", "2"])
    assert result.exit_code == 0
    assert "Replayed 2" in result.output
