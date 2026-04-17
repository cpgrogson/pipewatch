"""Tests for pipewatch.history module."""

import json
import os
import pytest

from pipewatch.history import HistoryEntry, HistoryStore


@pytest.fixture
def store(tmp_path):
    path = str(tmp_path / "history.json")
    return HistoryStore(path=path)


def make_entry(name="pipeline_a", alert_count=0, healthy=True, tags=None):
    return HistoryEntry(
        pipeline_name=name,
        checked_at="2024-01-01T00:00:00",
        alert_count=alert_count,
        healthy=healthy,
        tags=tags or [],
    )


def test_empty_store_returns_no_entries(store):
    assert store.all() == []


def test_record_adds_entry(store):
    entry = make_entry()
    store.record(entry)
    assert len(store.all()) == 1
    assert store.all()[0].pipeline_name == "pipeline_a"


def test_persists_to_disk(tmp_path):
    path = str(tmp_path / "history.json")
    s1 = HistoryStore(path=path)
    s1.record(make_entry(name="pipe_x", alert_count=2, healthy=False))

    s2 = HistoryStore(path=path)
    assert len(s2.all()) == 1
    assert s2.all()[0].pipeline_name == "pipe_x"
    assert s2.all()[0].healthy is False


def test_for_pipeline_filters_correctly(store):
    store.record(make_entry(name="alpha"))
    store.record(make_entry(name="beta"))
    store.record(make_entry(name="alpha", alert_count=1, healthy=False))

    results = store.for_pipeline("alpha")
    assert len(results) == 2
    assert all(e.pipeline_name == "alpha" for e in results)


def test_last_returns_most_recent(store):
    store.record(make_entry(name="pipe", alert_count=0, healthy=True))
    store.record(make_entry(name="pipe", alert_count=3, healthy=False))

    last = store.last("pipe")
    assert last is not None
    assert last.healthy is False
    assert last.alert_count == 3


def test_last_returns_none_for_unknown(store):
    assert store.last("nonexistent") is None


def test_clear_removes_all_entries(store):
    store.record(make_entry())
    store.record(make_entry(name="other"))
    store.clear()
    assert store.all() == []


def test_tags_persisted(tmp_path):
    path = str(tmp_path / "history.json")
    s1 = HistoryStore(path=path)
    s1.record(make_entry(tags=["prod", "critical"]))

    s2 = HistoryStore(path=path)
    assert s2.all()[0].tags == ["prod", "critical"]
