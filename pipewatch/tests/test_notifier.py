"""Tests for pipewatch.notifier."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.checker import Alert
from pipewatch.notifier import LogNotifier, EmailNotifier, build_notifier


@pytest.fixture
def sample_alerts():
    return [
        Alert(metric="duration_seconds", value=120.0, threshold=60.0, message="Duration exceeded"),
        Alert(metric="error_rate", value=0.15, threshold=0.05, message="Error rate too high"),
    ]


def test_log_notifier_emits_warnings(sample_alerts, caplog):
    notifier = LogNotifier(level="WARNING")
    with caplog.at_level(logging.WARNING, logger="pipewatch.notifier"):
        notifier.send(sample_alerts, "my_pipeline")
    assert len(caplog.records) == 2
    assert "my_pipeline" in caplog.records[0].message


def test_log_notifier_no_alerts_no_output(caplog):
    notifier = LogNotifier()
    with caplog.at_level(logging.WARNING, logger="pipewatch.notifier"):
        notifier.send([], "silent_pipeline")
    assert caplog.records == []


def test_email_notifier_skips_on_empty_alerts():
    notifier = EmailNotifier(
        smtp_host="localhost", smtp_port=25,
        sender="watch@example.com", recipients=["ops@example.com"]
    )
    with patch("smtplib.SMTP") as mock_smtp:
        notifier.send([], "pipe")
        mock_smtp.assert_not_called()


def test_email_notifier_sends_message(sample_alerts):
    notifier = EmailNotifier(
        smtp_host="localhost", smtp_port=25,
        sender="watch@example.com", recipients=["ops@example.com"]
    )
    mock_server = MagicMock()
    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.return_value.__enter__.return_value = mock_server
        notifier.send(sample_alerts, "my_pipeline")
        mock_server.send_message.assert_called_once()


def test_email_notifier_logs_on_smtp_error(sample_alerts, caplog):
    notifier = EmailNotifier(
        smtp_host="bad-host", smtp_port=25,
        sender="a@b.com", recipients=["c@d.com"]
    )
    with patch("smtplib.SMTP", side_effect=OSError("connection refused")):
        with caplog.at_level(logging.ERROR, logger="pipewatch.notifier"):
            notifier.send(sample_alerts, "pipe")
    assert any("Failed to send" in r.message for r in caplog.records)


def test_build_notifier_returns_log_notifier_by_default():
    notifier = build_notifier({})
    assert isinstance(notifier, LogNotifier)


def test_build_notifier_returns_email_notifier():
    cfg = {
        "backend": "email",
        "smtp_host": "smtp.example.com",
        "smtp_port": "587",
        "sender": "watch@example.com",
        "recipients": ["team@example.com"],
    }
    notifier = build_notifier(cfg)
    assert isinstance(notifier, EmailNotifier)
    assert notifier.smtp_port == 587
