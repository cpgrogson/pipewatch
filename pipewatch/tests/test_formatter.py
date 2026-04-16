"""Tests for output formatters."""
import json
import csv
import io
import pytest
from pipewatch.checker import Alert, PipelineMetrics
from pipewatch.reporter import PipelineReport, RunReport
from pipewatch.formatter import render, format_json, format_csv


@pytest.fixture
def run_report():
    m1 = PipelineMetrics(duration_seconds=45, error_rate=0.02, rows_processed=300)
    m2 = PipelineMetrics(duration_seconds=180, error_rate=0.1, rows_processed=50)
    run = RunReport()
    run.add(PipelineReport("etl_sales", m1, []))
    run.add(PipelineReport("etl_users", m2, [Alert("duration", 180, 120, ">")]))
    return run


def test_render_text(run_report):
    out = render(run_report, fmt="text", verbose=True)
    assert "etl_sales" in out
    assert "etl_users" in out


def test_render_json_valid(run_report):
    out = render(run_report, fmt="json")
    data = json.loads(out)
    assert data["summary"]["total"] == 2
    assert data["summary"]["alerts"] == 1
    names = [p["name"] for p in data["pipelines"]]
    assert "etl_sales" in names


def test_render_csv_valid(run_report):
    out = render(run_report, fmt="csv")
    reader = csv.DictReader(io.StringIO(out))
    rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["pipeline"] == "etl_sales"
    assert rows[1]["alert_count"] == "1"


def test_render_unknown_format_raises(run_report):
    with pytest.raises(ValueError, match="Unknown format"):
        render(run_report, fmt="xml")


def test_json_includes_metrics(run_report):
    data = json.loads(format_json(run_report))
    pipe = next(p for p in data["pipelines"] if p["name"] == "etl_sales")
    assert pipe["metrics"]["duration_seconds"] == 45
    assert pipe["healthy"] is True
