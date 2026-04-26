"""Alert muter: temporarily suppress alerts for a pipeline/metric pair with optional expiry."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from pipewatch.checker import Alert

DEFAULT_STORE = os.path.join(os.path.expanduser("~"), ".pipewatch", "mutes.json")


@dataclass
class MuteRule:
    pipeline: str  # "*" matches any pipeline
    metric: str    # "*" matches any metric
    expires_at: Optional[datetime] = None  # None means indefinite

    def is_active(self) -> bool:
        if self.expires_at is None:
            return True
        return datetime.now(tz=timezone.utc) < self.expires_at

    def matches(self, alert: Alert) -> bool:
        pipeline_match = self.pipeline == "*" or self.pipeline == alert.pipeline
        metric_match = self.metric == "*" or self.metric == alert.metric
        return pipeline_match and metric_match and self.is_active()

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "metric": self.metric,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MuteRule":
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])
        return cls(
            pipeline=data["pipeline"],
            metric=data["metric"],
            expires_at=expires_at,
        )


class MuteStore:
    def __init__(self, path: str = DEFAULT_STORE):
        self._path = path
        self._rules: list[MuteRule] = self._load()

    def _load(self) -> list[MuteRule]:
        if not os.path.exists(self._path):
            return []
        with open(self._path) as f:
            return [MuteRule.from_dict(d) for d in json.load(f)]

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w") as f:
            json.dump([r.to_dict() for r in self._rules], f, indent=2)

    def add(self, rule: MuteRule) -> None:
        self._rules.append(rule)
        self._save()

    def is_muted(self, alert: Alert) -> bool:
        return any(r.matches(alert) for r in self._rules)

    def prune_expired(self) -> int:
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.is_active()]
        self._save()
        return before - len(self._rules)

    def clear(self) -> None:
        self._rules = []
        self._save()

    def all_rules(self) -> list[MuteRule]:
        return list(self._rules)

    def filter_alerts(self, alerts: list[Alert]) -> list[Alert]:
        return [a for a in alerts if not self.is_muted(a)]
