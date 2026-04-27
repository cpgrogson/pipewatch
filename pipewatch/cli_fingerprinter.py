"""CLI commands for alert fingerprinting configuration and inspection."""

import click

from pipewatch.checker import Alert
from pipewatch.fingerprinter import AlertFingerprinter, FingerprintRule


@click.group(name="fingerprint")
def fingerprint_cmd() -> None:
    """Manage and inspect alert fingerprints."""


@fingerprint_cmd.command("show")
@click.option("--pipeline", required=True, help="Pipeline name")
@click.option("--metric", required=True, help="Metric name")
@click.option("--severity", default="warning", show_default=True)
@click.option("--message", default="", help="Alert message")
@click.option("--include-message", is_flag=True, default=False)
@click.option("--salt", default="", help="Optional salt value")
def show_fingerprint(
    pipeline: str,
    metric: str,
    severity: str,
    message: str,
    include_message: bool,
    salt: str,
) -> None:
    """Compute and display the fingerprint for a hypothetical alert."""
    alert = Alert(
        pipeline=pipeline,
        metric=metric,
        severity=severity,
        message=message,
        value=0.0,
        threshold=0.0,
    )
    rule = FingerprintRule(
        include_message=include_message,
        salt=salt,
    )
    fp = AlertFingerprinter(rule=rule).fingerprint(alert)
    click.echo(f"Fingerprint : {fp.fingerprint}")
    click.echo(f"Short       : {fp.fingerprint[:12]}")
    click.echo(f"Alert       : {fp.alert}")
