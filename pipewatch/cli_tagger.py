"""CLI commands for managing auto-tagging rules in pipewatch."""

import click
import json
from pathlib import Path

TAGGER_RULES_FILE = Path(".pipewatch_tagger_rules.json")


def _load_rules() -> list[dict]:
    if TAGGER_RULES_FILE.exists():
        return json.loads(TAGGER_RULES_FILE.read_text())
    return []


def _save_rules(rules: list[dict]) -> None:
    TAGGER_RULES_FILE.write_text(json.dumps(rules, indent=2))


@click.group(name="tagger")
def tagger_cmd():
    """Manage auto-tagging rules for alerts."""


@tagger_cmd.command("add")
@click.option("--pipeline", default="*", show_default=True, help="Pipeline name or '*' for all.")
@click.option("--metric", default="*", show_default=True, help="Metric name or '*' for all.")
@click.argument("tags", nargs=-1, required=True)
def add_tag_rule(pipeline: str, metric: str, tags: tuple):
    """Add a tagging rule."""
    rules = _load_rules()
    rule = {"pipeline": pipeline, "metric": metric, "tags": list(tags)}
    rules.append(rule)
    _save_rules(rules)
    click.echo(f"Added tag rule: pipeline={pipeline}, metric={metric}, tags={list(tags)}")


@tagger_cmd.command("list")
def list_tag_rules():
    """List all tagging rules."""
    rules = _load_rules()
    if not rules:
        click.echo("No tagging rules defined.")
        return
    for i, r in enumerate(rules):
        click.echo(f"[{i}] pipeline={r['pipeline']} metric={r['metric']} tags={r['tags']}")


@tagger_cmd.command("clear")
def clear_tag_rules():
    """Clear all tagging rules."""
    _save_rules([])
    click.echo("All tagging rules cleared.")
