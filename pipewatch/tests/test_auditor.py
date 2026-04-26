"""Tests for pipewatch.auditor."""

import json
import os
import pytest

from pipewatch.checker import Alert
from pipewatch.auditor import AuditEntry, AuditStore


@pytest.fixture
def alert():
    return Alert(pipeline="orders", metric="error_rate", severity="critical", value=0.15, threshold=0.05)


@pytest.fixture
def store(tmp_path):
    return AuditStore(path=str(tmp_path / "audit.json"))


def test_empty_store_returns_no_entries(store):
    assert store.all() == []


def test_record_adds_entry(store, alert):
    entry = store.record(alert, outcome="notified")
    assert entry.pipeline == "orders"
    assert entry.metric == "error_rate"
    assert entry.severity == "critical"
    assert entry.outcome == "notified"
    assert len(store.all()) == 1


def test_record_persists_to_disk(tmp_path, alert):
    path = str(tmp_path / "audit.json")
    store = AuditStore(path=path)
    store.record(alert, outcome="suppressed")

    store2 = AuditStore(path=path)
    entries = store2.all()
    assert len(entries) == 1
    assert entries[0].outcome == "suppressed"


def test_for_pipeline_filters_correctly(store, alert):
    store.record(alert, outcome="notified")
    other = Alert(pipeline="inventory", metric="row_count", severity="warning", value=10, threshold=100)
    store.record(other, outcome="silenced")

    results = store.for_pipeline("orders")
    assert len(results) == 1
    assert results[0].pipeline == "orders"


def test_for_outcome_filters_correctly(store, alert):
    store.record(alert, outcome="notified")
    store.record(alert, outcome="deduplicated")
    store.record(alert, outcome="notified")

    notified = store.for_outcome("notified")
    assert len(notified) == 2

    deduped = store.for_outcome("deduplicated")
    assert len(deduped) == 1


def test_clear_removes_all_entries(store, alert):
    store.record(alert, outcome="notified")
    store.record(alert, outcome="suppressed")
    store.clear()
    assert store.all() == []


def test_entry_timestamp_is_set(store, alert):
    entry = store.record(alert, outcome="notified")
    assert entry.timestamp is not None
    assert "T" in entry.timestamp  # ISO 8601 format


def test_entry_roundtrip_via_dict(alert):
    entry = AuditEntry.from_alert(alert, outcome="notified")
    restored = AuditEntry.from_dict(entry.to_dict())
    assert restored.pipeline == entry.pipeline
    assert restored.outcome == entry.outcome
    assert restored.timestamp == entry.timestamp
