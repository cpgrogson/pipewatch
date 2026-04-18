"""Tests for anomaly detection module."""
import pytest
from datetime import datetime, timezone
from pipewatch.anomaly import detect_anomalies, AnomalyResult
from pipewatch.history import HistoryEntry


def make_entry(duration=10.0, error_rate=0.01, rows=1000, pipeline="pipe1"):
    return HistoryEntry(
        pipeline=pipeline,
        timestamp=datetime.now(timezone.utc).isoformat(),
        duration=duration,
        error_rate=error_rate,
        rows_processed=rows,
        alert_count=0,
    )


@pytest.fixture
def stable_history():
    return [make_entry(duration=10.0 + i * 0.1) for i in range(10)]


def test_no_anomaly_on_empty_history():
    current = make_entry(duration=999.0)
    result = detect_anomalies("pipe1", [], current)
    assert result == []


def test_no_anomaly_within_normal_range(stable_history):
    current = make_entry(duration=10.5)
    results = detect_anomalies("pipe1", stable_history, current)
    anomalies = [r for r in results if r.is_anomaly]
    assert len(anomalies) == 0


def test_detects_duration_anomaly(stable_history):
    current = make_entry(duration=500.0)
    results = detect_anomalies("pipe1", stable_history, current)
    duration_result = next(r for r in results if r.metric == "duration")
    assert duration_result.is_anomaly
    assert duration_result.z_score > 2.5


def test_detects_error_rate_anomaly():
    history = [make_entry(error_rate=0.01) for _ in range(10)]
    current = make_entry(error_rate=0.95)
    results = detect_anomalies("pipe1", history, current)
    er_result = next(r for r in results if r.metric == "error_rate")
    assert er_result.is_anomaly


def test_custom_z_threshold(stable_history):
    current = make_entry(duration=500.0)
    results = detect_anomalies("pipe1", stable_history, current, z_threshold=100.0)
    anomalies = [r for r in results if r.is_anomaly]
    assert len(anomalies) == 0


def test_anomaly_result_str():
    r = AnomalyResult(
        pipeline="p", metric="duration", current_value=100.0,
        mean=10.0, std_dev=1.0, z_score=90.0, is_anomaly=True
    )
    assert "ANOMALY" in str(r)
    assert "duration" in str(r)


def test_returns_all_three_metrics(stable_history):
    current = make_entry()
    results = detect_anomalies("pipe1", stable_history, current)
    metric_names = {r.metric for r in results}
    assert metric_names == {"duration", "error_rate", "rows_processed"}
