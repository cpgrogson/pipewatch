from click.testing import CliRunner
from pipewatch.cli_router import router_cmd, _router


def setup_function():
    _router.rules.clear()


def test_add_rule_success():
    runner = CliRunner()
    result = runner.invoke(router_cmd, ["add", "--name", "crit", "--severity", "critical"])
    assert result.exit_code == 0
    assert "crit" in result.output
    assert len(_router.rules) == 1


def test_list_no_rules():
    runner = CliRunner()
    result = runner.invoke(router_cmd, ["list"])
    assert "No routing rules" in result.output


def test_list_with_rules():
    runner = CliRunner()
    runner.invoke(router_cmd, ["add", "--name", "r1", "--pipeline", "etl_main"])
    result = runner.invoke(router_cmd, ["list"])
    assert "r1" in result.output
    assert "etl_main" in result.output


def test_clear_rules():
    runner = CliRunner()
    runner.invoke(router_cmd, ["add", "--name", "tmp"])
    result = runner.invoke(router_cmd, ["clear"])
    assert "cleared" in result.output
    assert len(_router.rules) == 0
