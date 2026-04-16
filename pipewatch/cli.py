"""CLI entry point for pipewatch."""

from __future__ import annotations

import json
import sys

import click

from pipewatch.checker import PipelineMetrics, check_thresholds
from pipewatch.config import load_config


@click.group()
def cli() -> None:
    """pipewatch — monitor and alert on ETL pipeline health."""


@cli.command()
@click.option("--config", "-c", required=True, help="Path to pipewatch YAML config file.")
@click.option("--pipeline", "-p", required=True, help="Pipeline name to evaluate.")
@click.option("--metrics", "-m", required=True, help="JSON string of pipeline metrics.")
@click.option("--exit-code", is_flag=True, default=False, help="Exit with code 1 if alerts are triggered.")
def check(config: str, pipeline: str, metrics: str, exit_code: bool) -> None:
    """Check a pipeline's metrics against configured thresholds."""
    try:
        app_config = load_config(config)
    except FileNotFoundError as e:
        click.echo(str(e), err=True)
        sys.exit(2)

    pipeline_cfg = app_config.pipelines.get(pipeline)
    thresholds = pipeline_cfg.thresholds if pipeline_cfg else app_config.default_thresholds

    try:
        raw_metrics = json.loads(metrics)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid metrics JSON: {e}", err=True)
        sys.exit(2)

    m = PipelineMetrics(pipeline_name=pipeline, **raw_metrics)
    alerts = check_thresholds(m, thresholds)

    if alerts:
        for alert in alerts:
            click.echo(str(alert))
        if exit_code:
            sys.exit(1)
    else:
        click.echo(f"OK: {pipeline} — all thresholds passed.")


if __name__ == "__main__":
    cli()
