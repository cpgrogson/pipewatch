"""Alert resolver: marks alerts as resolved and tracks resolution history."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from pipewatch.checker import Alert

DEFAULT_STORE_PATH = ".pipewatch_resolutions.json"


@dataclass
class ResolutionEntry:
    pipeline: str
    metric: str
    resolved_at: str
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "metric": self.metric,
            "resolved_at": self.resolved_at,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ResolutionEntry":
        return cls(
            pipeline=data["pipeline"],
            metric=data["metric"],
            resolved_at=data["resolved_at"],
            note=data.get("note", ""),
        )

    @classmethod
    def from_alert(cls, alert: Alert, note: str = "") -> "ResolutionEntry":
        return cls(
            pipeline=alert.pipeline,
            metric=alert.metric,
            resolved_at=datetime.now(timezone.utc).isoformat(),
            note=note,
        )

    def is_resolved(self, pipeline: str, metric: str) -> bool:
        return self.pipeline == pipeline and self.metric == metric


class ResolutionStore:
    def __init__(self, path: str = DEFAULT_STORE_PATH):
        self._path = path
        self._entries: list[ResolutionEntry] = self._load()

    def _load(self) -> list[ResolutionEntry]:
        if not os.path.exists(self._path):
            return []
        with open(self._path) as f:
            return [ResolutionEntry.from_dict(d) for d in json.load(f)]

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump([e.to_dict() for e in self._entries], f, indent=2)

    def resolve(self, alert: Alert, note: str = "") -> ResolutionEntry:
        entry = ResolutionEntry.from_alert(alert, note=note)
        self._entries.append(entry)
        self._save()
        return entry

    def is_resolved(self, pipeline: str, metric: str) -> bool:
        return any(e.is_resolved(pipeline, metric) for e in self._entries)

    def all(self) -> list[ResolutionEntry]:
        return list(self._entries)

    def clear(self) -> None:
        self._entries = []
        self._save()

    def filter_unresolved(self, alerts: list[Alert]) -> list[Alert]:
        return [
            a for a in alerts
            if not self.is_resolved(a.pipeline, a.metric)
        ]
