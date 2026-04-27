"""CLI commands for alert replay."""

import click
from datetime import datetime
from typing import List

from pipewatch.checker import Alert
from pipewatch.history import HistoryStore
from pipewatch.replayer import replay_history


def _default_handler(pipeline: str, alerts: List[Alert]) -> None:
    for alert in alerts:
        click.echo(f"  [{pipeline}] {alert}")


@click.group(name="replay")
def replay_cmd() -> None:
    """Replay historical alerts through current pipeline logic."""


@replay_cmd.command(name="run")
@click.option("--pipeline", default=None, help="Filter by pipeline name.")
@click.option(
    "--since",
    default=None,
    help="Replay entries after this ISO datetime (e.g. 2024-01-01T00:00:00).",
)
@click.option("--limit", default=None, type=int, help="Max entries to replay.")
@click.option("--store", "store_path", default=".pipewatch_history.json", show_default=True)
def run_replay(
    pipeline: str,
    since: str,
    limit: int,
    store_path: str,
) -> None:
    """Replay stored history entries."""
    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
        except ValueError:
            raise click.BadParameter(f"Invalid datetime format: {since}")

    store = HistoryStore(path=store_path)
    result = replay_history(
        store,
        handler=_default_handler,
        pipeline=pipeline,
        since=since_dt,
        limit=limit,
    )

    for line in result.outputs:
        click.echo(line)

    click.echo(f"\n{result.summary}")
