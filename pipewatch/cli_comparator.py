"""CLI commands for alert comparison between runs."""
import json
import click
from pipewatch.checker import Alert
from pipewatch.comparator import compare_alerts, ComparisonResult


def _alerts_from_file(path: str):
    with open(path) as f:
        data = json.load(f)
    alerts = []
    for item in data:
        alerts.append(
            Alert(
                pipeline=item["pipeline"],
                metric=item["metric"],
                message=item["message"],
                severity=item.get("severity", "warning"),
                value=item.get("value"),
                threshold=item.get("threshold"),
            )
        )
    return alerts


@click.group(name="compare")
def comparator_cmd():
    """Compare alert snapshots between pipeline runs."""


@comparator_cmd.command(name="diff")
@click.argument("previous_file", type=click.Path(exists=True))
@click.argument("current_file", type=click.Path(exists=True))
@click.option("--show-persisting", is_flag=True, default=False, help="Also list persisting alerts.")
def diff_alerts(previous_file: str, current_file: str, show_persisting: bool):
    """Diff two alert JSON files and show what changed."""
    previous = _alerts_from_file(previous_file)
    current = _alerts_from_file(current_file)
    result = compare_alerts(previous, current)

    click.echo(result.summary())

    if result.new_alerts:
        click.echo("\nNew alerts:")
        for a in result.new_alerts:
            click.echo(f"  [NEW] [{a.severity.upper()}] {a.pipeline} / {a.metric}: {a.message}")

    if result.resolved_alerts:
        click.echo("\nResolved alerts:")
        for a in result.resolved_alerts:
            click.echo(f"  [RESOLVED] {a.pipeline} / {a.metric}: {a.message}")

    if show_persisting and result.persisting_alerts:
        click.echo("\nPersisting alerts:")
        for a in result.persisting_alerts:
            click.echo(f"  [PERSISTING] [{a.severity.upper()}] {a.pipeline} / {a.metric}: {a.message}")
