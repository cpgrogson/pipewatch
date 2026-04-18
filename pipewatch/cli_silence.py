"""CLI commands for managing alert silence rules."""
import click
from datetime import datetime
from pipewatch.silencer import SilenceStore, SilenceRule, silence_for

_store = SilenceStore()


@click.group(name="silence")
def silence_cmd():
    """Manage alert silence rules."""
    pass


@silence_cmd.command("add")
@click.argument("pipeline")
@click.argument("metric")
@click.option("--hours", default=1.0, show_default=True, help="Duration to silence in hours.")
@click.option("--reason", default="", help="Reason for silencing.")
def add_silence(pipeline, metric, hours, reason):
    """Silence alerts for PIPELINE / METRIC for a given number of hours."""
    rule = silence_for(pipeline, metric, hours, reason)
    _store.add(rule)
    click.echo(f"Silenced {pipeline}/{metric} for {hours}h (until {rule.until.strftime('%Y-%m-%d %H:%M')} UTC).")
    if reason:
        click.echo(f"Reason: {reason}")


@silence_cmd.command("list")
def list_silences():
    """List active silence rules."""
    rules = _store.active_rules()
    if not rules:
        click.echo("No active silence rules.")
        return
    for i, r in enumerate(rules, 1):
        until_str = r.until.strftime("%Y-%m-%d %H:%M UTC") if r.until else "indefinite"
        click.echo(f"{i}. pipeline={r.pipeline or '*'} metric={r.metric or '*'} until={until_str} reason={r.reason!r}")


@silence_cmd.command("clear")
@click.option("--expired-only", is_flag=True, default=False, help="Only remove expired rules.")
def clear_silences(expired_only):
    """Clear silence rules."""
    if expired_only:
        removed = _store.remove_expired()
        click.echo(f"Removed {removed} expired rule(s).")
    else:
        count = len(_store.rules)
        _store.rules.clear()
        click.echo(f"Cleared {count} rule(s).")
