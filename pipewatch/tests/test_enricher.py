"""Tests for pipewatch.enricher."""

import pytest

from pipewatch.checker import Alert
from pipewatch.enricher import AlertEnricher, EnrichmentRule, EnrichedAlert


@pytest.fixture
def alert_duration() -> Alert:
    return Alert(pipeline="etl_sales", metric="duration", value=120.0, threshold=60.0, severity="warning")


@pytest.fixture
def alert_errors() -> Alert:
    return Alert(pipeline="etl_inventory", metric="error_rate", value=0.15, threshold=0.05, severity="critical")


@pytest.fixture
def enricher() -> AlertEnricher:
    e = AlertEnricher()
    e.add_rule(EnrichmentRule(pipeline="etl_sales", metric="duration", tags={"team": "analytics"}, note="Check slow query"))
    e.add_rule(EnrichmentRule(pipeline="*", metric="error_rate", tags={"oncall": "data-eng"}))
    return e


def test_enrich_attaches_matching_tags(enricher, alert_duration):
    results = enricher.enrich([alert_duration])
    assert len(results) == 1
    assert results[0].tags["team"] == "analytics"


def test_enrich_attaches_note(enricher, alert_duration):
    results = enricher.enrich([alert_duration])
    assert results[0].note == "Check slow query"


def test_wildcard_pipeline_matches_any(enricher, alert_errors):
    results = enricher.enrich([alert_errors])
    assert results[0].tags.get("oncall") == "data-eng"


def test_no_matching_rule_leaves_empty_tags(alert_duration):
    e = AlertEnricher()
    results = e.enrich([alert_duration])
    assert results[0].tags == {}
    assert results[0].note is None


def test_multiple_rules_merge_tags(alert_errors):
    e = AlertEnricher()
    e.add_rule(EnrichmentRule(pipeline="*", metric="*", tags={"env": "prod"}))
    e.add_rule(EnrichmentRule(pipeline="etl_inventory", metric="error_rate", tags={"priority": "high"}))
    results = e.enrich([alert_errors])
    assert results[0].tags["env"] == "prod"
    assert results[0].tags["priority"] == "high"


def test_first_matching_note_wins():
    alert = Alert(pipeline="pipe_a", metric="duration", value=10.0, threshold=5.0, severity="warning")
    e = AlertEnricher()
    e.add_rule(EnrichmentRule(pipeline="*", metric="*", note="generic note"))
    e.add_rule(EnrichmentRule(pipeline="pipe_a", metric="duration", note="specific note"))
    results = e.enrich([alert])
    assert results[0].note == "generic note"


def test_str_includes_tags_and_note(enricher, alert_duration):
    results = enricher.enrich([alert_duration])
    text = str(results[0])
    assert "team=analytics" in text
    assert "Check slow query" in text


def test_empty_alert_list_returns_empty(enricher):
    assert enricher.enrich([]) == []
