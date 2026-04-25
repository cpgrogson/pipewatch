import pytest
from click.testing import CliRunner
from pipewatch.cli_ranker import ranker_cmd


@pytest.fixture
def runner():
    return CliRunner()


def test_show_ranked_default(runner):
    result = runner.invoke(ranker_cmd, ["show"])
    assert result.exit_code == 0
    assert "Rank #1" in result.output


def test_show_ranked_top_2(runner):
    result = runner.invoke(ranker_cmd, ["show", "--top", "2"])
    assert result.exit_code == 0
    assert "Rank #1" in result.output
    assert "Rank #2" in result.output
    assert "Rank #3" not in result.output


def test_show_ranked_filter_pipeline(runner):
    result = runner.invoke(ranker_cmd, ["show", "--pipeline", "orders"])
    assert result.exit_code == 0
    assert "orders" in result.output


def test_show_ranked_unknown_pipeline(runner):
    result = runner.invoke(ranker_cmd, ["show", "--pipeline", "nonexistent_pipeline_xyz"])
    assert result.exit_code == 0
    assert "No alerts to rank" in result.output


def test_show_ranked_output_has_score(runner):
    result = runner.invoke(ranker_cmd, ["show", "--top", "1"])
    assert result.exit_code == 0
    assert "score=" in result.output
