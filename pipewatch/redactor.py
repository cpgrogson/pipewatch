"""Redactor: mask sensitive fields in alert messages before logging or sending."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.checker import Alert


@dataclass
class RedactionRule:
    """A rule that matches alert fields and masks sensitive content."""

    pattern: str
    replacement: str = "[REDACTED]"
    apply_to: str = "message"  # "message", "pipeline", or "metric"

    def apply(self, text: str) -> str:
        return re.sub(self.pattern, self.replacement, text)


@dataclass
class RedactedAlert:
    """An alert whose sensitive fields have been masked."""

    original: Alert
    pipeline: str
    metric: str
    message: str
    severity: str
    redacted_fields: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        tag = f"[{self.severity.upper()}]" if self.severity else ""
        return f"{tag} {self.pipeline}/{self.metric}: {self.message}"


class AlertRedactor:
    """Applies redaction rules to alerts, masking sensitive content."""

    def __init__(self, rules: Optional[List[RedactionRule]] = None) -> None:
        self.rules: List[RedactionRule] = rules or []

    def add_rule(self, rule: RedactionRule) -> None:
        self.rules.append(rule)

    def redact(self, alert: Alert) -> RedactedAlert:
        pipeline = alert.pipeline
        metric = alert.metric
        message = alert.message
        redacted: List[str] = []

        for rule in self.rules:
            if rule.apply_to == "message":
                new_msg = rule.apply(message)
                if new_msg != message:
                    message = new_msg
                    redacted.append("message")
            elif rule.apply_to == "pipeline":
                new_p = rule.apply(pipeline)
                if new_p != pipeline:
                    pipeline = new_p
                    redacted.append("pipeline")
            elif rule.apply_to == "metric":
                new_m = rule.apply(metric)
                if new_m != metric:
                    metric = new_m
                    redacted.append("metric")

        return RedactedAlert(
            original=alert,
            pipeline=pipeline,
            metric=metric,
            message=message,
            severity=alert.severity,
            redacted_fields=list(set(redacted)),
        )

    def redact_all(self, alerts: List[Alert]) -> List[RedactedAlert]:
        return [self.redact(a) for a in alerts]
