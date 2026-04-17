"""Persist and retrieve pipeline check run history."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class HistoryEntry:
    pipeline_name: str
    checked_at: str
    alert_count: int
    healthy: bool
    tags: List[str] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict) -> "HistoryEntry":
        return HistoryEntry(
            pipeline_name=d["pipeline_name"],
            checked_at=d["checked_at"],
            alert_count=d["alert_count"],
            healthy=d["healthy"],
            tags=d.get("tags", []),
        )


class HistoryStore:
    def __init__(self, path: str = ".pipewatch_history.json"):
        self.path = path
        self._entries: List[HistoryEntry] = []
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                raw = json.load(f)
            self._entries = [HistoryEntry.from_dict(r) for r in raw]

    def save(self) -> None:
        with open(self.path, "w") as f:
            json.dump([asdict(e) for e in self._entries], f, indent=2)

    def record(self, entry: HistoryEntry) -> None:
        self._entries.append(entry)
        self.save()

    def all(self) -> List[HistoryEntry]:
        return list(self._entries)

    def for_pipeline(self, name: str) -> List[HistoryEntry]:
        return [e for e in self._entries if e.pipeline_name == name]

    def last(self, name: str) -> Optional[HistoryEntry]:
        entries = self.for_pipeline(name)
        return entries[-1] if entries else None

    def clear(self) -> None:
        self._entries = []
        self.save()
