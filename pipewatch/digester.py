"""digester.py — Produce periodic digest summaries of alerts across pipelines.

A digest groups alerts over a time window and produces a concise summary
suitable for batched notification (e.g. hourly email digests instead of
per-alert noise).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pipewatch.checker import Alert


@dataclass
class DigestEntry:
    """A single alert captured for inclusion in a digest."""

    pipeline: str
    metric: str
    severity: str
    message: str
    captured_at: datetime

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "metric": self.metric,
            "severity": self.severity,
            "message": self.message,
            "captured_at": self.captured_at.isoformat(),
        }

    @staticmethod
    def from_dict(d: dict) -> "DigestEntry":
        return DigestEntry(
            pipeline=d["pipeline"],
            metric=d["metric"],
            severity=d["severity"],
            message=d["message"],
            captured_at=datetime.fromisoformat(d["captured_at"]),
        )


@dataclass
class Digest:
    """A summary of alerts collected within a specific time window."""

    window_start: datetime
    window_end: datetime
    entries: List[DigestEntry] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.entries)

    @property
    def critical_count(self) -> int:
        return sum(1 for e in self.entries if e.severity == "critical")

    @property
    def warning_count(self) -> int:
        return sum(1 for e in self.entries if e.severity == "warning")

    def by_pipeline(self) -> Dict[str, List[DigestEntry]]:
        """Group entries by pipeline name."""
        result: Dict[str, List[DigestEntry]] = {}
        for entry in self.entries:
            result.setdefault(entry.pipeline, []).append(entry)
        return result

    def summary(self) -> str:
        lines = [
            f"Digest [{self.window_start.isoformat()} -> {self.window_end.isoformat()}]",
            f"  Total alerts : {self.total}",
            f"  Critical     : {self.critical_count}",
            f"  Warning      : {self.warning_count}",
        ]
        for pipeline, entries in self.by_pipeline().items():
            lines.append(f"  {pipeline}: {len(entries)} alert(s)")
        return "\n".join(lines)


class DigestStore:
    """Persists pending digest entries to disk and flushes them into a Digest."""

    def __init__(self, path: str = ".pipewatch_digest.json"):
        self._path = path
        self._entries: List[DigestEntry] = self._load()

    def _load(self) -> List[DigestEntry]:
        if not os.path.exists(self._path):
            return []
        try:
            with open(self._path, "r") as fh:
                raw = json.load(fh)
            return [DigestEntry.from_dict(d) for d in raw]
        except (json.JSONDecodeError, KeyError):
            return []

    def _save(self) -> None:
        with open(self._path, "w") as fh:
            json.dump([e.to_dict() for e in self._entries], fh, indent=2)

    def add(self, alert: Alert, captured_at: Optional[datetime] = None) -> None:
        """Record an alert for the next digest."""
        entry = DigestEntry(
            pipeline=alert.pipeline,
            metric=alert.metric,
            severity=alert.severity,
            message=alert.message,
            captured_at=captured_at or datetime.utcnow(),
        )
        self._entries.append(entry)
        self._save()

    def flush(self, window_minutes: int = 60) -> Digest:
        """Consume all pending entries and return a Digest for the given window."""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        digest = Digest(
            window_start=window_start,
            window_end=now,
            entries=list(self._entries),
        )
        self._entries = []
        self._save()
        return digest

    def pending_count(self) -> int:
        """Number of alerts waiting to be included in the next digest."""
        return len(self._entries)
