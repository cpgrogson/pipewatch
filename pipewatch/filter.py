"""Filter pipelines by tags, names, or alert severity."""
from typing import List, Optional
from pipewatch.checker import Alert, PipelineMetrics
from pipewatch.reporter import PipelineReport, RunReport


def filter_by_tags(reports: List[PipelineReport], tags: List[str]) -> List[PipelineReport]:
    """Return only reports whose pipeline tags overlap with the given tags."""
    if not tags:
        return reports
    return [
        r for r in reports
        if r.metrics and any(t in getattr(r.metrics, 'tags', []) for t in tags)
    ]


def filter_by_names(reports: List[PipelineReport], names: List[str]) -> List[PipelineReport]:
    """Return only reports whose pipeline name is in the given list."""
    if not names:
        return reports
    return [r for r in reports if r.pipeline_name in names]


def filter_alerts_by_severity(alerts: List[Alert], severity: str) -> List[Alert]:
    """Return alerts matching the given severity level ('warning' or 'critical')."""
    return [a for a in alerts if a.severity == severity]


def filter_run_report(run_report: RunReport,
                      tags: Optional[List[str]] = None,
                      names: Optional[List[str]] = None) -> RunReport:
    """Return a new RunReport containing only matching pipeline reports."""
    reports = list(run_report.pipeline_reports)
    if tags:
        reports = filter_by_tags(reports, tags)
    if names:
        reports = filter_by_names(reports, names)
    filtered = RunReport()
    for r in reports:
        filtered.add(r)
    return filtered
