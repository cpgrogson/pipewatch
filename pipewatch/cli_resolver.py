"""CLI commands for managing alert resolutions."""

import click

from pipewatch.checker import Alert
from pipewatch.resolver import ResolutionStore

_store = ResolutionStore()


@click.group(name="resolve")
def resolver_cmd():
    """Manage alert resolutions."""


@resolver_cmd.command("add")
@click.argument("pipeline")
@click.argument("metric")
@click.option("--note", default="", help="Optional resolution note.")
def add_resolution(pipeline: str, metric: str, note: str):
    """Mark an alert as resolved."""
    alert = Alert(pipeline=pipeline, metric=metric, message="", severity="info")
    entry = _store.resolve(alert, note=note)
    click.echo(f"Resolved: {entry.pipeline}/{entry.metric} at {entry.resolved_at}")
    if note:
        click.echo(f"  Note: {note}")


@resolver_cmd.command("list")
def list_resolutions():
    """List all resolved alerts."""
    entries = _store.all()
    if not entries:
        click.echo("No resolutions recorded.")
        return
    for e in entries:
        note_part = f" — {e.note}" if e.note else ""
        click.echo(f"  [{e.resolved_at}] {e.pipeline}/{e.metric}{note_part}")


@resolver_cmd.command("clear")
def clear_resolutions():
    """Clear all resolution records."""
    _store.clear()
    click.echo("All resolutions cleared.")
