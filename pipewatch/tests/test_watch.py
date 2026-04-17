"""Tests for pipewatch.watch."""

import pytest
from unittest.mock import MagicMock, patch

from pipewatch.checker import PipelineMetrics, Alert
from pipewatch.config import AppConfig, PipelineConfig, ThresholdConfig
from pipewatch.watch import run_single_check


@pytest.fixture
def threshold():
    return ThresholdConfig(max_duration_seconds=100, max_error_rate=0.05, min_rows_processed=10)


@pytest.fixture
def pipelines(threshold):
    return [
        PipelineConfig(name="pipe_a", thresholds=threshold, tags=[]),
        PipelineConfig(name="pipe_b", thresholds=threshold, tags=[]),
    ]


@pytest.fixture
def healthy_metrics():
    return PipelineMetrics(
        pipeline_name="x",
        duration_seconds=50,
        error_rate=0.01,
        rows_processed=100,
    )


@pytest.fixture
def app_config(pipelines):
    return AppConfig(pipelines=pipelines, notifier={"backend": "log"})


def test_run_single_check_no_alerts(app_config, pipelines, healthy_metrics):
    metrics_fn = MagicMock(return_value=healthy_metrics)

    with patch("pipewatch.watch.build_notifier") as mock_build:
        mock_notifier = MagicMock()
        mock_build.return_value = mock_notifier
        report = run_single_check(pipelines, metrics_fn, app_config)

    assert report.healthy_count == 2
    assert report.alerting_count == 0
    mock_notifier.send.assert_called_once_with([])


def test_run_single_check_with_alerts(app_config, pipelines, threshold):
    bad_metrics = PipelineMetrics(
        pipeline_name="pipe_a",
        duration_seconds=999,
        error_rate=0.9,
        rows_processed=0,
    )
    metrics_fn = MagicMock(return_value=bad_metrics)

    with patch("pipewatch.watch.build_notifier") as mock_build:
        mock_notifier = MagicMock()
        mock_build.return_value = mock_notifier
        report = run_single_check(pipelines, metrics_fn, app_config)

    assert report.alerting_count == 2
    sent_alerts = mock_notifier.send.call_args[0][0]
    assert len(sent_alerts) > 0
