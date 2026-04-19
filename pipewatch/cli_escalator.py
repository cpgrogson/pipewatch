import click
from pipewatch.escalator import EscalationRule, EscalationStore

_store = EscalationStore()


@click.group(name="escalate")
def escalate_cmd():
    """Manage alert escalation rules."""
    pass


@escalate_cmd.command("add")
@click.argument("pipeline")
@click.argument("metric")
@click.option("--window", default=30, show_default=True, help="Repeat window in minutes.")
@click.option("--max", "max_escalations", default=3, show_default=True, help="Occurrences before escalation.")
def add_escalation(pipeline, metric, window, max_escalations):
    """Add an escalation rule for PIPELINE and METRIC."""
    rule = EscalationRule(
        pipeline=pipeline,
        metric=metric,
        repeat_window_minutes=window,
        max_escalations=max_escalations,
    )
    _store.add_rule(rule)
    click.echo(f"Escalation rule added: {pipeline}:{metric} (window={window}m, max={max_escalations})")


@escalate_cmd.command("list")
def list_escalations():
    """List all escalation rules."""
    if not _store.rules:
        click.echo("No escalation rules defined.")
        return
    for rule in _store.rules:
        click.echo(f"  {rule.pipeline}:{rule.metric} window={rule.repeat_window_minutes}m max={rule.max_escalations}")


@escalate_cmd.command("clear")
def clear_escalations():
    """Clear all escalation records."""
    _store.clear()
    click.echo("Escalation records cleared.")
