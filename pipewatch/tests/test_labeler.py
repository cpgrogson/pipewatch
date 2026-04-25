import pytest
from pipewatch.checker import Alert
from pipewatch.labeler import LabelRule, LabeledAlert, AlertLabeler


@pytest.fixture
def duration_alert():
    return Alert(pipeline="etl_main", metric="duration", value=500.0, threshold=300.0, severity="critical")


@pytest.fixture
def error_alert():
    return Alert(pipeline="etl_main", metric="error_rate", value=0.15, threshold=0.05, severity="warning")


@pytest.fixture
def labeler():
    lbl = AlertLabeler()
    lbl.add_rule(LabelRule(pipeline="etl_main", metric="duration", label_key="team", label_value="data-eng"))
    lbl.add_rule(LabelRule(pipeline="*", metric="error_rate", label_key="channel", label_value="#alerts"))
    lbl.add_rule(LabelRule(pipeline="etl_main", metric="*", label_key="env", label_value="prod"))
    return lbl


def test_label_rule_matches_exact(duration_alert):
    rule = LabelRule(pipeline="etl_main", metric="duration", label_key="k", label_value="v")
    assert rule.matches(duration_alert)


def test_label_rule_no_match_wrong_pipeline(duration_alert):
    rule = LabelRule(pipeline="other", metric="duration", label_key="k", label_value="v")
    assert not rule.matches(duration_alert)


def test_label_rule_wildcard_pipeline(error_alert):
    rule = LabelRule(pipeline="*", metric="error_rate", label_key="k", label_value="v")
    assert rule.matches(error_alert)


def test_label_rule_wildcard_metric(duration_alert):
    rule = LabelRule(pipeline="etl_main", metric="*", label_key="k", label_value="v")
    assert rule.matches(duration_alert)


def test_labeled_alert_str_with_labels(duration_alert):
    labeled = LabeledAlert(alert=duration_alert, labels={"team": "data-eng"})
    result = str(labeled)
    assert "team=data-eng" in result


def test_labeled_alert_str_no_labels(duration_alert):
    labeled = LabeledAlert(alert=duration_alert, labels={})
    assert str(labeled) == str(duration_alert)


def test_labeler_attaches_matching_labels(labeler, duration_alert):
    labeled = labeler.label(duration_alert)
    assert labeled.labels.get("team") == "data-eng"
    assert labeled.labels.get("env") == "prod"
    assert "channel" not in labeled.labels


def test_labeler_wildcard_metric_label(labeler, error_alert):
    labeled = labeler.label(error_alert)
    assert labeled.labels.get("channel") == "#alerts"
    assert labeled.labels.get("env") == "prod"


def test_labeler_no_rules_returns_empty_labels():
    lbl = AlertLabeler()
    alert = Alert(pipeline="x", metric="y", value=1.0, threshold=0.5, severity="warning")
    labeled = lbl.label(alert)
    assert labeled.labels == {}


def test_label_all_processes_multiple_alerts(labeler, duration_alert, error_alert):
    results = labeler.label_all([duration_alert, error_alert])
    assert len(results) == 2
    assert all(isinstance(r, LabeledAlert) for r in results)
