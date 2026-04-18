"""Tests for alert deduplication logic."""

from datetime import datetime, timedelta

import pytest

from pipewatch.checker import Alert
from pipewatch.deduplicator import DeduplicationRule, DeduplicatorStore


@pytest.fixture
def alert():
    return Alert(pipeline="etl_main", metric="error_rate", value=0.15, threshold=0.10)


@pytest.fixture
def store():
    return DeduplicatorStore(rule=DeduplicationRule(cooldown_minutes=30))


def test_first_alert_not_duplicate(store, alert):
    now = datetime(2024, 1, 1, 12, 0, 0)
    assert store.is_duplicate(alert, now) is False


def test_alert_duplicate_within_cooldown(store, alert):
    now = datetime(2024, 1, 1, 12, 0, 0)
    store.record(alert, now)
    later = now + timedelta(minutes=10)
    assert store.is_duplicate(alert, later) is True


def test_alert_not_duplicate_after_cooldown(store, alert):
    now = datetime(2024, 1, 1, 12, 0, 0)
    store.record(alert, now)
    later = now + timedelta(minutes=31)
    assert store.is_duplicate(alert, later) is False


def test_different_pipelines_not_duplicate(store):
    now = datetime(2024, 1, 1, 12, 0, 0)
    a1 = Alert(pipeline="pipe_a", metric="error_rate", value=0.2, threshold=0.1)
    a2 = Alert(pipeline="pipe_b", metric="error_rate", value=0.2, threshold=0.1)
    store.record(a1, now)
    assert store.is_duplicate(a2, now) is False


def test_filter_alerts_removes_duplicates(store):
    now = datetime(2024, 1, 1, 12, 0, 0)
    alerts = [
        Alert(pipeline="etl", metric="error_rate", value=0.2, threshold=0.1),
        Alert(pipeline="etl", metric="error_rate", value=0.2, threshold=0.1),
    ]
    result = store.filter_alerts(alerts, now)
    assert len(result) == 1


def test_filter_alerts_passes_distinct(store):
    now = datetime(2024, 1, 1, 12, 0, 0)
    alerts = [
        Alert(pipeline="etl", metric="error_rate", value=0.2, threshold=0.1),
        Alert(pipeline="etl", metric="duration", value=500, threshold=300),
    ]
    result = store.filter_alerts(alerts, now)
    assert len(result) == 2


def test_clear_resets_seen(store, alert):
    now = datetime(2024, 1, 1, 12, 0, 0)
    store.record(alert, now)
    store.clear()
    assert store.is_duplicate(alert, now) is False
