"""CLI commands for managing alert grouping rules."""
import json
import os
import click
from pipewatch.grouper import GroupRule, AlertGrouper

_RULES_FILE = os.environ.get("PIPEWATCH_GROUP_RULES", ".pipewatch_group_rules.json")


def _load_rules():
    if not os.path.exists(_RULES_FILE):
        return []
    with open(_RULES_FILE) as f:
        data = json.load(f)
    return [GroupRule(**r) for r in data]


def _save_rules(rules):
    with open(_RULES_FILE, "w") as f:
        json.dump([r.__dict__ for r in rules], f, indent=2)


@click.group(name="group")
def grouper_cmd():
    """Manage alert grouping rules."""


@grouper_cmd.command("add")
@click.argument("group_name")
@click.option("--pipeline", default="*", help="Pipeline name or '*' for any")
@click.option("--metric", default="*", help="Metric name or '*' for any")
@click.option("--severity", default="*", help="Severity level or '*' for any")
def add_group_rule(group_name, pipeline, metric, severity):
    """Add a grouping rule."""
    rules = _load_rules()
    rule = GroupRule(group_name=group_name, pipeline=pipeline, metric=metric, severity=severity)
    rules.append(rule)
    _save_rules(rules)
    click.echo(f"Added group rule: '{group_name}' (pipeline={pipeline}, metric={metric}, severity={severity})")


@grouper_cmd.command("list")
def list_group_rules():
    """List all grouping rules."""
    rules = _load_rules()
    if not rules:
        click.echo("No grouping rules defined.")
        return
    for r in rules:
        click.echo(f"  {r.group_name}: pipeline={r.pipeline}, metric={r.metric}, severity={r.severity}")


@grouper_cmd.command("clear")
def clear_group_rules():
    """Remove all grouping rules."""
    _save_rules([])
    click.echo("All grouping rules cleared.")
