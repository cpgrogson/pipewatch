"""CLI commands for managing alert throttle rules."""

import click

from pipewatch.throttler import ThrottleRule, ThrottlerStore

_DEFAULT_PATH = ".pipewatch_throttle.json"


@click.group(name="throttle")
def throttle_cmd():
    """Manage alert throttle rules."""


@throttle_cmd.command("add")
@click.argument("pipeline")
@click.argument("metric")
@click.argument("interval", type=int)
@click.option("--store", default=_DEFAULT_PATH, help="Path to throttle store.")
def add_throttle(pipeline: str, metric: str, interval: int, store: str):
    """Add a throttle rule: suppress repeated alerts within INTERVAL seconds."""
    s = ThrottlerStore(path=store)
    rule = ThrottleRule(pipeline=pipeline, metric=metric, interval_seconds=interval)
    s.add_rule(rule)
    # Persist rule list separately via a simple JSON sidecar
    import json
    from pathlib import Path
    rules_path = Path(store).with_suffix(".rules.json")
    existing = []
    if rules_path.exists():
        existing = json.loads(rules_path.read_text())
    existing.append({"pipeline": pipeline, "metric": metric, "interval_seconds": interval})
    rules_path.write_text(json.dumps(existing, indent=2))
    click.echo(f"Throttle rule added: {pipeline}/{metric} every {interval}s")


@throttle_cmd.command("list")
@click.option("--store", default=_DEFAULT_PATH, help="Path to throttle store.")
def list_throttles(store: str):
    """List all configured throttle rules."""
    import json
    from pathlib import Path
    rules_path = Path(store).with_suffix(".rules.json")
    if not rules_path.exists():
        click.echo("No throttle rules configured.")
        return
    rules = json.loads(rules_path.read_text())
    if not rules:
        click.echo("No throttle rules configured.")
        return
    for r in rules:
        click.echo(f"  {r['pipeline']}/{r['metric']} — interval: {r['interval_seconds']}s")


@throttle_cmd.command("clear")
@click.option("--store", default=_DEFAULT_PATH, help="Path to throttle store.")
def clear_throttles(store: str):
    """Clear all throttle rules and recorded state."""
    import json
    from pathlib import Path
    s = ThrottlerStore(path=store)
    s.clear()
    rules_path = Path(store).with_suffix(".rules.json")
    if rules_path.exists():
        rules_path.unlink()
    click.echo("All throttle rules and state cleared.")
