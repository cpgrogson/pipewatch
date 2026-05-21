import pytest
from click.testing import CliRunner
from pipewatch.cli_tracer import tracer_cmd, _tracer


@pytest.fixture(autouse=True)
def setup_function():
    _tracer.clear()
    yield
    _tracer.clear()


@pytest.fixture
def runner():
    return CliRunner()


def test_trace_alert_creates_trace(runner):
    result = runner.invoke(tracer_cmd, [
        "trace",
        "--pipeline", "etl_orders",
        "--metric", "error_rate",
        "--severity", "critical",
        "--stage", "check",
        "--detail", "exceeded threshold",
    ])
    assert result.exit_code == 0
    assert "etl_orders" in result.output
    assert "check" in result.output


def test_list_no_traces(runner):
    result = runner.invoke(tracer_cmd, ["list"])
    assert result.exit_code == 0
    assert "No traces recorded" in result.output


def test_list_with_traces(runner):
    runner.invoke(tracer_cmd, [
        "trace",
        "--pipeline", "etl_users",
        "--metric", "duration",
        "--stage", "notify",
    ])
    result = runner.invoke(tracer_cmd, ["list"])
    assert result.exit_code == 0
    assert "etl_users" in result.output
    assert "notify" in result.output


def test_list_filter_by_pipeline(runner):
    runner.invoke(tracer_cmd, ["trace", "--pipeline", "etl_a", "--metric", "m1", "--stage", "s1"])
    runner.invoke(tracer_cmd, ["trace", "--pipeline", "etl_b", "--metric", "m2", "--stage", "s2"])
    result = runner.invoke(tracer_cmd, ["list", "--pipeline", "etl_a"])
    assert "etl_a" in result.output
    assert "etl_b" not in result.output


def test_clear_traces(runner):
    runner.invoke(tracer_cmd, ["trace", "--pipeline", "p1", "--metric", "m1", "--stage", "s1"])
    result = runner.invoke(tracer_cmd, ["clear"])
    assert result.exit_code == 0
    assert "cleared" in result.output
    result2 = runner.invoke(tracer_cmd, ["list"])
    assert "No traces recorded" in result2.output
