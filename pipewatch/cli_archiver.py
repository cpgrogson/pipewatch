"""CLI commands for the alert archiver."""

import click

from pipewatch.archiver import ArchiveStore
from pipewatch.checker import Alert

_STORE = ArchiveStore()


@click.group(name="archive")
def archive_cmd() -> None:
    """Manage the alert archive."""


@archive_cmd.command("add")
@click.option("--pipeline", required=True, help="Pipeline name")
@click.option("--metric", required=True, help="Metric name")
@click.option("--severity", default="warning", show_default=True)
@click.option("--message", default="", help="Alert message")
@click.option("--reason", default="manual", show_default=True, help="Archive reason")
def add_archive(pipeline: str, metric: str, severity: str, message: str, reason: str) -> None:
    """Archive an alert manually."""
    alert = Alert(pipeline=pipeline, metric=metric, severity=severity, message=message)
    entry = _STORE.archive(alert, reason=reason)
    click.echo(f"Archived: [{entry.severity}] {entry.pipeline}/{entry.metric} at {entry.archived_at}")


@archive_cmd.command("list")
@click.option("--pipeline", default=None, help="Filter by pipeline")
def list_archives(pipeline: str) -> None:
    """List archived alerts."""
    entries = _STORE.filter_by_pipeline(pipeline) if pipeline else _STORE.all()
    if not entries:
        click.echo("No archived alerts.")
        return
    for e in entries:
        click.echo(f"[{e.severity}] {e.pipeline}/{e.metric} — {e.reason} @ {e.archived_at}")


@archive_cmd.command("clear")
def clear_archives() -> None:
    """Remove all archived alerts."""
    _STORE.clear()
    click.echo("Archive cleared.")
