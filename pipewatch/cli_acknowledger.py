import click
from datetime import datetime, timedelta, timezone
from pipewatch.acknowledger import AcknowledgementEntry, AcknowledgementStore

_store = AcknowledgementStore()


@click.group(name="ack")
def ack_cmd():
    """Manage alert acknowledgements."""
    pass


@ack_cmd.command("add")
@click.argument("pipeline")
@click.argument("metric")
@click.option("--by", required=True, help="Name of the person acknowledging.")
@click.option("--reason", required=True, help="Reason for acknowledgement.")
@click.option(
    "--expires-in",
    default=None,
    type=int,
    help="Expiry in minutes from now (optional).",
)
def add_ack(pipeline, metric, by, reason, expires_in):
    """Acknowledge an alert for a pipeline/metric."""
    expires_at = None
    if expires_in is not None:
        expiry = datetime.now(timezone.utc) + timedelta(minutes=expires_in)
        expires_at = expiry.isoformat()

    entry = AcknowledgementEntry(
        pipeline=pipeline,
        metric=metric,
        acknowledged_by=by,
        reason=reason,
        expires_at=expires_at,
    )
    _store.acknowledge(entry)
    click.echo(f"Acknowledged {metric} for pipeline '{pipeline}' by {by}.")


@ack_cmd.command("list")
def list_acks():
    """List all active acknowledgements."""
    entries = _store.active_entries()
    if not entries:
        click.echo("No active acknowledgements.")
        return
    for e in entries:
        expiry_str = e.expires_at if e.expires_at else "never"
        click.echo(
            f"[{e.pipeline}] {e.metric} — by {e.acknowledged_by}: "
            f"{e.reason} (expires: {expiry_str})"
        )


@ack_cmd.command("clear")
def clear_acks():
    """Clear all acknowledgements."""
    _store.clear()
    click.echo("All acknowledgements cleared.")
