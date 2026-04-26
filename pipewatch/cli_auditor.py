"""CLI commands for inspecting the alert audit log."""

import click
from pipewatch.auditor import AuditStore


@click.group(name="audit")
def audit_cmd():
    """Inspect the alert audit log."""


@audit_cmd.command("list")
@click.option("--pipeline", default=None, help="Filter by pipeline name.")
@click.option("--outcome", default=None, help="Filter by outcome (e.g. notified, suppressed).")
@click.option("--limit", default=50, show_default=True, help="Max entries to show.")
def list_audits(pipeline: str, outcome: str, limit: int):
    """List recorded audit entries."""
    store = AuditStore()
    entries = store.all()

    if pipeline:
        entries = [e for e in entries if e.pipeline == pipeline]
    if outcome:
        entries = [e for e in entries if e.outcome == outcome]

    entries = entries[-limit:]

    if not entries:
        click.echo("No audit entries found.")
        return

    for e in entries:
        click.echo(f"[{e.timestamp}] {e.pipeline}/{e.metric} ({e.severity}) -> {e.outcome}: {e.message}")


@audit_cmd.command("summary")
def audit_summary():
    """Show a summary of alert outcomes."""
    store = AuditStore()
    entries = store.all()

    if not entries:
        click.echo("No audit entries.")
        return

    from collections import Counter
    counts = Counter(e.outcome for e in entries)
    click.echo(f"Total entries: {len(entries)}")
    for outcome, count in sorted(counts.items()):
        click.echo(f"  {outcome}: {count}")


@audit_cmd.command("clear")
@click.confirmation_option(prompt="Clear all audit entries?")
def clear_audits():
    """Delete all audit log entries."""
    store = AuditStore()
    store.clear()
    click.echo("Audit log cleared.")
