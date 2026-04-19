from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional
import json
import os


@dataclass
class RateLimitRule:
    pipeline: str
    metric: str
    max_alerts: int = 3
    window_seconds: int = 3600

    def key(self) -> str:
        return f"{self.pipeline}:{self.metric}"


@dataclass
class RateLimitRecord:
    timestamps: list = field(default_factory=list)

    def prune(self, window_seconds: int):
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        self.timestamps = [t for t in self.timestamps if t > cutoff]

    def count(self) -> int:
        return len(self.timestamps)

    def record(self):
        self.timestamps.append(datetime.utcnow())


class RateLimiterStore:
    def __init__(self, path: str = ".pipewatch_ratelimits.json"):
        self.path = path
        self._rules: Dict[str, RateLimitRule] = {}
        self._records: Dict[str, RateLimitRecord] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path) as f:
                data = json.load(f)
            for r in data.get("rules", []):
                rule = RateLimitRule(**r)
                self._rules[rule.key()] = rule

    def _save(self):
        with open(self.path, "w") as f:
            json.dump({"rules": [vars(r) for r in self._rules.values()]}, f)

    def add_rule(self, rule: RateLimitRule):
        self._rules[rule.key()] = rule
        self._save()

    def clear(self):
        self._rules.clear()
        self._records.clear()
        if os.path.exists(self.path):
            os.remove(self.path)

    def is_rate_limited(self, pipeline: str, metric: str) -> bool:
        key = f"{pipeline}:{metric}"
        rule = self._rules.get(key) or self._rules.get(f"*:{metric}") or self._rules.get(f"{pipeline}:*")
        if rule is None:
            return False
        record = self._records.setdefault(key, RateLimitRecord())
        record.prune(rule.window_seconds)
        if record.count() >= rule.max_alerts:
            return True
        record.record()
        return False

    def list_rules(self):
        return list(self._rules.values())
