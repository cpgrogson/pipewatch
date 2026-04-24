"""Alert retry tracking — re-queue alerts that failed to notify."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from pipewatch.checker import Alert

DEFAULT_STORE = Path(".pipewatch_retries.json")
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF = 60  # seconds


@dataclass
class RetryEntry:
    pipeline: str
    metric: str
    severity: str
    message: str
    attempts: int = 0
    next_retry_at: float = field(default_factory=time.time)
    max_attempts: int = DEFAULT_MAX_ATTEMPTS

    def is_ready(self) -> bool:
        return time.time() >= self.next_retry_at

    def is_exhausted(self) -> bool:
        return self.attempts >= self.max_attempts

    def increment(self, backoff: float = DEFAULT_BACKOFF) -> None:
        self.attempts += 1
        self.next_retry_at = time.time() + backoff * self.attempts

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "metric": self.metric,
            "severity": self.severity,
            "message": self.message,
            "attempts": self.attempts,
            "next_retry_at": self.next_retry_at,
            "max_attempts": self.max_attempts,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RetryEntry":
        return cls(**data)

    @classmethod
    def from_alert(cls, alert: Alert, max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> "RetryEntry":
        return cls(
            pipeline=alert.pipeline,
            metric=alert.metric,
            severity=alert.severity,
            message=str(alert),
            max_attempts=max_attempts,
        )


class RetryStore:
    def __init__(self, path: Path = DEFAULT_STORE) -> None:
        self._path = path
        self._entries: List[RetryEntry] = self._load()

    def _load(self) -> List[RetryEntry]:
        if not self._path.exists():
            return []
        with open(self._path) as f:
            return [RetryEntry.from_dict(d) for d in json.load(f)]

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump([e.to_dict() for e in self._entries], f, indent=2)

    def enqueue(self, alert: Alert, max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> RetryEntry:
        entry = RetryEntry.from_alert(alert, max_attempts=max_attempts)
        self._entries.append(entry)
        self._save()
        return entry

    def due(self) -> List[RetryEntry]:
        return [e for e in self._entries if e.is_ready() and not e.is_exhausted()]

    def mark_attempted(self, entry: RetryEntry, backoff: float = DEFAULT_BACKOFF) -> None:
        entry.increment(backoff)
        self._entries = [e for e in self._entries if not e.is_exhausted()]
        self._save()

    def clear(self) -> None:
        self._entries = []
        self._save()

    def all(self) -> List[RetryEntry]:
        return list(self._entries)
