import pytest
from unittest.mock import MagicMock
from pipewatch.checker import Alert
from pipewatch.router import AlertRouter, RoutingRule


@pytest.fixture
def critical_alert():
    return Alert(pipeline="pipe_a", metric="duration", value=999, threshold=100, severity="critical")


@pytest.fixture
def warning_alert():
    return Alert(pipeline="pipe_b", metric="error_rate", value=0.5, threshold=0.1, severity="warning")


def test_route_matches_severity(critical_alert, warning_alert):
    notifier = MagicMock()
    rule = RoutingRule(name="crit-only", severities=["critical"], notifier=notifier)
    router = AlertRouter(rules=[rule], fallback=None)
    router.route([critical_alert, warning_alert])
    sent = notifier.send.call_args[0][0]
    assert critical_alert in sent
    assert warning_alert not in sent


def test_route_matches_pipeline(critical_alert, warning_alert):
    notifier = MagicMock()
    rule = RoutingRule(name="pipe-a", pipelines=["pipe_a"], notifier=notifier)
    router = AlertRouter(rules=[rule], fallback=None)
    router.route([critical_alert, warning_alert])
    sent = notifier.send.call_args[0][0]
    assert critical_alert in sent
    assert warning_alert not in sent


def test_unmatched_alerts_go_to_fallback(warning_alert):
    fallback = MagicMock()
    rule = RoutingRule(name="crit-only", severities=["critical"], notifier=MagicMock())
    router = AlertRouter(rules=[rule], fallback=fallback)
    router.route([warning_alert])
    fallback.send.assert_called_once()
    assert warning_alert in fallback.send.call_args[0][0]


def test_no_fallback_unmatched_alerts_silently_dropped(warning_alert):
    router = AlertRouter(rules=[], fallback=None)
    router.route([warning_alert])  # should not raise


def test_empty_alert_list_no_calls():
    notifier = MagicMock()
    fallback = MagicMock()
    rule = RoutingRule(name="any", notifier=notifier)
    router = AlertRouter(rules=[rule], fallback=fallback)
    router.route([])
    notifier.send.assert_not_called()
    fallback.send.assert_not_called()


def test_rule_no_filters_matches_all(critical_alert, warning_alert):
    notifier = MagicMock()
    rule = RoutingRule(name="catch-all", notifier=notifier)
    router = AlertRouter(rules=[rule], fallback=None)
    router.route([critical_alert, warning_alert])
    sent = notifier.send.call_args[0][0]
    assert critical_alert in sent
    assert warning_alert in sent
