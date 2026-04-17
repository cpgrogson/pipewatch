"""CLI sub-command for exporting pipeline reports."""
from __future__ import annotations

from pathlib import Path

import click

from pipewatch.config import load_config
from pipewatch.exporter import ExportFormat, export_report
from pipewatch.watch import run_single_check


@click.command("export")
@click.option(
    "--config",
    "config_path",
    default="pipewatch.yaml",
    show_default=True,
    help="Path to pipewatch config file.",
)
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Destination file for the exported report.",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "csv"]),
    default="json",
    show_default=True,
    help="Export format.",
)
def export_cmd(config_path: str, output: Path, fmt: ExportFormat) -> None:
    """Run a single pipeline check and export the report to a file."""
    try:
        app_config = load_config(config_path)
    except FileNotFoundError:
        raise click.ClickException(f"Config file not found: {config_path}")

    run_report = run_single_check(app_config)
    export_report(run_report, output, fmt=fmt)
    click.echo(f"Report exported to {output} ({fmt})")
    if run_report.degraded:
        click.echo(
            click.style(
                f"{run_report.degraded} pipeline(s) degraded.", fg="yellow"
            )
        )
