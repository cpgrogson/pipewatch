"""Tests for the alert grouper module."""
import pytest
from pipewatch.checker import Alert
from pipewatch.grouper import GroupRule, AlertGroup, AlertGrouper


@pytest.fixture
def critical_alert():
    return Alert(pipeline="orders", metric="error_rate", value=0.15, threshold=0.1, severity="critical")


@pytest.fixture
def warning_alert():
    return Alert(pipeline="inventory", metric="duration", value=320.0, threshold=300.0, severity="warning")


@pytest.fixture
def another_critical():
    return Alert(pipeline="payments", metric="error_rate", value=0.2, threshold=0.05, severity="critical")


def test_group_rule_matches_exact(critical_alert):
    rule = GroupRule(group_name="errors", pipeline="orders", metric="error_rate", severity="critical")
    assert rule.matches(critical_alert)


def test_group_rule_no_match_wrong_pipeline(critical_alert):
    rule = GroupRule(group_name="errors", pipeline="payments", metric="error_rate")
    assert not rule.matches(critical_alert)


def test_group_rule_wildcard_pipeline(warning_alert):
    rule = GroupRule(group_name="slow", pipeline="*", metric="duration")
    assert rule.matches(warning_alert)


def test_group_rule_wildcard_all(critical_alert):
    rule = GroupRule(group_name="all", pipeline="*", metric="*", severity="*")
    assert rule.matches(critical_alert)


def test_grouper_assigns_correct_group(critical_alert, warning_alert):
    grouper = AlertGrouper()
    grouper.add_rule(GroupRule(group_name="errors", metric="error_rate"))
    grouper.add_rule(GroupRule(group_name="slow", metric="duration"))
    groups = grouper.group([critical_alert, warning_alert])
    assert "errors" in groups
    assert "slow" in groups
    assert critical_alert in groups["errors"].alerts
    assert warning_alert in groups["slow"].alerts


def test_grouper_fallback_for_unmatched(critical_alert):
    grouper = AlertGrouper(fallback="misc")
    groups = grouper.group([critical_alert])
    assert "misc" in groups
    assert critical_alert in groups["misc"].alerts


def test_grouper_multiple_alerts_in_same_group(critical_alert, another_critical):
    grouper = AlertGrouper()
    grouper.add_rule(GroupRule(group_name="errors", metric="error_rate", severity="critical"))
    groups = grouper.group([critical_alert, another_critical])
    assert groups["errors"].size() == 2


def test_alert_group_summary(critical_alert, another_critical):
    group = AlertGroup(name="errors", alerts=[critical_alert, another_critical])
    summary = group.summary()
    assert "errors" in summary
    assert "2" in summary


def test_alert_group_pipelines(critical_alert, another_critical):
    group = AlertGroup(name="errors", alerts=[critical_alert, another_critical])
    pipelines = group.pipelines()
    assert "orders" in pipelines
    assert "payments" in pipelines


def test_alert_group_severities(critical_alert, warning_alert):
    group = AlertGroup(name="mixed", alerts=[critical_alert, warning_alert])
    severities = group.severities()
    assert "critical" in severities
    assert "warning" in severities
