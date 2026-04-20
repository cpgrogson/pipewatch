"""Tests for alert correlator."""
import pytest
from pipewatch.checker import Alert
from pipewatch.correlator import AlertCorrelator, CorrelationRule, Incident


def make_alert(pipeline: str, metric: str, severity: str = "warning") -> Alert:
    return Alert(pipeline=pipeline, metric=metric, severity=severity, message=f"{pipeline}/{metric}")


@pytest.fixture
def alerts():
    return [
        make_alert("etl_orders", "error_rate", "critical"),
        make_alert("etl_users", "error_rate", "critical"),
        make_alert("etl_orders", "duration", "warning"),
        make_alert("etl_inventory", "row_count", "warning"),
    ]


def test_no_incidents_without_rules(alerts):
    correlator = AlertCorrelator(rules=[])
    incidents = correlator.correlate(alerts)
    assert incidents == []


def test_no_incidents_on_empty_alerts():
    correlator = AlertCorrelator(rules=[CorrelationRule(group_by="metric", min_alerts=2)])
    incidents = correlator.correlate([])
    assert incidents == []


def test_correlate_by_metric(alerts):
    correlator = AlertCorrelator(rules=[CorrelationRule(group_by="metric", min_alerts=2)])
    incidents = correlator.correlate(alerts)
    assert len(incidents) == 1
    assert incidents[0].incident_id == "metric:error_rate"
    assert incidents[0].size == 2


def test_correlate_by_severity(alerts):
    correlator = AlertCorrelator(rules=[CorrelationRule(group_by="severity", min_alerts=2)])
    incidents = correlator.correlate(alerts)
    assert len(incidents) == 2
    ids = {i.incident_id for i in incidents}
    assert "severity:critical" in ids
    assert "severity:warning" in ids


def test_correlate_by_pipeline(alerts):
    correlator = AlertCorrelator(rules=[CorrelationRule(group_by="pipeline", min_alerts=2)])
    incidents = correlator.correlate(alerts)
    assert len(incidents) == 1
    assert incidents[0].incident_id == "pipeline:etl_orders"


def test_min_alerts_threshold_respected(alerts):
    correlator = AlertCorrelator(rules=[CorrelationRule(group_by="metric", min_alerts=3)])
    incidents = correlator.correlate(alerts)
    assert incidents == []


def test_incident_summary():
    a1 = make_alert("pipe_a", "error_rate", "critical")
    a2 = make_alert("pipe_b", "error_rate", "warning")
    incident = Incident(incident_id="metric:error_rate", alerts=[a1, a2])
    summary = incident.summary()
    assert "metric:error_rate" in summary
    assert "2 alert(s)" in summary
    assert "error_rate" in summary


def test_incident_pipelines_and_metrics():
    a1 = make_alert("pipe_a", "error_rate", "critical")
    a2 = make_alert("pipe_b", "error_rate", "critical")
    incident = Incident(incident_id="metric:error_rate", alerts=[a1, a2])
    assert set(incident.pipelines) == {"pipe_a", "pipe_b"}
    assert incident.metrics == ["error_rate"]
    assert incident.severities == ["critical"]
