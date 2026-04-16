"""Tests for the threshold checker module."""

import pytest

from pipewatch.checker import PipelineMetrics, check_thresholds, Alert
from pipewatch.config import ThresholdConfig


@pytest.fixture
def thresholds():
    return ThresholdConfig(
        max_duration_seconds=300.0,
        max_error_rate=0.05,
        min_rows_processed=100,
        max_lag_seconds=60.0,
    )


def test_no_alerts_when_all_within_thresholds(thresholds):
    metrics = PipelineMetrics(
        pipeline_name="etl_daily",
        duration_seconds=200.0,
        error_rate=0.01,
        rows_processed=500,
        lag_seconds=10.0,
    )
    alerts = check_thresholds(metrics, thresholds)
    assert alerts == []


def test_alert_on_exceeded_duration(thresholds):
    metrics = PipelineMetrics(pipeline_name="etl_daily", duration_seconds=400.0)
    alerts = check_thresholds(metrics, thresholds)
    assert len(alerts) == 1
    assert alerts[0].field == "duration_seconds"


def test_alert_on_high_error_rate(thresholds):
    metrics = PipelineMetrics(pipeline_name="etl_daily", error_rate=0.10)
    alerts = check_thresholds(metrics, thresholds)
    assert any(a.field == "error_rate" for a in alerts)


def test_alert_on_low_rows(thresholds):
    metrics = PipelineMetrics(pipeline_name="etl_daily", rows_processed=50)
    alerts = check_thresholds(metrics, thresholds)
    assert any(a.field == "rows_processed" for a in alerts)


def test_alert_on_high_lag(thresholds):
    metrics = PipelineMetrics(pipeline_name="etl_daily", lag_seconds=120.0)
    alerts = check_thresholds(metrics, thresholds)
    assert any(a.field == "lag_seconds" for a in alerts)


def test_multiple_alerts(thresholds):
    metrics = PipelineMetrics(
        pipeline_name="etl_daily",
        duration_seconds=999.0,
        error_rate=0.99,
    )
    alerts = check_thresholds(metrics, thresholds)
    assert len(alerts) == 2


def test_none_metrics_skipped(thresholds):
    metrics = PipelineMetrics(pipeline_name="etl_daily")
    alerts = check_thresholds(metrics, thresholds)
    assert alerts == []


def test_alert_str_format(thresholds):
    metrics = PipelineMetrics(pipeline_name="etl_daily", duration_seconds=999.0)
    alerts = check_thresholds(metrics, thresholds)
    assert "etl_daily" in str(alerts[0])
    assert "duration_seconds" in str(alerts[0])
