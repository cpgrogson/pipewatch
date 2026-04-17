"""Unit tests for PipelineTrend degradation logic."""
import pytest
from pipewatch.aggregator import PipelineTrend


def make_trend(avg_duration=60.0, avg_error_rate=0.01, alert_rate=0.0):
    return PipelineTrend(
        pipeline_name="test",
        avg_duration=avg_duration,
        avg_error_rate=avg_error_rate,
        avg_rows_processed=1000,
        run_count=5,
        alert_rate=alert_rate,
    )


def test_healthy_trend_not_degrading():
    trend = make_trend(avg_duration=60.0, avg_error_rate=0.01)
    assert not trend.is_degrading()


def test_high_error_rate_is_degrading():
    trend = make_trend(avg_error_rate=0.10)
    assert trend.is_degrading()


def test_very_long_duration_is_degrading():
    # default duration_threshold=0.2 hours = 720s; 3x = 2160s
    trend = make_trend(avg_duration=3000.0)
    assert trend.is_degrading()


def test_custom_thresholds_respected():
    trend = make_trend(avg_duration=500.0, avg_error_rate=0.03)
    # With tight thresholds
    assert trend.is_degrading(duration_threshold=0.1, error_threshold=0.02)
    # With loose thresholds
    assert not trend.is_degrading(duration_threshold=1.0, error_threshold=0.1)


def test_boundary_error_rate_not_degrading():
    trend = make_trend(avg_error_rate=0.05)
    # exactly at threshold — not strictly greater
    assert not trend.is_degrading()


def test_boundary_error_rate_just_over():
    trend = make_trend(avg_error_rate=0.051)
    assert trend.is_degrading()
