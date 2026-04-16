"""Notification backends for pipewatch alerts."""

from __future__ import annotations

import smtplib
import logging
from email.message import EmailMessage
from dataclasses import dataclass, field
from typing import List, Protocol

from pipewatch.checker import Alert

logger = logging.getLogger(__name__)


class NotifierBackend(Protocol):
    def send(self, alerts: List[Alert], pipeline_name: str) -> None:
        ...


@dataclass
class LogNotifier:
    """Logs alerts using Python's logging module."""
    level: str = "WARNING"

    def send(self, alerts: List[Alert], pipeline_name: str) -> None:
        log_fn = getattr(logger, self.level.lower(), logger.warning)
        for alert in alerts:
            log_fn("[%s] %s", pipeline_name, alert)


@dataclass
class EmailNotifier:
    """Sends alert digest via SMTP."""
    smtp_host: str
    smtp_port: int
    sender: str
    recipients: List[str]
    subject_prefix: str = "[pipewatch]"

    def send(self, alerts: List[Alert], pipeline_name: str) -> None:
        if not alerts:
            return

        body = "\n".join(str(a) for a in alerts)
        subject = f"{self.subject_prefix} Alerts for pipeline '{pipeline_name}'"

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)
        msg.set_content(body)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.send_message(msg)
            logger.info("Alert email sent for pipeline '%s'", pipeline_name)
        except OSError as exc:
            logger.error("Failed to send alert email: %s", exc)


def build_notifier(config: dict) -> NotifierBackend:
    """Factory that builds a notifier from a config dict."""
    backend = config.get("backend", "log")
    if backend == "email":
        return EmailNotifier(
            smtp_host=config["smtp_host"],
            smtp_port=int(config.get("smtp_port", 25)),
            sender=config["sender"],
            recipients=config["recipients"],
            subject_prefix=config.get("subject_prefix", "[pipewatch]"),
        )
    return LogNotifier(level=config.get("level", "WARNING"))
