"""Alert archiver: move resolved or expired alerts into a long-term archive store."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from pipewatch.checker import Alert

_DEFAULT_PATH = ".pipewatch_archive.json"


@dataclass
class ArchivedAlert:
    pipeline: str
    metric: str
    severity: str
    message: str
    archived_at: str
    reason: str = "manual"

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "metric": self.metric,
            "severity": self.severity,
            "message": self.message,
            "archived_at": self.archived_at,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ArchivedAlert":
        return cls(**d)

    @classmethod
    def from_alert(cls, alert: Alert, reason: str = "manual") -> "ArchivedAlert":
        return cls(
            pipeline=alert.pipeline,
            metric=alert.metric,
            severity=alert.severity,
            message=alert.message,
            archived_at=datetime.now(timezone.utc).isoformat(),
            reason=reason,
        )


class ArchiveStore:
    def __init__(self, path: str = _DEFAULT_PATH) -> None:
        self._path = path
        self._entries: List[ArchivedAlert] = self._load()

    def _load(self) -> List[ArchivedAlert]:
        if not os.path.exists(self._path):
            return []
        with open(self._path) as fh:
            return [ArchivedAlert.from_dict(d) for d in json.load(fh)]

    def _save(self) -> None:
        with open(self._path, "w") as fh:
            json.dump([e.to_dict() for e in self._entries], fh, indent=2)

    def archive(self, alert: Alert, reason: str = "manual") -> ArchivedAlert:
        entry = ArchivedAlert.from_alert(alert, reason=reason)
        self._entries.append(entry)
        self._save()
        return entry

    def all(self) -> List[ArchivedAlert]:
        return list(self._entries)

    def filter_by_pipeline(self, pipeline: str) -> List[ArchivedAlert]:
        return [e for e in self._entries if e.pipeline == pipeline]

    def clear(self) -> None:
        self._entries = []
        self._save()
