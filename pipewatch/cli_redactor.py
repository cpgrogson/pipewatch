"""CLI commands for managing redaction rules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import click

from pipewatch.redactor import RedactionRule

_RULES_FILE = Path(".pipewatch_redaction_rules.json")


def _load_rules() -> List[dict]:
    if _RULES_FILE.exists():
        return json.loads(_RULES_FILE.read_text())
    return []


def _save_rules(rules: List[dict]) -> None:
    _RULES_FILE.write_text(json.dumps(rules, indent=2))


@click.group(name="redact")
def redactor_cmd() -> None:
    """Manage alert redaction rules."""


@redactor_cmd.command("add")
@click.argument("pattern")
@click.option("--replacement", default="[REDACTED]", show_default=True)
@click.option(
    "--apply-to",
    default="message",
    type=click.Choice(["message", "pipeline", "metric"]),
    show_default=True,
)
def add_redaction_rule(pattern: str, replacement: str, apply_to: str) -> None:
    """Add a redaction rule."""
    rules = _load_rules()
    rules.append({"pattern": pattern, "replacement": replacement, "apply_to": apply_to})
    _save_rules(rules)
    click.echo(f"Added redaction rule: pattern='{pattern}' apply_to={apply_to}")


@redactor_cmd.command("list")
def list_redaction_rules() -> None:
    """List all redaction rules."""
    rules = _load_rules()
    if not rules:
        click.echo("No redaction rules configured.")
        return
    for i, r in enumerate(rules, 1):
        click.echo(f"{i}. pattern='{r['pattern']}' replacement='{r['replacement']}' apply_to={r['apply_to']}")


@redactor_cmd.command("clear")
def clear_redaction_rules() -> None:
    """Remove all redaction rules."""
    _save_rules([])
    click.echo("All redaction rules cleared.")
