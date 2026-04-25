"""Tests for pipewatch.scorer — AlertScorer and ScoredAlert."""

import pytest
from pipewatch.checker import Alert
from pipewatch.scorer import AlertScorer, ScoredAlert, DEFAULT_SEVERITY_WEIGHTS, DEFAULT_METRIC_WEIGHTS


@pytest.fixture
def scorer() -> AlertScorer:
    return AlertScorer()


def make_alert(pipeline="pipe_a", metric="error_rate", severity="critical", message="bad") -> Alert:
    return Alert(pipeline=pipeline, metric=metric, severity=severity, message=message)


def test_score_returns_scored_alert(scorer):
    alert = make_alert()
    result = scorer.score(alert)
    assert isinstance(result, ScoredAlert)
    assert result.alert is alert


def test_score_critical_error_rate_is_highest(scorer):
    alert = make_alert(metric="error_rate", severity="critical")
    result = scorer.score(alert)
    expected = DEFAULT_SEVERITY_WEIGHTS["critical"] * DEFAULT_METRIC_WEIGHTS["error_rate"]
    assert result.score == pytest.approx(expected)


def test_score_info_row_count_is_low(scorer):
    alert = make_alert(metric="row_count", severity="info")
    result = scorer.score(alert)
    expected = DEFAULT_SEVERITY_WEIGHTS["info"] * DEFAULT_METRIC_WEIGHTS["row_count"]
    assert result.score == pytest.approx(expected)


def test_unknown_severity_defaults_to_one(scorer):
    alert = make_alert(severity="unknown_level")
    result = scorer.score(alert)
    metric_w = DEFAULT_METRIC_WEIGHTS.get("error_rate", 1.0)
    assert result.score == pytest.approx(1.0 * metric_w)


def test_unknown_metric_defaults_to_one(scorer):
    alert = make_alert(metric="latency", severity="warning")
    result = scorer.score(alert)
    severity_w = DEFAULT_SEVERITY_WEIGHTS["warning"]
    assert result.score == pytest.approx(severity_w * 1.0)


def test_score_all_returns_sorted_descending(scorer):
    alerts = [
        make_alert(metric="row_count", severity="info"),
        make_alert(metric="error_rate", severity="critical"),
        make_alert(metric="duration", severity="warning"),
    ]
    results = scorer.score_all(alerts)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_top_returns_at_most_n(scorer):
    alerts = [make_alert(metric="error_rate", severity="critical") for _ in range(10)]
    results = scorer.top(alerts, n=3)
    assert len(results) == 3


def test_top_default_n_is_five(scorer):
    alerts = [make_alert() for _ in range(10)]
    results = scorer.top(alerts)
    assert len(results) == 5


def test_scored_alert_str(scorer):
    alert = make_alert(pipeline="etl_main", metric="duration", severity="warning")
    sa = scorer.score(alert)
    s = str(sa)
    assert "etl_main" in s
    assert "duration" in s
    assert "warning" in s
    assert "score=" in s


def test_custom_weights_applied():
    custom_scorer = AlertScorer(
        severity_weights={"critical": 100.0, "warning": 1.0, "info": 0.1},
        metric_weights={"error_rate": 1.0, "duration": 1.0, "row_count": 1.0},
    )
    alert = make_alert(metric="error_rate", severity="critical")
    result = custom_scorer.score(alert)
    assert result.score == pytest.approx(100.0)
