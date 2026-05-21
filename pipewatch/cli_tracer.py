import click
from pipewatch.checker import Alert
from pipewatch.tracer import AlertTracer

_tracer = AlertTracer()


@click.group(name="tracer")
def tracer_cmd():
    """Trace alert lifecycle stages."""


@tracer_cmd.command(name="trace")
@click.option("--pipeline", required=True, help="Pipeline name")
@click.option("--metric", required=True, help="Metric name")
@click.option("--severity", default="warning", help="Alert severity")
@click.option("--message", default="", help="Alert message")
@click.option("--stage", required=True, help="Stage label to record")
@click.option("--detail", default="", help="Detail for this stage")
def trace_alert(pipeline, metric, severity, message, stage, detail):
    """Record a trace event for an alert."""
    alert = Alert(pipeline=pipeline, metric=metric, severity=severity, message=message)
    t = _tracer.trace(alert)
    t.add_event(stage=stage, detail=detail or f"recorded at stage '{stage}'")
    click.echo(f"Traced: {t.summary()}")


@tracer_cmd.command(name="list")
@click.option("--pipeline", default=None, help="Filter by pipeline")
def list_traces(pipeline):
    """List recorded traces."""
    traces = _tracer.for_pipeline(pipeline) if pipeline else _tracer.all_traces()
    if not traces:
        click.echo("No traces recorded.")
        return
    for t in traces:
        click.echo(t.summary())
        for e in t.events:
            click.echo(f"  [{e.timestamp}] {e.stage}: {e.detail}")


@tracer_cmd.command(name="clear")
def clear_traces():
    """Clear all recorded traces."""
    _tracer.clear()
    click.echo("All traces cleared.")
