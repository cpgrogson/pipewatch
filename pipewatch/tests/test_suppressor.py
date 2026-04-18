"""Tests for alert suppression logic."""
import pytest
from datetime import datetime, timedelta
from pipewatch.checker import Alert
from pipewatch.suppressor import SuppressionRule, SuppressionStore


@pytest.fixture
def alert():
    return Alert(pipeline="etl_main", metric="error_rate", value=0.15, threshold=0.1, severity="warning")


@pytest.fixture
def store():
    s = SuppressionStore()
    s.add_rule(SuppressionRule(pipeline="etl_main", metric="error_rate", min_occurrences=3, window_seconds=300))
    return s


def test_suppressed_below_min_occurrences(store, alert):
    store.record(alert)
    store.record(alert)
    assert store.is_suppressed(alert) is True


def test_not_suppressed_at_min_occurrences(store, alert):
    for _ in range(3):
        store.record(alert)
    assert store.is_suppressed(alert) is False


def test_no_rule_means_not_suppressed(alert):
    store = SuppressionStore()
    assert store.is_suppressed(alert) is False


def test_wildcard_pipeline_matches(alert):
    store = SuppressionStore()
    store.add_rule(SuppressionRule(pipeline="*", metric="error_rate", min_occurrences=2, window_seconds=300))
    store.record(alert)
    assert store.is_suppressed(alert) is True


def test_old_records_outside_window_ignored(store, alert):
    old_time = datetime.utcnow() - timedelta(seconds=400)
    key = f"{alert.pipeline}:{alert.metric}"
    store._history[key] = [old_time, old_time, old_time]
    assert store.is_suppressed(alert) is True


def test_filter_alerts_returns_unsuppressed(store, alert):
    alerts = [alert] * 2
    result = store.filter_alerts(alerts)
    assert result == []


def test_filter_alerts_passes_after_threshold(store, alert):
    alerts = [alert] * 3
    result = store.filter_alerts(alerts)
    assert len(result) == 1
