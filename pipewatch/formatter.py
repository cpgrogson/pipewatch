"""Output formatters for RunReport (text, JSON, CSV)."""
import csv
import io
import json
from pipewatch.reporter import RunReport


def format_text(report: RunReport, verbose: bool = False) -> str:
    return report.render(verbose=verbose)


def format_json(report: RunReport) -> str:
    data = {
        "generated_at": report.generated_at.isoformat(),
        "summary": {
            "total": report.total,
            "healthy": report.healthy_count,
            "alerts": report.alert_count,
        },
        "pipelines": [],
    }
    for r in report.reports:
        data["pipelines"].append({
            "name": r.pipeline_name,
            "checked_at": r.checked_at.isoformat(),
            "healthy": r.healthy,
            "metrics": {
                "duration_seconds": r.metrics.duration_seconds,
                "error_rate": r.metrics.error_rate,
                "rows_processed": r.metrics.rows_processed,
            },
            "alerts": [str(a) for a in r.alerts],
        })
    return json.dumps(data, indent=2)


def format_csv(report: RunReport) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["pipeline", "checked_at", "healthy", "duration_seconds",
                     "error_rate", "rows_processed", "alert_count", "alerts"])
    for r in report.reports:
        writer.writerow([
            r.pipeline_name,
            r.checked_at.isoformat(),
            r.healthy,
            r.metrics.duration_seconds,
            f"{r.metrics.error_rate:.4f}",
            r.metrics.rows_processed,
            len(r.alerts),
            "; ".join(str(a) for a in r.alerts),
        ])
    return buf.getvalue()


FORMATS = {
    "text": format_text,
    "json": format_json,
    "csv": format_csv,
}


def render(report: RunReport, fmt: str = "text", verbose: bool = False) -> str:
    if fmt not in FORMATS:
        raise ValueError(f"Unknown format '{fmt}'. Choose from: {list(FORMATS)}.")
    if fmt == "text":
        return format_text(report, verbose=verbose)
    return FORMATS[fmt](report)
