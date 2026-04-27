"""Alert fingerprinting: generate stable identifiers for dedup and tracking."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional

from pipewatch.checker import Alert


@dataclass
class FingerprintedAlert:
    alert: Alert
    fingerprint: str
    version: int = 1

    def __str__(self) -> str:
        return f"[{self.fingerprint[:8]}] {self.alert}"


@dataclass
class FingerprintRule:
    include_pipeline: bool = True
    include_metric: bool = True
    include_severity: bool = True
    include_message: bool = False
    salt: str = ""


class AlertFingerprinter:
    def __init__(self, rule: Optional[FingerprintRule] = None) -> None:
        self.rule = rule or FingerprintRule()

    def fingerprint(self, alert: Alert) -> FingerprintedAlert:
        parts: dict = {}
        r = self.rule
        if r.include_pipeline:
            parts["pipeline"] = alert.pipeline
        if r.include_metric:
            parts["metric"] = alert.metric
        if r.include_severity:
            parts["severity"] = alert.severity
        if r.include_message:
            parts["message"] = alert.message
        if r.salt:
            parts["_salt"] = r.salt
        raw = json.dumps(parts, sort_keys=True)
        digest = hashlib.sha256(raw.encode()).hexdigest()
        return FingerprintedAlert(alert=alert, fingerprint=digest)

    def fingerprint_all(
        self, alerts: list[Alert]
    ) -> list[FingerprintedAlert]:
        return [self.fingerprint(a) for a in alerts]
