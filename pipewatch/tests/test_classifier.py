import pytest
from pipewatch.checker import Alert
from pipewatch.classifier import AlertClassifier, ClassificationRule, ClassifiedAlert


@pytest.fixture
def error_alert():
    return Alert(pipeline="ingest", metric="error_rate", value=0.15, threshold=0.05, severity="critical")


@pytest.fixture
def duration_alert():
    return Alert(pipeline="transform", metric="duration", value=300, threshold=120, severity="warning")


@pytest.fixture
def row_alert():
    return Alert(pipeline="export", metric="row_count", value=5, threshold=100, severity="warning")


@pytest.fixture
def classifier():
    return AlertClassifier()


def test_default_error_rate_classified_as_data_quality(classifier, error_alert):
    result = classifier.classify(error_alert)
    assert result.category == "data_quality"


def test_default_duration_classified_as_performance(classifier, duration_alert):
    result = classifier.classify(duration_alert)
    assert result.category == "performance"


def test_default_row_count_classified_as_volume(classifier, row_alert):
    result = classifier.classify(row_alert)
    assert result.category == "volume"


def test_unknown_metric_classified_as_unknown(classifier):
    alert = Alert(pipeline="ingest", metric="latency", value=999, threshold=100, severity="info")
    result = classifier.classify(alert)
    assert result.category == "unknown"


def test_custom_rule_overrides_default(error_alert):
    classifier = AlertClassifier()
    rule = ClassificationRule(pipeline="ingest", metric="error_rate", category="sla_breach", description="SLA violated")
    classifier.add_rule(rule)
    result = classifier.classify(error_alert)
    assert result.category == "sla_breach"
    assert result.description == "SLA violated"


def test_wildcard_pipeline_matches_any(duration_alert):
    classifier = AlertClassifier()
    rule = ClassificationRule(pipeline="*", metric="duration", category="timeout")
    classifier.add_rule(rule)
    result = classifier.classify(duration_alert)
    assert result.category == "timeout"


def test_wildcard_metric_matches_any(error_alert):
    classifier = AlertClassifier()
    rule = ClassificationRule(pipeline="ingest", metric="*", category="ingest_issue")
    classifier.add_rule(rule)
    result = classifier.classify(error_alert)
    assert result.category == "ingest_issue"


def test_classify_all_returns_list(classifier, error_alert, duration_alert, row_alert):
    results = classifier.classify_all([error_alert, duration_alert, row_alert])
    assert len(results) == 3
    assert all(isinstance(r, ClassifiedAlert) for r in results)


def test_group_by_category(classifier, error_alert, duration_alert, row_alert):
    groups = classifier.group_by_category([error_alert, duration_alert, row_alert])
    assert "data_quality" in groups
    assert "performance" in groups
    assert "volume" in groups
    assert len(groups["data_quality"]) == 1


def test_classified_alert_str_includes_category(classifier, error_alert):
    result = classifier.classify(error_alert)
    assert "[data_quality]" in str(result)


def test_classified_alert_str_includes_description():
    classifier = AlertClassifier()
    rule = ClassificationRule(pipeline="ingest", metric="error_rate", category="sla", description="SLA breach")
    classifier.add_rule(rule)
    alert = Alert(pipeline="ingest", metric="error_rate", value=0.2, threshold=0.1, severity="critical")
    result = classifier.classify(alert)
    assert "SLA breach" in str(result)
