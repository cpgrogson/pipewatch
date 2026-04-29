"""Tests for pipewatch.streaker."""

import os
import pytest

from pipewatch.checker import Alert
from pipewatch.streaker import StreakEntry, StreakStore


@pytest.fixture
def alert():
    return Alert(pipeline="etl_main", metric="error_rate", value=0.15, threshold=0.10, severity="warning")


@pytest.fixture
def store(tmp_path):
    return StreakStore(path=str(tmp_path / "streaks.json"))


def test_first_record_creates_entry(store, alert):
    entry = store.record(alert)
    assert entry.count == 1
    assert entry.pipeline == "etl_main"
    assert entry.metric == "error_rate"


def test_same_alert_increments_streak(store, alert):
    store.record(alert)
    store.record(alert)
    entry = store.record(alert)
    assert entry.count == 3


def test_severity_change_resets_streak(store, alert):
    store.record(alert)
    store.record(alert)
    critical = Alert(pipeline="etl_main", metric="error_rate", value=0.5, threshold=0.10, severity="critical")
    entry = store.record(critical)
    assert entry.count == 1
    assert entry.severity == "critical"


def test_get_returns_none_for_unknown_alert(store):
    unknown = Alert(pipeline="ghost", metric="rows", value=0, threshold=100, severity="warning")
    assert store.get(unknown) is None


def test_get_returns_entry_after_record(store, alert):
    store.record(alert)
    entry = store.get(alert)
    assert entry is not None
    assert entry.count == 1


def test_clear_removes_entry(store, alert):
    store.record(alert)
    store.clear(alert)
    assert store.get(alert) is None


def test_persists_to_disk(tmp_path, alert):
    path = str(tmp_path / "streaks.json")
    s1 = StreakStore(path=path)
    s1.record(alert)
    s1.record(alert)

    s2 = StreakStore(path=path)
    entry = s2.get(alert)
    assert entry is not None
    assert entry.count == 2


def test_all_entries_returns_all(store, alert):
    other = Alert(pipeline="loader", metric="duration", value=300, threshold=120, severity="critical")
    store.record(alert)
    store.record(other)
    assert len(store.all_entries()) == 2


def test_streak_entry_to_dict_roundtrip():
    e = StreakEntry(pipeline="p", metric="m", severity="warning", count=5)
    restored = StreakEntry.from_dict(e.to_dict())
    assert restored.pipeline == "p"
    assert restored.metric == "m"
    assert restored.severity == "warning"
    assert restored.count == 5
