import click
from pipewatch.router import AlertRouter, RoutingRule
from pipewatch.notifier import LogNotifier

_router = AlertRouter()


@click.group(name="router")
def router_cmd():
    """Manage alert routing rules."""
    pass


@router_cmd.command("add")
@click.option("--name", required=True, help="Rule name")
@click.option("--severity", multiple=True, help="Match severities")
@click.option("--pipeline", multiple=True, help="Match pipeline names")
def add_rule(name, severity, pipeline):
    """Add a routing rule (uses LogNotifier by default)."""
    rule = RoutingRule(
        name=name,
        severities=list(severity),
        pipelines=list(pipeline),
        notifier=LogNotifier(),
    )
    _router.add_rule(rule)
    click.echo(f"Routing rule '{name}' added.")


@router_cmd.command("list")
def list_rules():
    """List all routing rules."""
    if not _router.rules:
        click.echo("No routing rules defined.")
        return
    for rule in _router.rules:
        sev = ", ".join(rule.severities) or "any"
        pip = ", ".join(rule.pipelines) or "any"
        click.echo(f"  [{rule.name}] severities={sev} pipelines={pip}")


@router_cmd.command("clear")
def clear_rules():
    """Clear all routing rules."""
    _router.rules.clear()
    click.echo("All routing rules cleared.")
