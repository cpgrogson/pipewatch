"""Export pipeline run reports to various file formats."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Literal

from pipewatch.reporter import RunReport

ExportFormat = Literal["json", "csv"]


def export_json(report: RunReport, path: Path) -> None:
    """Write a RunReport to a JSON file."""
    data = {
        "total": report.total,
        "healthy": report.healthy,
        "degraded": report.degraded,
        "pipelines": [
            {
                "pipeline": pr.pipeline,
                "healthy": pr.healthy,
                "alerts": [
                    {"level": a.level, "message": a.message}
                    for a in pr.alerts
                ],
            }
            for pr in report.pipeline_reports
        ],
    }
    path.write_text(json.dumps(data, indent=2))


def export_csv(report: RunReport, path: Path) -> None:
    """Write alert rows from a RunReport to a CSV file."""
    with path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["pipeline", "healthy", "alert_level", "alert_message"])
        for pr in report.pipeline_reports:
            if pr.alerts:
                for alert in pr.alerts:
                    writer.writerow([pr.pipeline, pr.healthy, alert.level, alert.message])
            else:
                writer.writerow([pr.pipeline, pr.healthy, "", ""])


def export_report(report: RunReport, path: Path, fmt: ExportFormat = "json") -> None:
    """Export a RunReport to *path* in the requested format."""
    if fmt == "json":
        export_json(report, path)
    elif fmt == "csv":
        export_csv(report, path)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}")
