"""Tests for pipewatch.aggregator."""
import pytest
from datetime import datetime
from pipewatch.history import HistoryEntry
from pipewatch.aggregator import aggregate_entries, AggregationReport, PipelineTrend


def make_entry(name: str, duration: float, error_rate: float, rows: int, alerts: int) -> HistoryEntry:
    return HistoryEntry(
        pipeline_name=name,
        timestamp=datetime.utcnow().isoformat(),
        duration=duration,
        error_rate=error_rate,
        rows_processed=rows,
        alert_count=alerts,
    )


@pytest.fixture
def entries():
    return [
        make_entry("ingest", 120.0, 0.01, 5000, 0),
        make_entry("ingest", 150.0, 0.02, 4800, 1),
        make_entry("ingest", 130.0, 0.01, 5100, 0),
        make_entry("transform", 300.0, 0.10, 3000, 2),
        make_entry("transform", 320.0, 0.12, 2900, 2),
    ]


def test_aggregate_groups_by_pipeline(entries):
    report = aggregate_entries(entries)
    names = {t.pipeline_name for t in report.trends}
    assert names == {"ingest", "transform"}


def test_aggregate_run_count(entries):
    report = aggregate_entries(entries)
    ingest = next(t for t in report.trends if t.pipeline_name == "ingest")
    assert ingest.run_count == 3


def test_aggregate_avg_duration(entries):
    report = aggregate_entries(entries)
    ingest = next(t for t in report.trends if t.pipeline_name == "ingest")
    assert abs(ingest.avg_duration - (120 + 150 + 130) / 3) < 0. test_aggregate_alert_rate(entries):
    report = aggregate_entries(entries)
    ingest = next(t for t in report.trends if t.pipeline_name == "ingest")
    # 1 out of 3 runs had alerts
    assert abs(ingest.alert_rate - 1 / 3) < 0.01


def test_degrading_pipelines(entries):
    report = aggregate_entries(entries)
    degrading = report.degrading_pipelines()
    names = {t.pipeline_name for t in degrading}
    assert "transform" in names
    assert "ingest" not in names


def test_empty_entries():
    report = aggregate_entries([])
    assert report.trends == []
    assert report.degrading_pipelines() == []


def test_summary_contains_pipeline_names(entries):
    report = aggregate_entries(entries)
    summary = report.summary()
    assert "ingest" in summary
    assert "transform" in summary
    assert "DEGRADING" in summary
