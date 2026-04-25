import pytest
from pipewatch.checker import Alert
from pipewatch.ranker import AlertRanker, RankedAlert, SEVERITY_WEIGHTS, METRIC_WEIGHTS


@pytest.fixture
def ranker():
    return AlertRanker()


@pytest.fixture
def mixed_alerts():
    return [
        Alert(pipeline="p1", metric="error_rate", value=0.2, threshold=0.05, severity="critical"),
        Alert(pipeline="p2", metric="row_count", value=50, threshold=100, severity="info"),
        Alert(pipeline="p3", metric="duration", value=400, threshold=300, severity="warning"),
        Alert(pipeline="p4", metric="error_rate", value=0.1, threshold=0.05, severity="warning"),
    ]


def test_rank_returns_ranked_alerts(ranker, mixed_alerts):
    ranked = ranker.rank(mixed_alerts)
    assert len(ranked) == 4
    assert all(isinstance(r, RankedAlert) for r in ranked)


def test_rank_order_descending_by_score(ranker, mixed_alerts):
    ranked = ranker.rank(mixed_alerts)
    scores = [r.score for r in ranked]
    assert scores == sorted(scores, reverse=True)


def test_rank_assigns_sequential_ranks(ranker, mixed_alerts):
    ranked = ranker.rank(mixed_alerts)
    assert [r.rank for r in ranked] == list(range(1, len(mixed_alerts) + 1))


def test_critical_error_rate_is_highest(ranker, mixed_alerts):
    ranked = ranker.rank(mixed_alerts)
    top = ranked[0]
    assert top.alert.pipeline == "p1"
    assert top.alert.metric == "error_rate"
    assert top.alert.severity == "critical"


def test_info_row_count_is_lowest(ranker, mixed_alerts):
    ranked = ranker.rank(mixed_alerts)
    bottom = ranked[-1]
    assert bottom.alert.metric == "row_count"
    assert bottom.alert.severity == "info"


def test_top_limits_results(ranker, mixed_alerts):
    ranked = ranker.top(mixed_alerts, n=2)
    assert len(ranked) == 2
    assert ranked[0].rank == 1
    assert ranked[1].rank == 2


def test_top_on_empty_alerts(ranker):
    ranked = ranker.top([], n=5)
    assert ranked == []


def test_custom_severity_weights():
    custom_ranker = AlertRanker(severity_weights={"critical": 10.0, "warning": 1.0, "info": 0.1})
    alerts = [
        Alert(pipeline="a", metric="duration", value=500, threshold=300, severity="warning"),
        Alert(pipeline="b", metric="duration", value=500, threshold=300, severity="critical"),
    ]
    ranked = custom_ranker.rank(alerts)
    assert ranked[0].alert.severity == "critical"


def test_ranked_alert_str(ranker):
    alert = Alert(pipeline="x", metric="error_rate", value=0.1, threshold=0.05, severity="critical")
    ranked = ranker.rank([alert])
    result = str(ranked[0])
    assert "Rank #1" in result
    assert "x/error_rate" in result


def test_reason_contains_severity_and_metric(ranker):
    alert = Alert(pipeline="z", metric="row_count", value=10, threshold=100, severity="info")
    ranked = ranker.rank([alert])
    assert "severity=info" in ranked[0].reason
    assert "metric=row_count" in ranked[0].reason
