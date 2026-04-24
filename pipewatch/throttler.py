"""Alert throttling: limit how frequently the same alert is re-sent."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from pipewatch.checker import Alert

DEFAULT_THROTTLE_PATH = ".pipewatch_throttle.json"


@dataclass
class ThrottleRule:
    pipeline: str          # '*' for wildcard
    metric: str            # '*' for wildcard
    interval_seconds: int  # minimum seconds between repeated alerts

    def key(self) -> str:
        return f"{self.pipeline}:{self.metric}"

    def matches(self, alert: Alert) -> bool:
        pipeline_match = self.pipeline == "*" or self.pipeline == alert.pipeline
        metric_match = self.metric == "*" or self.metric == alert.metric
        return pipeline_match and metric_match


@dataclass
class ThrottleRecord:
    last_sent: float = field(default_factory=time.time)

    def is_throttled(self, interval_seconds: int) -> bool:
        return (time.time() - self.last_sent) < interval_seconds

    def reset(self) -> None:
        self.last_sent = time.time()

    def to_dict(self) -> dict:
        return {"last_sent": self.last_sent}

    @classmethod
    def from_dict(cls, data: dict) -> "ThrottleRecord":
        return cls(last_sent=data["last_sent"])


class ThrottlerStore:
    def __init__(self, path: str = DEFAULT_THROTTLE_PATH):
        self._path = Path(path)
        self._rules: list[ThrottleRule] = []
        self._records: Dict[str, ThrottleRecord] = self._load()

    def _load(self) -> Dict[str, ThrottleRecord]:
        if not self._path.exists():
            return {}
        try:
            raw = json.loads(self._path.read_text())
            return {k: ThrottleRecord.from_dict(v) for k, v in raw.items()}
        except (json.JSONDecodeError, KeyError):
            return {}

    def _save(self) -> None:
        self._path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._records.items()}, indent=2)
        )

    def add_rule(self, rule: ThrottleRule) -> None:
        self._rules.append(rule)

    def _matching_rule(self, alert: Alert) -> Optional[ThrottleRule]:
        for rule in self._rules:
            if rule.matches(alert):
                return rule
        return None

    def is_throttled(self, alert: Alert) -> bool:
        rule = self._matching_rule(alert)
        if rule is None:
            return False
        record_key = f"{alert.pipeline}:{alert.metric}"
        record = self._records.get(record_key)
        if record is None:
            return False
        return record.is_throttled(rule.interval_seconds)

    def record(self, alert: Alert) -> None:
        record_key = f"{alert.pipeline}:{alert.metric}"
        rec = self._records.get(record_key)
        if rec is None:
            self._records[record_key] = ThrottleRecord()
        else:
            rec.reset()
        self._save()

    def clear(self) -> None:
        self._rules.clear()
        self._records.clear()
        if self._path.exists():
            self._path.unlink()
