import pytest
from pipewatch.ratelimiter import RateLimiterStore, RateLimitRule
from pipewatch.checker import Alert


@pytest.fixture
def store(tmp_path):
    return RateLimiterStore(path=str(tmp_path / "ratelimits.json"))


def test_no_rule_means_not_limited(store):
    assert store.is_rate_limited("pipeline_a", "error_rate") is False


def test_first_alert_not_limited(store):
    store.add_rule(RateLimitRule(pipeline="pipeline_a", metric="error_rate", max_alerts=2, window_seconds=60))
    assert store.is_rate_limited("pipeline_a", "error_rate") is False


def test_alert_limited_after_max(store):
    store.add_rule(RateLimitRule(pipeline="pipeline_a", metric="error_rate", max_alerts=2, window_seconds=60))
    assert store.is_rate_limited("pipeline_a", "error_rate") is False
    assert store.is_rate_limited("pipeline_a", "error_rate") is False
    assert store.is_rate_limited("pipeline_a", "error_rate") is True


def test_wildcard_pipeline_matches(store):
    store.add_rule(RateLimitRule(pipeline="*", metric="duration", max_alerts=1, window_seconds=60))
    assert store.is_rate_limited("any_pipeline", "duration") is False
    assert store.is_rate_limited("any_pipeline", "duration") is True


def test_wildcard_metric_matches(store):
    store.add_rule(RateLimitRule(pipeline="etl_main", metric="*", max_alerts=1, window_seconds=60))
    assert store.is_rate_limited("etl_main", "rows_processed") is False
    assert store.is_rate_limited("etl_main", "rows_processed") is True


def test_list_rules(store):
    store.add_rule(RateLimitRule(pipeline="p1", metric="m1", max_alerts=5, window_seconds=300))
    store.add_rule(RateLimitRule(pipeline="p2", metric="m2", max_alerts=1, window_seconds=60))
    rules = store.list_rules()
    assert len(rules) == 2


def test_clear_removes_rules(store):
    store.add_rule(RateLimitRule(pipeline="p1", metric="m1"))
    store.clear()
    assert store.list_rules() == []
    assert store.is_rate_limited("p1", "m1") is False


def test_persists_rules(tmp_path):
    path = str(tmp_path / "rl.json")
    s1 = RateLimiterStore(path=path)
    s1.add_rule(RateLimitRule(pipeline="etl", metric="error_rate", max_alerts=3, window_seconds=120))
    s2 = RateLimiterStore(path=path)
    rules = s2.list_rules()
    assert len(rules) == 1
    assert rules[0].pipeline == "etl"
    assert rules[0].max_alerts == 3
