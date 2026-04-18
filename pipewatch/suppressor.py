"""Alert suppression based on repeat/flap detection."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List
from pipewatch.checker import Alert


@dataclass
class SuppressionRule:
    pipeline: str
    metric: str
    min_occurrences: int = 3
    window_seconds: int = 300

    def key(self) -> str:
        return f"{self.pipeline}:{self.metric}"


@dataclass
class SuppressionStore:
    rules: List[SuppressionRule] = field(default_factory=list)
    _history: Dict[str, List[datetime]] = field(default_factory=dict)

    def add_rule(self, rule: SuppressionRule) -> None:
        self.rules.append(rule)

    def record(self, alert: Alert) -> None:
        key = f"{alert.pipeline}:{alert.metric}"
        now = datetime.utcnow()
        self._history.setdefault(key, []).append(now)

    def _matching_rule(self, alert: Alert) -> SuppressionRule | None:
        for rule in self.rules:
            if rule.pipeline in (alert.pipeline, "*") and rule.metric in (alert.metric, "*"):
                return rule
        return None

    def is_suppressed(self, alert: Alert) -> bool:
        rule = self._matching_rule(alert)
        if rule is None:
            return False
        key = f"{alert.pipeline}:{alert.metric}"
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=rule.window_seconds)
        recent = [t for t in self._history.get(key, []) if t >= cutoff]
        return len(recent) < rule.min_occurrences

    def filter_alerts(self, alerts: List[Alert]) -> List[Alert]:
        result = []
        for alert in alerts:
            self.record(alert)
            if not self.is_suppressed(alert):
                result.append(alert)
        return result
