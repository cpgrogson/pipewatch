"""Tests for pipewatch.fingerprinter."""

import pytest

from pipewatch.checker import Alert
from pipewatch.fingerprinter import (
    AlertFingerprinter,
    FingerprintRule,
    FingerprintedAlert,
)


@pytest.fixture
def alert() -> Alert:
    return Alert(
        pipeline="orders",
        metric="error_rate",
        severity="critical",
        message="Error rate too high",
        value=0.15,
        threshold=0.05,
    )


def test_fingerprint_returns_fingerprinted_alert(alert: Alert) -> None:
    fp = AlertFingerprinter().fingerprint(alert)
    assert isinstance(fp, FingerprintedAlert)
    assert fp.alert is alert
    assert len(fp.fingerprint) == 64  # sha256 hex


def test_fingerprint_is_stable_for_same_inputs(alert: Alert) -> None:
    f1 = AlertFingerprinter().fingerprint(alert)
    f2 = AlertFingerprinter().fingerprint(alert)
    assert f1.fingerprint == f2.fingerprint


def test_different_pipelines_produce_different_fingerprints(alert: Alert) -> None:
    other = Alert(
        pipeline="inventory",
        metric=alert.metric,
        severity=alert.severity,
        message=alert.message,
        value=alert.value,
        threshold=alert.threshold,
    )
    f1 = AlertFingerprinter().fingerprint(alert)
    f2 = AlertFingerprinter().fingerprint(other)
    assert f1.fingerprint != f2.fingerprint


def test_exclude_severity_makes_fingerprints_equal_across_severities(alert: Alert) -> None:
    rule = FingerprintRule(include_severity=False)
    fingerprinter = AlertFingerprinter(rule=rule)
    warning = Alert(
        pipeline=alert.pipeline,
        metric=alert.metric,
        severity="warning",
        message=alert.message,
        value=alert.value,
        threshold=alert.threshold,
    )
    f1 = fingerprinter.fingerprint(alert)
    f2 = fingerprinter.fingerprint(warning)
    assert f1.fingerprint == f2.fingerprint


def test_include_message_changes_fingerprint(alert: Alert) -> None:
    rule_with = FingerprintRule(include_message=True)
    rule_without = FingerprintRule(include_message=False)
    f_with = AlertFingerprinter(rule=rule_with).fingerprint(alert)
    f_without = AlertFingerprinter(rule=rule_without).fingerprint(alert)
    assert f_with.fingerprint != f_without.fingerprint


def test_salt_changes_fingerprint(alert: Alert) -> None:
    f1 = AlertFingerprinter(FingerprintRule(salt="abc")).fingerprint(alert)
    f2 = AlertFingerprinter(FingerprintRule(salt="xyz")).fingerprint(alert)
    assert f1.fingerprint != f2.fingerprint


def test_fingerprint_all_returns_list(alert: Alert) -> None:
    alerts = [alert, alert]
    results = AlertFingerprinter().fingerprint_all(alerts)
    assert len(results) == 2
    assert all(isinstance(r, FingerprintedAlert) for r in results)


def test_str_shows_short_fingerprint_and_alert(alert: Alert) -> None:
    fp = AlertFingerprinter().fingerprint(alert)
    s = str(fp)
    assert fp.fingerprint[:8] in s
