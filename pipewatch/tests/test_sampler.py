"""Tests for pipewatch.sampler."""

import pytest

from pipewatch.checker import Alert
from pipewatch.sampler import AlertSampler, SampleRule, SampledResult


@pytest.fixture
def alert() -> Alert:
    return Alert(pipeline="etl_main", metric="error_rate", value=0.12, threshold=0.05, severity="critical")


def test_no_rules_keeps_all_alerts(alert):
    sampler = AlertSampler()
    result = sampler.sample([alert])
    assert len(result.kept) == 1
    assert len(result.dropped) == 0


def test_rate_1_keeps_alert(alert):
    sampler = AlertSampler(rules=[SampleRule(pipeline="*", metric="*", rate=1.0)])
    result = sampler.sample([alert])
    assert alert in result.kept


def test_rate_0_drops_alert(alert):
    sampler = AlertSampler(rules=[SampleRule(pipeline="*", metric="*", rate=0.0)])
    result = sampler.sample([alert])
    assert alert in result.dropped
    assert len(result.kept) == 0


def test_deterministic_sampling_stable(alert):
    rule = SampleRule(pipeline="etl_main", metric="error_rate", rate=0.5, seed="test-seed")
    sampler = AlertSampler(rules=[rule])
    result1 = sampler.sample([alert])
    result2 = sampler.sample([alert])
    assert len(result1.kept) == len(result2.kept)
    assert len(result1.dropped) == len(result2.dropped)


def test_deterministic_sampling_different_seeds_may_differ():
    a = Alert(pipeline="pipe", metric="rows", value=0, threshold=10, severity="warning")
    rule_a = SampleRule(pipeline="*", metric="*", rate=0.5, seed="seed-A")
    rule_b = SampleRule(pipeline="*", metric="*", rate=0.5, seed="seed-B")
    keep_a = rule_a.should_keep(a)
    keep_b = rule_b.should_keep(a)
    # They can differ; just assert both return booleans
    assert isinstance(keep_a, bool)
    assert isinstance(keep_b, bool)


def test_rule_matches_exact_pipeline_and_metric(alert):
    rule = SampleRule(pipeline="etl_main", metric="error_rate", rate=0.0)
    assert rule.matches(alert)


def test_rule_no_match_wrong_pipeline(alert):
    rule = SampleRule(pipeline="other_pipe", metric="error_rate", rate=0.0)
    assert not rule.matches(alert)


def test_rule_wildcard_pipeline_matches_any(alert):
    rule = SampleRule(pipeline="*", metric="error_rate", rate=0.0)
    assert rule.matches(alert)


def test_unmatched_alert_is_kept(alert):
    rule = SampleRule(pipeline="other_pipe", metric="error_rate", rate=0.0)
    sampler = AlertSampler(rules=[rule])
    result = sampler.sample([alert])
    assert alert in result.kept


def test_sampled_result_summary():
    kept = [Alert(pipeline="p", metric="m", value=1, threshold=0, severity="info")]
    dropped = [Alert(pipeline="p", metric="m", value=2, threshold=0, severity="info")]
    result = SampledResult(kept=kept, dropped=dropped)
    assert result.total == 2
    assert "2 alerts" in result.summary()
    assert "1 kept" in result.summary()
    assert "1 dropped" in result.summary()


def test_multiple_rules_first_match_wins():
    a = Alert(pipeline="pipe", metric="duration", value=999, threshold=100, severity="critical")
    r1 = SampleRule(pipeline="pipe", metric="duration", rate=0.0)  # drop
    r2 = SampleRule(pipeline="*", metric="*", rate=1.0)            # keep
    sampler = AlertSampler(rules=[r1, r2])
    result = sampler.sample([a])
    assert a in result.dropped
