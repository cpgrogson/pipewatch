"""Alert streak tracking — counts consecutive occurrences of the same alert."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, Optional

from pipewatch.checker import Alert


@dataclass
class StreakEntry:
    pipeline: str
    metric: str
    severity: str
    count: int = 1

    def increment(self) -> None:
        self.count += 1

    def reset(self) -> None:
        self.count = 1

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "metric": self.metric,
            "severity": self.severity,
            "count": self.count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StreakEntry":
        return cls(
            pipeline=data["pipeline"],
            metric=data["metric"],
            severity=data["severity"],
            count=data["count"],
        )


class StreakStore:
    def __init__(self, path: str = ".pipewatch_streaks.json") -> None:
        self._path = path
        self._streaks: Dict[str, StreakEntry] = {}
        self._load()

    def _key(self, alert: Alert) -> str:
        return f"{alert.pipeline}::{alert.metric}"

    def _load(self) -> None:
        if os.path.exists(self._path):
            with open(self._path) as fh:
                raw = json.load(fh)
            self._streaks = {
                k: StreakEntry.from_dict(v) for k, v in raw.items()
            }

    def _save(self) -> None:
        with open(self._path, "w") as fh:
            json.dump(
                {k: v.to_dict() for k, v in self._streaks.items()}, fh, indent=2
            )

    def record(self, alert: Alert) -> StreakEntry:
        key = self._key(alert)
        if key in self._streaks:
            entry = self._streaks[key]
            if entry.severity == alert.severity:
                entry.increment()
            else:
                entry.severity = alert.severity
                entry.reset()
        else:
            self._streaks[key] = StreakEntry(
                pipeline=alert.pipeline,
                metric=alert.metric,
                severity=alert.severity,
            )
        self._save()
        return self._streaks[key]

    def get(self, alert: Alert) -> Optional[StreakEntry]:
        return self._streaks.get(self._key(alert))

    def clear(self, alert: Alert) -> None:
        key = self._key(alert)
        if key in self._streaks:
            del self._streaks[key]
            self._save()

    def all_entries(self) -> list:
        return list(self._streaks.values())
