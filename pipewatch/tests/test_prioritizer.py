import pytest
from pipewatch.checker import Alert
from pipewatch.prioritizer import AlertPrioritizer, PriorityRule, PrioritizedAlert


@pytest.fixture
def critical_alert():
    return Alert(pipeline="payments", metric="error_rate", value=0.9, threshold=0.1, severity="critical")


@pytest.fixture
def warning_alert():
    return Alert(pipeline="inventory", metric="duration", value=300, threshold=120, severity="warning")


@pytest.fixture
def low_alert():
    return Alert(pipeline="reports", metric="row_count", value=5, threshold=10, severity="info")


def test_default_critical_severity_gets_critical_priority(critical_alert):
    prioritizer = AlertPrioritizer()
    result = prioritizer.prioritize([critical_alert])
    assert result[0].priority == "critical"


def test_default_warning_severity_gets_medium_priority(warning_alert):
    prioritizer = AlertPrioritizer()
    result = prioritizer.prioritize([warning_alert])
    assert result[0].priority == "medium"


def test_unknown_severity_gets_low_priority(low_alert):
    prioritizer = AlertPrioritizer()
    result = prioritizer.prioritize([low_alert])
    assert result[0].priority == "low"


def test_rule_overrides_default_priority(warning_alert):
    rule = PriorityRule(severity="warning", pipeline="inventory", priority="high")
    prioritizer = AlertPrioritizer(rules=[rule])
    result = prioritizer.prioritize([warning_alert])
    assert result[0].priority == "high"


def test_rule_does_not_match_wrong_pipeline(warning_alert):
    rule = PriorityRule(severity="warning", pipeline="payments", priority="high")
    prioritizer = AlertPrioritizer(rules=[rule])
    result = prioritizer.prioritize([warning_alert])
    assert result[0].priority == "medium"


def test_prioritize_sorts_by_score_descending(critical_alert, warning_alert, low_alert):
    prioritizer = AlertPrioritizer()
    alerts = [low_alert, warning_alert, critical_alert]
    result = prioritizer.prioritize(alerts)
    scores = [r.score for r in result]
    assert scores == sorted(scores, reverse=True)


def test_top_returns_limited_results(critical_alert, warning_alert, low_alert):
    prioritizer = AlertPrioritizer()
    result = prioritizer.top([critical_alert, warning_alert, low_alert], n=2)
    assert len(result) == 2
    assert result[0].priority == "critical"


def test_group_by_priority_buckets_correctly(critical_alert, warning_alert):
    prioritizer = AlertPrioritizer()
    groups = prioritizer.group_by_priority([critical_alert, warning_alert])
    assert len(groups["critical"]) == 1
    assert len(groups["medium"]) == 1


def test_prioritized_alert_str(critical_alert):
    prioritizer = AlertPrioritizer()
    result = prioritizer.prioritize([critical_alert])
    assert "CRITICAL" in str(result[0])


def test_add_rule_dynamically(warning_alert):
    prioritizer = AlertPrioritizer()
    prioritizer.add_rule(PriorityRule(severity="warning", metric="duration", priority="critical"))
    result = prioritizer.prioritize([warning_alert])
    assert result[0].priority == "critical"
