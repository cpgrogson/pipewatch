"""CLI commands for baseline capture and drift detection."""
import click
from pipewatch.baseline import BaselineStore, BaselineEntry
from pipewatch.aggregator import aggregate
from pipewatch.history import HistoryStore


@click.group("baseline")
def baseline_cmd():
    """Manage pipeline metric baselines."""


@baseline_cmd.command("capture")
@click.option("--history", default=".pipewatch_history.json", show_default=True)
@click.option("--baseline", "baseline_path", default=".pipewatch_baseline.json", show_default=True)
def capture_baseline(history: str, baseline_path: str):
    """Capture current aggregated metrics as baseline."""
    hs = HistoryStore(history)
    bs = BaselineStore(baseline_path)
    report = aggregate(hs.all())
    for trend in report.trends:
        entry = BaselineEntry(
            pipeline=trend.pipeline,
            avg_duration=trend.avg_duration,
            avg_error_rate=trend.avg_error_rate,
            avg_rows_processed=trend.avg_rows_processed,
        )
        bs.save(entry)
        click.echo(f"Captured baseline for {trend.pipeline}")
    click.echo(f"Saved {len(report.trends)} baseline(s) to {baseline_path}")


@baseline_cmd.command("drift")
@click.option("--history", default=".pipewatch_history.json", show_default=True)
@click.option("--baseline", "baseline_path", default=".pipewatch_baseline.json", show_default=True)
@click.option("--threshold", default=0.2, show_default=True, help="Significance threshold (fraction)")
def show_drift(history: str, baseline_path: str, threshold: float):
    """Show drift between current metrics and baseline."""
    hs = HistoryStore(history)
    bs = BaselineStore(baseline_path)
    report = aggregate(hs.all())
    found = False
    for trend in report.trends:
        current = BaselineEntry(
            pipeline=trend.pipeline,
            avg_duration=trend.avg_duration,
            avg_error_rate=trend.avg_error_rate,
            avg_rows_processed=trend.avg_rows_processed,
        )
        drift = bs.compare(current)
        if drift is None:
            click.echo(f"{trend.pipeline}: no baseline found")
            continue
        found = True
        marker = "[SIGNIFICANT]" if drift.is_significant(threshold) else "[ok]"
        click.echo(f"{marker} {drift.summary()}")
    if not found:
        click.echo("No baselines available. Run 'baseline capture' first.")
