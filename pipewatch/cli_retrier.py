"""CLI commands for managing alert retries."""
import click

from pipewatch.retrier import RetryStore


@click.group("retry")
def retry_cmd() -> None:
    """Manage alert retry queue."""


@retry_cmd.command("list")
def list_retries() -> None:
    """List all pending retry entries."""
    store = RetryStore()
    entries = store.all()
    if not entries:
        click.echo("No pending retries.")
        return
    for e in entries:
        status = "exhausted" if e.is_exhausted() else ("ready" if e.is_ready() else "waiting")
        click.echo(
            f"[{status}] {e.pipeline}/{e.metric} ({e.severity}) "
            f"attempts={e.attempts}/{e.max_attempts} — {e.message}"
        )


@retry_cmd.command("due")
def list_due() -> None:
    """List retry entries that are ready to be re-sent."""
    store = RetryStore()
    entries = store.due()
    if not entries:
        click.echo("No retries due.")
        return
    for e in entries:
        click.echo(f"{e.pipeline}/{e.metric} ({e.severity}) attempts={e.attempts} — {e.message}")


@retry_cmd.command("clear")
def clear_retries() -> None:
    """Clear all retry entries."""
    store = RetryStore()
    store.clear()
    click.echo("Retry queue cleared.")
