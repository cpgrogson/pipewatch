"""Alert auditing: record every alert event with timestamps and outcomes."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from pipewatch.checker import Alert

DEFAULT_AUDIT_PATH = ".pipewatch_audit.json"


@dataclass
class AuditEntry:
    pipeline: str
    metric: str
    severity: str
    message: str
    outcome: str  # e.g. "notified", "suppressed", "deduplicated", "silenced"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "metric": self.metric,
            "severity": self.severity,
            "message": self.message,
            "outcome": self.outcome,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            pipeline=data["pipeline"],
            metric=data["metric"],
            severity=data["severity"],
            message=data["message"],
            outcome=data["outcome"],
            timestamp=data["timestamp"],
        )

    @classmethod
    def from_alert(cls, alert: Alert, outcome: str) -> "AuditEntry":
        return cls(
            pipeline=alert.pipeline,
            metric=alert.metric,
            severity=alert.severity,
            message=str(alert),
            outcome=outcome,
        )


class AuditStore:
    def __init__(self, path: str = DEFAULT_AUDIT_PATH):
        self._path = path
        self._entries: List[AuditEntry] = self._load()

    def _load(self) -> List[AuditEntry]:
        if not os.path.exists(self._path):
            return []
        with open(self._path) as f:
            return [AuditEntry.from_dict(d) for d in json.load(f)]

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump([e.to_dict() for e in self._entries], f, indent=2)

    def record(self, alert: Alert, outcome: str) -> AuditEntry:
        entry = AuditEntry.from_alert(alert, outcome)
        self._entries.append(entry)
        self._save()
        return entry

    def all(self) -> List[AuditEntry]:
        return list(self._entries)

    def for_pipeline(self, pipeline: str) -> List[AuditEntry]:
        return [e for e in self._entries if e.pipeline == pipeline]

    def for_outcome(self, outcome: str) -> List[AuditEntry]:
        return [e for e in self._entries if e.outcome == outcome]

    def clear(self) -> None:
        self._entries = []
        self._save()
