"""Tests for pipewatch.resolver."""

import json
import os
import tempfile

import pytest

from pipewatch.checker import Alert
from pipewatch.resolver import ResolutionEntry, ResolutionStore


@pytest.fixture
def store(tmp_path):
    return ResolutionStore(path=str(tmp_path / "resolutions.json"))


def make_alert(pipeline="pipe_a", metric="error_rate", severity="critical"):
    return Alert(pipeline=pipeline, metric=metric, message="threshold exceeded", severity=severity)


def test_empty_store_returns_not_resolved(store):
    assert store.is_resolved("pipe_a", "error_rate") is False


def test_resolve_marks_as_resolved(store):
    alert = make_alert()
    store.resolve(alert)
    assert store.is_resolved("pipe_a", "error_rate") is True


def test_resolve_different_metric_not_resolved(store):
    alert = make_alert(metric="error_rate")
    store.resolve(alert)
    assert store.is_resolved("pipe_a", "duration") is False


def test_resolve_stores_note(store):
    alert = make_alert()
    store.resolve(alert, note="fixed upstream")
    entries = store.all()
    assert entries[0].note == "fixed upstream"


def test_resolve_persists_to_disk(tmp_path):
    path = str(tmp_path / "res.json")
    s1 = ResolutionStore(path=path)
    s1.resolve(make_alert())

    s2 = ResolutionStore(path=path)
    assert s2.is_resolved("pipe_a", "error_rate") is True


def test_clear_removes_all(store):
    store.resolve(make_alert())
    store.clear()
    assert store.all() == []
    assert store.is_resolved("pipe_a", "error_rate") is False


def test_filter_unresolved_excludes_resolved(store):
    alerts = [
        make_alert(pipeline="pipe_a", metric="error_rate"),
        make_alert(pipeline="pipe_b", metric="duration"),
    ]
    store.resolve(alerts[0])
    result = store.filter_unresolved(alerts)
    assert len(result) == 1
    assert result[0].pipeline == "pipe_b"


def test_filter_unresolved_returns_all_when_none_resolved(store):
    alerts = [
        make_alert(pipeline="pipe_a", metric="error_rate"),
        make_alert(pipeline="pipe_b", metric="duration"),
    ]
    result = store.filter_unresolved(alerts)
    assert len(result) == 2


def test_resolution_entry_from_alert_fields():
    alert = make_alert(pipeline="x", metric="row_count")
    entry = ResolutionEntry.from_alert(alert, note="ok")
    assert entry.pipeline == "x"
    assert entry.metric == "row_count"
    assert entry.note == "ok"
    assert entry.resolved_at != ""
