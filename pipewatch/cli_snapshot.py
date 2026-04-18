"""CLI commands for pipeline metric snapshots."""
import click
from datetime import datetime, timezone
from pipewatch.snapshot import MetricSnapshot, SnapshotStore


@click.group("snapshot")
def snapshot_cmd():
    """Manage pipeline metric snapshots."""


@snapshot_cmd.command("save")
@click.option("--pipeline", required=True, help="Pipeline name")
@click.option("--duration", type=float, required=True, help="Duration in seconds")
@click.option("--error-rate", type=float, required=True, help="Error rate (0.0-1.0)")
@click.option("--rows", type=int, required=True, help="Rows processed")
@click.option("--store", "store_path", default=".pipewatch_snapshots.json", show_default=True)
def save_snapshot(pipeline, duration, error_rate, rows, store_path):
    """Save a metric snapshot for a pipeline."""
    snap = MetricSnapshot(
        pipeline_name=pipeline,
        captured_at=datetime.now(timezone.utc).isoformat(),
        duration_seconds=duration,
        error_rate=error_rate,
        rows_processed=rows,
    )
    store = SnapshotStore(store_path)
    diff = store.diff(snap)
    store.save_snapshot(snap)
    click.echo(f"Snapshot saved for '{pipeline}'.")
    if diff:
        click.echo(f"  Change: {diff.summary()}")


@snapshot_cmd.command("list")
@click.option("--store", "store_path", default=".pipewatch_snapshots.json", show_default=True)
def list_snapshots(store_path):
    """List all saved snapshots."""
    store = SnapshotStore(store_path)
    snaps = store.all_snapshots()
    if not snaps:
        click.echo("No snapshots found.")
        return
    for s in snaps:
        click.echo(
            f"{s.pipeline_name} | captured: {s.captured_at} | "
            f"duration: {s.duration_seconds}s | error_rate: {s.error_rate} | rows: {s.rows_processed}"
        )


@snapshot_cmd.command("diff")
@click.option("--pipeline", required=True)
@click.option("--duration", type=float, required=True)
@click.option("--error-rate", type=float, required=True)
@click.option("--rows", type=int, required=True)
@click.option("--store", "store_path", default=".pipewatch_snapshots.json", show_default=True)
def diff_snapshot(pipeline, duration, error_rate, rows, store_path):
    """Show diff between current metrics and saved snapshot."""
    snap = MetricSnapshot(
        pipeline_name=pipeline,
        captured_at=datetime.now(timezone.utc).isoformat(),
        duration_seconds=duration,
        error_rate=error_rate,
        rows_processed=rows,
    )
    store = SnapshotStore(store_path)
    diff = store.diff(snap)
    if diff is None:
        click.echo(f"No previous snapshot found for '{pipeline}'.")
    else:
        click.echo(diff.summary())
