"""CLI commands for managing alert suppression rules."""
import click
from pipewatch.suppressor import SuppressionRule, SuppressionStore

_store = SuppressionStore()


@click.group(name="suppress")
def suppress_cmd():
    """Manage alert suppression rules."""
    pass


@suppress_cmd.command("add")
@click.argument("pipeline")
@click.argument("metric")
@click.option("--min-occurrences", default=3, show_default=True, help="Minimum occurrences before alerting.")
@click.option("--window", default=300, show_default=True, help="Time window in seconds.")
def add_suppression(pipeline, metric, min_occurrences, window):
    """Add a suppression rule for a pipeline/metric."""
    rule = SuppressionRule(
        pipeline=pipeline,
        metric=metric,
        min_occurrences=min_occurrences,
        window_seconds=window,
    )
    _store.add_rule(rule)
    click.echo(f"Suppression rule added: {pipeline}:{metric} (min={min_occurrences}, window={window}s)")


@suppress_cmd.command("list")
def list_suppressions():
    """List all active suppression rules."""
    if not _store.rules:
        click.echo("No suppression rules defined.")
        return
    for rule in _store.rules:
        click.echo(f"  {rule.pipeline}:{rule.metric} — min_occurrences={rule.min_occurrences}, window={rule.window_seconds}s")


@suppress_cmd.command("clear")
def clear_suppressions():
    """Remove all suppression rules."""
    _store.rules.clear()
    _store._history.clear()
    click.echo("All suppression rules cleared.")
