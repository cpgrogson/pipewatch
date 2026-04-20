"""Tests for the AlertTagger auto-tagging module."""

import pytest
from pipewatch.checker import Alert
from pipewatch.tagger import TagRule, TaggedAlert, AlertTagger


@pytest.fixture
def tagger() -> AlertTagger:
    t = AlertTagger()
    t.add_rule(TagRule(pipeline="sales_etl", metric="error_rate", tags=["critical", "errors"]))
    t.add_rule(TagRule(pipeline="*", metric="duration", tags=["perf"]))
    t.add_rule(TagRule(pipeline="inventory", metric="*", tags=["inventory-team"]))
    return t


@pytest.fixture
def alert_error() -> Alert:
    return Alert(pipeline="sales_etl", metric="error_rate", value=0.15, threshold=0.05, severity="critical")


@pytest.fixture
def alert_duration() -> Alert:
    return Alert(pipeline="orders_etl", metric="duration", value=300, threshold=120, severity="warning")


@pytest.fixture
def alert_inventory() -> Alert:
    return Alert(pipeline="inventory", metric="rows_processed", value=0, threshold=100, severity="warning")


def test_tag_rule_matches_exact(alert_error):
    rule = TagRule(pipeline="sales_etl", metric="error_rate", tags=["critical"])
    assert rule.matches(alert_error)


def test_tag_rule_no_match_wrong_pipeline(alert_error):
    rule = TagRule(pipeline="other_etl", metric="error_rate", tags=["critical"])
    assert not rule.matches(alert_error)


def test_tag_rule_wildcard_pipeline_matches_any(alert_duration):
    rule = TagRule(pipeline="*", metric="duration", tags=["perf"])
    assert rule.matches(alert_duration)


def test_tag_rule_wildcard_metric_matches_any(alert_inventory):
    rule = TagRule(pipeline="inventory", metric="*", tags=["inventory-team"])
    assert rule.matches(alert_inventory)


def test_tagger_applies_matching_tags(tagger, alert_error):
    result = tagger.tag(alert_error)
    assert isinstance(result, TaggedAlert)
    assert "critical" in result.tags
    assert "errors" in result.tags


def test_tagger_wildcard_duration_tag(tagger, alert_duration):
    result = tagger.tag(alert_duration)
    assert "perf" in result.tags


def test_tagger_no_matching_rule_returns_empty_tags(tagger):
    alert = Alert(pipeline="unknown", metric="rows", value=0, threshold=10, severity="warning")
    result = tagger.tag(alert)
    assert result.tags == []


def test_tagger_tag_all_returns_list(tagger, alert_error, alert_duration):
    results = tagger.tag_all([alert_error, alert_duration])
    assert len(results) == 2
    assert all(isinstance(r, TaggedAlert) for r in results)


def test_tagged_alert_str_includes_tags(tagger, alert_error):
    result = tagger.tag(alert_error)
    s = str(result)
    assert "critical" in s or "errors" in s


def test_tagger_clear_removes_rules(tagger):
    tagger.clear()
    assert tagger.rules() == []


def test_no_duplicate_tags_from_multiple_rules():
    t = AlertTagger()
    t.add_rule(TagRule(pipeline="*", metric="*", tags=["shared"]))
    t.add_rule(TagRule(pipeline="sales_etl", metric="*", tags=["shared", "extra"]))
    alert = Alert(pipeline="sales_etl", metric="rows", value=0, threshold=5, severity="warning")
    result = t.tag(alert)
    assert result.tags.count("shared") == 1
    assert "extra" in result.tags
