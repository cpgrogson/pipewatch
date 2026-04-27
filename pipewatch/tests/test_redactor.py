"""Tests for the AlertRedactor."""

from __future__ import annotations

import pytest

from pipewatch.checker import Alert
from pipewatch.redactor import AlertRedactor, RedactionRule


@pytest.fixture
def alert() -> Alert:
    return Alert(
        pipeline="payments",
        metric="error_rate",
        message="Error rate 0.42 exceeds threshold (token=abc123secret)",
        severity="critical",
    )


@pytest.fixture
def redactor() -> AlertRedactor:
    return AlertRedactor()


def test_no_rules_returns_unchanged(redactor: AlertRedactor, alert: Alert) -> None:
    result = redactor.redact(alert)
    assert result.message == alert.message
    assert result.pipeline == alert.pipeline
    assert result.metric == alert.metric
    assert result.redacted_fields == []


def test_redact_message_masks_pattern(alert: Alert) -> None:
    r = AlertRedactor(rules=[RedactionRule(pattern=r"token=\w+")])
    result = r.redact(alert)
    assert "token=" not in result.message
    assert "[REDACTED]" in result.message
    assert "message" in result.redacted_fields


def test_redact_pipeline_name(alert: Alert) -> None:
    r = AlertRedactor(rules=[RedactionRule(pattern="payments", apply_to="pipeline")])
    result = r.redact(alert)
    assert result.pipeline == "[REDACTED]"
    assert "pipeline" in result.redacted_fields


def test_redact_metric_name(alert: Alert) -> None:
    r = AlertRedactor(rules=[RedactionRule(pattern="error_rate", apply_to="metric")])
    result = r.redact(alert)
    assert result.metric == "[REDACTED]"
    assert "metric" in result.redacted_fields


def test_custom_replacement(alert: Alert) -> None:
    r = AlertRedactor(rules=[RedactionRule(pattern=r"token=\w+", replacement="***")])
    result = r.redact(alert)
    assert "***" in result.message


def test_multiple_rules_applied(alert: Alert) -> None:
    r = AlertRedactor(
        rules=[
            RedactionRule(pattern=r"token=\w+"),
            RedactionRule(pattern=r"\d+\.\d+"),
        ]
    )
    result = r.redact(alert)
    assert "token=" not in result.message
    assert "0.42" not in result.message
    assert "message" in result.redacted_fields


def test_redact_all_applies_to_each_alert() -> None:
    alerts = [
        Alert(pipeline="p1", metric="m", message="secret=xyz", severity="warning"),
        Alert(pipeline="p2", metric="m", message="normal message", severity="info"),
    ]
    r = AlertRedactor(rules=[RedactionRule(pattern=r"secret=\w+")])
    results = r.redact_all(alerts)
    assert len(results) == 2
    assert "[REDACTED]" in results[0].message
    assert results[1].message == "normal message"


def test_str_representation(alert: Alert) -> None:
    r = AlertRedactor(rules=[RedactionRule(pattern=r"token=\w+")])
    result = r.redact(alert)
    s = str(result)
    assert "[CRITICAL]" in s
    assert "payments" in s
    assert "error_rate" in s


def test_no_match_leaves_redacted_fields_empty(alert: Alert) -> None:
    r = AlertRedactor(rules=[RedactionRule(pattern="nomatch")])
    result = r.redact(alert)
    assert result.redacted_fields == []
    assert result.message == alert.message


def test_original_alert_preserved(alert: Alert) -> None:
    r = AlertRedactor(rules=[RedactionRule(pattern=r"token=\w+")])
    result = r.redact(alert)
    assert result.original is alert
    assert result.original.message == alert.message
