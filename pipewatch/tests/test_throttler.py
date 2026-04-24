"""Tests for the alert throttler module."""

import time
import pytest

from pipewatch.checker import Alert
from pipewatch.throttler import ThrottleRule, ThrottleRecord, ThrottlerStore


@pytest.fixture
def alert():
    return Alert(pipeline="etl_main", metric="error_rate", value=0.15, threshold=0.1, severity="warning")


@pytest.fixture
def store(tmp_path):
    return ThrottlerStore(path=str(tmp_path / "throttle.json"))


def test_throttle_rule_matches_exact(alert):
    rule = ThrottleRule(pipeline="etl_main", metric="error_rate", interval_seconds=60)
    assert rule.matches(alert)


def test_throttle_rule_wildcard_pipeline(alert):
    rule = ThrottleRule(pipeline="*", metric="error_rate", interval_seconds=60)
    assert rule.matches(alert)


def test_throttle_rule_wildcard_metric(alert):
    rule = ThrottleRule(pipeline="etl_main", metric="*", interval_seconds=60)
    assert rule.matches(alert)


def test_throttle_rule_no_match_wrong_pipeline(alert):
    rule = ThrottleRule(pipeline="other_pipeline", metric="error_rate", interval_seconds=60)
    assert not rule.matches(alert)


def test_no_rule_means_not_throttled(store, alert):
    assert not store.is_throttled(alert)


def test_first_alert_not_throttled_no_record(store, alert):
    rule = ThrottleRule(pipeline="etl_main", metric="error_rate", interval_seconds=60)
    store.add_rule(rule)
    # No record yet — should not be throttled
    assert not store.is_throttled(alert)


def test_alert_throttled_after_record(store, alert):
    rule = ThrottleRule(pipeline="etl_main", metric="error_rate", interval_seconds=300)
    store.add_rule(rule)
    store.record(alert)
    assert store.is_throttled(alert)


def test_alert_not_throttled_after_interval_expires(store, alert):
    rule = ThrottleRule(pipeline="etl_main", metric="error_rate", interval_seconds=1)
    store.add_rule(rule)
    store.record(alert)
    time.sleep(1.05)
    assert not store.is_throttled(alert)


def test_clear_removes_state(store, alert):
    rule = ThrottleRule(pipeline="etl_main", metric="error_rate", interval_seconds=300)
    store.add_rule(rule)
    store.record(alert)
    store.clear()
    # After clear, rules are gone so alert is not throttled
    assert not store.is_throttled(alert)


def test_throttle_record_persists_to_disk(tmp_path, alert):
    path = str(tmp_path / "throttle.json")
    s1 = ThrottlerStore(path=path)
    rule = ThrottleRule(pipeline="etl_main", metric="error_rate", interval_seconds=300)
    s1.add_rule(rule)
    s1.record(alert)

    s2 = ThrottlerStore(path=path)
    s2.add_rule(rule)
    assert s2.is_throttled(alert)
