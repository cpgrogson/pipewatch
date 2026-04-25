import json
import click
from pathlib import Path
from pipewatch.labeler import LabelRule

_RULES_PATH = Path(".pipewatch_label_rules.json")


def _load_rules() -> list[dict]:
    if not _RULES_PATH.exists():
        return []
    return json.loads(_RULES_PATH.read_text())


def _save_rules(rules: list[dict]) -> None:
    _RULES_PATH.write_text(json.dumps(rules, indent=2))


@click.group(name="label")
def labeler_cmd():
    """Manage alert labeling rules."""


@labeler_cmd.command("add")
@click.option("--pipeline", default="*", show_default=True, help="Pipeline name or '*'")
@click.option("--metric", default="*", show_default=True, help="Metric name or '*'")
@click.argument("key")
@click.argument("value")
def add_label_rule(pipeline: str, metric: str, key: str, value: str):
    """Add a label rule that attaches KEY=VALUE to matching alerts."""
    rules = _load_rules()
    rules.append({"pipeline": pipeline, "metric": metric, "label_key": key, "label_value": value})
    _save_rules(rules)
    click.echo(f"Added label rule: {pipeline}/{metric} -> {key}={value}")


@labeler_cmd.command("list")
def list_label_rules():
    """List all label rules."""
    rules = _load_rules()
    if not rules:
        click.echo("No label rules configured.")
        return
    for r in rules:
        click.echo(f"  {r['pipeline']}/{r['metric']} -> {r['label_key']}={r['label_value']}")


@labeler_cmd.command("clear")
def clear_label_rules():
    """Remove all label rules."""
    _save_rules([])
    click.echo("All label rules cleared.")
