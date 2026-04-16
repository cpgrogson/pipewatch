"""Tests for reporter module."""
from datetime import datetime
import pytest
from pipewatch.checker import Alert, PipelineMetrics
from pipewatch.reporter import PipelineReport, RunReport


@pytest.fixture
def healthy_metrics():
    return PipelineMetrics(duration_seconds=30, error_rate=0.01, rows_processed=500)


@pytest.fixture
def alert_metrics():
    return PipelineMetrics(duration_seconds=200, error_rate=0.15, rows_processed=10)


def test_pipeline_report_healthy(healthy_metrics):
    report = PipelineReport("pipe_a", healthy_metrics, [])
    assert report.healthy is True
    assert "OK" in report.summary()
    assert "pipe_a" in report.summary()


def test_pipeline_report_with_alerts(alert_metrics):
    alerts = [Alert("duration", 200, 120, ">")]
    report = PipelineReport("pipe_b", alert_metrics, alerts)
    assert report.healthy is False
    assert "ALERT" in report.summary()
    assert "!" in report.summary()


def test_run_report_counts():
    m = PipelineMetrics(10, 0.0, 100)
    run = RunReport()
    run.add(PipelineReport("p1", m, []))
    run.add(PipelineReport("p2", m, [Alert("duration", 50, 30, ">")]))
    assert run.total == 2
    assert run.healthy_count == 1
    assert run.alert_count == 1


def test_run_report_render_shows_alerts_by_default():
    m = PipelineMetrics(10, 0.0, 100)
    run = RunReport()
    run.add(PipelineReport("p1", m, [Alert("duration", 50, 30, ">")])) 
    output = run.render(verbose=False)
    assert "p1" in output
    assert "ALERT" in output


def test_run_report_render_verbose_shows_healthy():
    m = PipelineMetrics(10, 0.0, 100)
    run = RunReport()
    run.add(PipelineReport("p1", m, []))
    output = run.render(verbose=True)
    assert "OK" in output
    assert "p1" in output
