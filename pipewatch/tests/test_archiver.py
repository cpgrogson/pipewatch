"""Tests for pipewatch.archiver."""

import json
import os
import pytest

from pipewatch.archiver import ArchiveStore, ArchivedAlert
from pipewatch.checker import Alert


@pytest.fixture
def store(tmp_path):
    return ArchiveStore(path=str(tmp_path / "archive.json"))


def make_alert(pipeline="pipe_a", metric="error_rate", severity="warning"):
    return Alert(pipeline=pipeline, metric=metric, severity=severity, message="test")


def test_empty_store_returns_no_entries(store):
    assert store.all() == []


def test_archive_adds_entry(store):
    alert = make_alert()
    store.archive(alert)
    assert len(store.all()) == 1


def test_archived_entry_fields(store):
    alert = make_alert(pipeline="pipe_x", metric="duration", severity="critical")
    entry = store.archive(alert, reason="resolved")
    assert entry.pipeline == "pipe_x"
    assert entry.metric == "duration"
    assert entry.severity == "critical"
    assert entry.reason == "resolved"
    assert entry.archived_at is not None


def test_persists_to_disk(tmp_path):
    path = str(tmp_path / "archive.json")
    s1 = ArchiveStore(path=path)
    s1.archive(make_alert())
    s2 = ArchiveStore(path=path)
    assert len(s2.all()) == 1


def test_filter_by_pipeline(store):
    store.archive(make_alert(pipeline="a"))
    store.archive(make_alert(pipeline="b"))
    results = store.filter_by_pipeline("a")
    assert len(results) == 1
    assert results[0].pipeline == "a"


def test_filter_by_pipeline_no_match(store):
    store.archive(make_alert(pipeline="a"))
    assert store.filter_by_pipeline("z") == []


def test_clear_removes_all_entries(store):
    store.archive(make_alert())
    store.archive(make_alert(pipeline="b"))
    store.clear()
    assert store.all() == []


def test_from_dict_roundtrip():
    data = {
        "pipeline": "p",
        "metric": "m",
        "severity": "info",
        "message": "msg",
        "archived_at": "2024-01-01T00:00:00+00:00",
        "reason": "expired",
    }
    entry = ArchivedAlert.from_dict(data)
    assert entry.to_dict() == data
