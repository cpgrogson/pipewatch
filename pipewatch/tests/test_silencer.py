"""Tests for the silencer module."""
import pytest
from datetime import datetime, timedelta
from pipewatch.checker import Alert
from pipewatch.silencer import SilenceRule, SilenceStore, silence_for


@pytest.fixture
def alert():
    return Alert(pipeline="etl_sales", metric="error_rate", value=0.15, threshold=0.1, severity="warning")


def test_silence_rule_matches_pipeline_and_metric(alert):
    rule = SilenceRule(pipeline="etl_sales", metric="error_rate")
    assert rule.matches(alert)


def test_silence_rule_no_match_wrong_pipeline(alert):
    rule = SilenceRule(pipeline="other_pipeline", metric="error_rate")
    assert not rule.matches(alert)


def test_silence_rule_no_match_wrong_metric(alert):
    rule = SilenceRule(pipeline="etl_sales", metric="duration")
    assert not rule.matches(alert)


def test_silence_rule_wildcard_matches_any(alert):
    rule = SilenceRule()  # no pipeline or metric filter
    assert rule.matches(alert)


def test_expired_rule_does_not_match(alert):
    past = datetime.utcnow() - timedelta(hours=1)
    rule = SilenceRule(pipeline="etl_sales", metric="error_rate", until=past)
    assert not rule.matches(alert)
    assert not rule.is_active()


def test_active_rule_within_time(alert):
    future = datetime.utcnow() + timedelta(hours=2)
    rule = SilenceRule(pipeline="etl_sales", metric="error_rate", until=future)
    assert rule.is_active()
    assert rule.matches(alert)


def test_store_filters_silenced_alerts():
    store = SilenceStore()
    alerts = [
        Alert(pipeline="etl_sales", metric="error_rate", value=0.2, threshold=0.1, severity="warning"),
        Alert(pipeline="etl_orders", metric="duration", value=300, threshold=120, severity="critical"),
    ]
    store.add(SilenceRule(pipeline="etl_sales", metric="error_rate"))
    result = store.filter_alerts(alerts)
    assert len(result) == 1
    assert result[0].pipeline == "etl_orders"


def test_store_remove_expired():
    store = SilenceStore()
    past = datetime.utcnow() - timedelta(hours=1)
    future = datetime.utcnow() + timedelta(hours=1)
    store.add(SilenceRule(until=past))
    store.add(SilenceRule(until=future))
    removed = store.remove_expired()
    assert removed == 1
    assert len(store.rules) == 1


def test_silence_for_helper_creates_rule():
    rule = silence_for("my_pipeline", "row_count", hours=2.0, reason="maintenance")
    assert rule.pipeline == "my_pipeline"
    assert rule.metric == "row_count"
    assert rule.reason == "maintenance"
    assert rule.is_active()
