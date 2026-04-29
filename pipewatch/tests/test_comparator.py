"""Tests for pipewatch.comparator."""
import pytest
from pipewatch.checker import Alert
from pipewatch.comparator import compare_alerts, ComparisonResult


def make_alert(pipeline="pipe_a", metric="error_rate", severity="warning", message="msg"):
    return Alert(pipeline=pipeline, metric=metric, message=message, severity=severity)


# --- compare_alerts ---

def test_no_changes_when_alerts_identical():
    alerts = [make_alert()]
    result = compare_alerts(alerts, alerts)
    assert result.new_alerts == []
    assert result.resolved_alerts == []
    assert len(result.persisting_alerts) == 1


def test_new_alert_detected():
    previous = []
    current = [make_alert()]
    result = compare_alerts(previous, current)
    assert len(result.new_alerts) == 1
    assert result.new_alerts[0].pipeline == "pipe_a"
    assert result.resolved_alerts == []


def test_resolved_alert_detected():
    previous = [make_alert()]
    current = []
    result = compare_alerts(previous, current)
    assert result.new_alerts == []
    assert len(result.resolved_alerts) == 1
    assert result.resolved_alerts[0].pipeline == "pipe_a"


def test_mixed_changes():
    prev = [make_alert(pipeline="a"), make_alert(pipeline="b")]
    curr = [make_alert(pipeline="b"), make_alert(pipeline="c")]
    result = compare_alerts(prev, curr)
    assert len(result.new_alerts) == 1
    assert result.new_alerts[0].pipeline == "c"
    assert len(result.resolved_alerts) == 1
    assert result.resolved_alerts[0].pipeline == "a"
    assert len(result.persisting_alerts) == 1
    assert result.persisting_alerts[0].pipeline == "b"


def test_has_changes_true_when_new():
    result = compare_alerts([], [make_alert()])
    assert result.has_changes() is True


def test_has_changes_false_when_only_persisting():
    alerts = [make_alert()]
    result = compare_alerts(alerts, alerts)
    assert result.has_changes() is False


def test_summary_no_changes():
    result = ComparisonResult()
    assert result.summary() == "No changes detected."


def test_summary_with_new_and_resolved():
    result = ComparisonResult(
        new_alerts=[make_alert()],
        resolved_alerts=[make_alert(pipeline="b")],
    )
    summary = result.summary()
    assert "1 new" in summary
    assert "1 resolved" in summary


def test_total_counts_all_categories():
    result = ComparisonResult(
        new_alerts=[make_alert()],
        resolved_alerts=[make_alert(pipeline="b")],
        persisting_alerts=[make_alert(pipeline="c")],
    )
    assert result.total == 3
