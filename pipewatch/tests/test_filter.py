"""Tests for pipewatch.filter module."""
import pytest
from pipewatch.checker import Alert, PipelineMetrics
from pipewatch.reporter import PipelineReport, RunReport
from pipewatch.filter import (
    filter_by_tags, filter_by_names,
    filter_alerts_by_severity, filter_run_report,
)


def make_metrics(name: str, tags=None):
    m = PipelineMetrics(pipeline_name=name, duration_seconds=10.0,
                        error_rate=0.0, rows_processed=100)
    m.tags = tags or []
    return m


def make_report(name: str, tags=None, alerts=None):
    metrics = make_metrics(name, tags)
    report = PipelineReport(pipeline_name=name, metrics=metrics)
    for a in (alerts or []):
        report.alerts.append(a)
    return report


@pytest.fixture
def reports():
    return [
        make_report("etl_a", tags=["finance", "daily"]),
        make_report("etl_b", tags=["marketing"]),
        make_report("etl_c", tags=["finance"]),
    ]


def test_filter_by_tags_returns_matching(reports):
    result = filter_by_tags(reports, ["finance"])
    assert len(result) == 2
    assert all("finance" in r.metrics.tags for r in result)


def test_filter_by_tags_empty_returns_all(reports):
    result = filter_by_tags(reports, [])
    assert len(result) == 3


def test_filter_by_names(reports):
    result = filter_by_names(reports, ["etl_a", "etl_c"])
    assert [r.pipeline_name for r in result] == ["etl_a", "etl_c"]


def test_filter_by_names_empty_returns_all(reports):
    assert len(filter_by_names(reports, [])) == 3


def test_filter_alerts_by_severity():
    alerts = [
        Alert(pipeline_name="p", field="duration", value=5.0, threshold=3.0, severity="critical"),
        Alert(pipeline_name="p", field="error_rate", value=0.1, threshold=0.05, severity="warning"),
    ]
    critical = filter_alerts_by_severity(alerts, "critical")
    assert len(critical) == 1 and critical[0].severity == "critical"

    warnings = filter_alerts_by_severity(alerts, "warning")
    assert len(warnings) == 1 and warnings[0].severity == "warning"


def test_filter_run_report_by_tags(reports):
    run = RunReport()
    for r in reports:
        run.add(r)
    filtered = filter_run_report(run, tags=["marketing"])
    assert filtered.total == 1


def test_filter_run_report_by_names(reports):
    run = RunReport()
    for r in reports:
        run.add(r)
    filtered = filter_run_report(run, names=["etl_b"])
    assert filtered.total == 1
    assert filtered.pipeline_reports[0].pipeline_name == "etl_b"
