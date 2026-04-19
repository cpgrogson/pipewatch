import click
from pipewatch.ratelimiter import RateLimiterStore, RateLimitRule

_store = RateLimiterStore()


@click.group(name="ratelimit")
def ratelimit_cmd():
    """Manage alert rate limiting rules."""
    pass


@ratelimit_cmd.command("add")
@click.argument("pipeline")
@click.argument("metric")
@click.option("--max-alerts", default=3, show_default=True, help="Max alerts per window")
@click.option("--window", default=3600, show_default=True, help="Window in seconds")
def add_ratelimit(pipeline, metric, max_alerts, window):
    """Add a rate limit rule for a pipeline/metric pair."""
    rule = RateLimitRule(pipeline=pipeline, metric=metric, max_alerts=max_alerts, window_seconds=window)
    _store.add_rule(rule)
    click.echo(f"Rate limit rule added: {pipeline}:{metric} max={max_alerts} window={window}s")


@ratelimit_cmd.command("list")
def list_ratelimits():
    """List all rate limit rules."""
    rules = _store.list_rules()
    if not rules:
        click.echo("No rate limit rules configured.")
        return
    for r in rules:
        click.echo(f"{r.pipeline}:{r.metric}  max={r.max_alerts}  window={r.window_seconds}s")


@ratelimit_cmd.command("clear")
def clear_ratelimits():
    """Clear all rate limit rules."""
    _store.clear()
    click.echo("All rate limit rules cleared.")
