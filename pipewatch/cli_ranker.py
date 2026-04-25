import click
from pipewatch.checker import Alert
from pipewatch.ranker import AlertRanker


@click.group(name="rank")
def ranker_cmd():
    """Rank and prioritize alerts by severity and metric type."""


@ranker_cmd.command(name="show")
@click.option("--top", default=5, show_default=True, help="Number of top alerts to show.")
@click.option("--pipeline", default=None, help="Filter by pipeline name.")
def show_ranked(top: int, pipeline: str):
    """Show top-ranked alerts from a sample or stdin (demo mode)."""
    sample_alerts = [
        Alert(pipeline="orders", metric="error_rate", value=0.15, threshold=0.05, severity="critical"),
        Alert(pipeline="orders", metric="duration", value=320, threshold=300, severity="warning"),
        Alert(pipeline="inventory", metric="row_count", value=80, threshold=100, severity="info"),
        Alert(pipeline="payments", metric="error_rate", value=0.08, threshold=0.05, severity="warning"),
        Alert(pipeline="users", metric="duration", value=500, threshold=300, severity="critical"),
    ]

    alerts = sample_alerts
    if pipeline:
        alerts = [a for a in alerts if a.pipeline == pipeline]

    if not alerts:
        click.echo("No alerts to rank.")
        return

    ranker = AlertRanker()
    ranked = ranker.top(alerts, n=top)

    click.echo(f"Top {len(ranked)} ranked alert(s):")
    for ra in ranked:
        click.echo(f"  {ra}")
