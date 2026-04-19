import pytest
from datetime import datetime, timedelta
from pipewatch.checker import Alert
from pipewatch.escalator import EscalationRule, EscalationStore


@pytest.fixture
def alert():
    return Alert(pipeline="orders", metric="error_rate", value=0.15, threshold=0.1)


@pytest.fixture
def store():
    s = EscalationStore()
    s.add_rule(EscalationRule(pipeline="orders", metric="error_rate", repeat_window_minutes=30, max_escalations=3))
    return s


def test_first_occurrence_not_escalated(store, alert):
    now = datetime.utcnow()
    assert store.record(alert, now=now) is False


def test_escalates_at_max_occurrences(store, alert):
    now = datetime.utcnow()
    store.record(alert, now=now)
    store.record(alert, now=now + timedelta(minutes=5))
    result = store.record(alert, now=now + timedelta(minutes=10))
    assert result is True


def test_no_escalation_below_max(store, alert):
    now = datetime.utcnow()
    store.record(alert, now=now)
    result = store.record(alert, now=now + timedelta(minutes=5))
    assert result is False


def test_resets_after_window_expires(store, alert):
    now = datetime.utcnow()
    for _ in range(3):
        store.record(alert, now=now)
    expired = now + timedelta(minutes=31)
    assert store.record(alert, now=expired) is False


def test_no_rule_returns_false(alert):
    s = EscalationStore()
    assert s.record(alert) is False


def test_clear_resets_records(store, alert):
    now = datetime.utcnow()
    store.record(alert, now=now)
    store.record(alert, now=now + timedelta(minutes=5))
    store.clear()
    assert store.record(alert, now=now + timedelta(minutes=6)) is False


def test_different_pipeline_not_matched(store):
    other = Alert(pipeline="shipments", metric="error_rate", value=0.2, threshold=0.1)
    assert store.record(other) is False
