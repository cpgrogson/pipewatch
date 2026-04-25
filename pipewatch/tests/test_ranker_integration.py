import pytest
from pipewatch.checker import Alert
from pipewatch.ranker import AlertRanker
from pipewatch.scorer import AlertScorer


@pytest.fixture
def alerts():
    return [
        Alert(pipeline="billing", metric="error_rate", value=0.25, threshold=0.05, severity="critical"),
        Alert(pipeline="billing", metric="duration", value=600, threshold=300, severity="critical"),
        Alert(pipeline="shipping", metric="row_count", value=5, threshold=100, severity="warning"),
        Alert(pipeline="auth", metric="error_rate", value=0.06, threshold=0.05, severity="info"),
    ]


def test_ranker_and_scorer_agree_on_top_alert(alerts):
    """Both ranker and scorer should identify critical error_rate as most severe."""
    ranker = AlertRanker()
    scorer = AlertScorer()

    ranked = ranker.rank(alerts)
    scored = scorer.score_all(alerts)

    top_ranked_metric = ranked[0].alert.metric
    top_scored_metric = max(scored, key=lambda s: s.score).alert.metric

    assert top_ranked_metric == "error_rate"
    assert top_scored_metric == "error_rate"


def test_ranker_preserves_all_alerts(alerts):
    ranker = AlertRanker()
    ranked = ranker.rank(alerts)
    assert len(ranked) == len(alerts)


def test_ranker_top_n_subset(alerts):
    ranker = AlertRanker()
    top2 = ranker.top(alerts, n=2)
    all_ranked = ranker.rank(alerts)
    assert top2[0].alert == all_ranked[0].alert
    assert top2[1].alert == all_ranked[1].alert


def test_ranker_stable_on_single_alert():
    ranker = AlertRanker()
    single = [Alert(pipeline="x", metric="duration", value=999, threshold=300, severity="warning")]
    ranked = ranker.rank(single)
    assert len(ranked) == 1
    assert ranked[0].rank == 1
