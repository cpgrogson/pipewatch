"""Tests for pipewatch.exporter."""
import csv
import json
from pathlib import Path

import pytest

from pipewatch.checker import Alert, PipelineMetrics
from pipewatch.exporter import export_report
from pipewatch.reporter import PipelineReport, RunReport


@pytest.fixture()
def run_report():
    healthy_pr = PipelineReport(
        pipeline="pipe_ok",
        metrics=PipelineMetrics(pipeline="pipe_ok", duration_seconds=10, error_rate=0.0, rows_processed=500),
        alerts=[],
    )
    alert_pr = PipelineReport(
        pipeline="pipe_bad",
        metrics=PipelineMetrics(pipeline="pipe_bad", duration_seconds=999, error_rate=0.5, rows_processed=1),
        alerts=[
            Alert(level="critical", message="duration exceeded"),
            Alert(level="warning", message="error rate high"),
        ],
    )
    rr = RunReport()
    rr.add(healthy_pr)
    rr.add(alert_pr)
    return rr


def test_export_json_creates_file(tmp_path, run_report):
    out = tmp_path / "report.json"
    export_report(run_report, out, fmt="json")
    assert out.exists()


def test_export_json_structure(tmp_path, run_report):
    out = tmp_path / "report.json"
    export_report(run_report, out, fmt="json")
    data = json.loads(out.read_text())
    assert data["total"] == 2
    assert data["healthy"] == 1
    assert data["degraded"] == 1
    pipelines = {p["pipeline"]: p for p in data["pipelines"]}
    assert pipelines["pipe_ok"]["healthy"] is True
    assert len(pipelines["pipe_bad"]["alerts"]) == 2


def test_export_csv_creates_file(tmp_path, run_report):
    out = tmp_path / "report.csv"
    export_report(run_report, out, fmt="csv")
    assert out.exists()


def test_export_csv_rows(tmp_path, run_report):
    out = tmp_path / "report.csv"
    export_report(run_report, out, fmt="csv")
    rows = list(csv.DictReader(out.open()))
    pipelines = [r["pipeline"] for r in rows]
    assert "pipe_ok" in pipelines
    assert "pipe_bad" in pipelines
    bad_rows = [r for r in rows if r["pipeline"] == "pipe_bad"]
    assert len(bad_rows) == 2


def test_export_unknown_format_raises(tmp_path, run_report):
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_report(run_report, tmp_path / "out.txt", fmt="xml")  # type: ignore[arg-type]
