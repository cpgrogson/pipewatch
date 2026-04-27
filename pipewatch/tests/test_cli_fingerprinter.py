"""Tests for pipewatch.cli_fingerprinter."""

from click.testing import CliRunner

from pipewatch.cli_fingerprinter import fingerprint_cmd


def test_show_fingerprint_outputs_hash() -> None:
    runner = CliRunner()
    result = runner.invoke(
        fingerprint_cmd,
        ["show", "--pipeline", "orders", "--metric", "error_rate"],
    )
    assert result.exit_code == 0
    assert "Fingerprint" in result.output
    assert "Short" in result.output


def test_show_fingerprint_stable_across_calls() -> None:
    runner = CliRunner()
    args = ["show", "--pipeline", "orders", "--metric", "error_rate", "--severity", "critical"]
    r1 = runner.invoke(fingerprint_cmd, args)
    r2 = runner.invoke(fingerprint_cmd, args)
    assert r1.exit_code == 0
    assert r2.exit_code == 0
    # extract fingerprint lines and compare
    def _fp_line(output: str) -> str:
        for line in output.splitlines():
            if line.startswith("Fingerprint"):
                return line
        return ""
    assert _fp_line(r1.output) == _fp_line(r2.output)


def test_show_fingerprint_with_salt_differs() -> None:
    runner = CliRunner()
    base = ["show", "--pipeline", "orders", "--metric", "error_rate"]
    r1 = runner.invoke(fingerprint_cmd, base + ["--salt", "aaa"])
    r2 = runner.invoke(fingerprint_cmd, base + ["--salt", "bbb"])
    assert r1.exit_code == 0
    assert r2.exit_code == 0
    assert r1.output != r2.output


def test_show_fingerprint_with_include_message() -> None:
    runner = CliRunner()
    args = [
        "show",
        "--pipeline", "orders",
        "--metric", "error_rate",
        "--message", "too many errors",
        "--include-message",
    ]
    result = runner.invoke(fingerprint_cmd, args)
    assert result.exit_code == 0
    assert "Fingerprint" in result.output
