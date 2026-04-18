"""Silence/suppress alerts matching configurable rules."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
from pipewatch.checker import Alert


@dataclass
class SilenceRule:
    pipeline: Optional[str] = None  # None means match all
    metric: Optional[str] = None    # None means match all
    until: Optional[datetime] = None
    reason: str = ""

    def is_active(self) -> bool:
        if self.until is None:
            return True
        return datetime.utcnow() < self.until

    def matches(self, alert: Alert) -> bool:
        if not self.is_active():
            return False
        if self.pipeline and alert.pipeline != self.pipeline:
            return False
        if self.metric and alert.metric != self.metric:
            return False
        return True


@dataclass
class SilenceStore:
    rules: List[SilenceRule] = field(default_factory=list)

    def add(self, rule: SilenceRule) -> None:
        self.rules.append(rule)

    def remove_expired(self) -> int:
        before = len(self.rules)
        self.rules = [r for r in self.rules if r.is_active()]
        return before - len(self.rules)

    def is_silenced(self, alert: Alert) -> bool:
        return any(r.matches(alert) for r in self.rules)

    def filter_alerts(self, alerts: List[Alert]) -> List[Alert]:
        return [a for a in alerts if not self.is_silenced(a)]

    def active_rules(self) -> List[SilenceRule]:
        return [r for r in self.rules if r.is_active()]


def silence_for(pipeline: str, metric: str, hours: float, reason: str = "") -> SilenceRule:
    until = datetime.utcnow() + timedelta(hours=hours)
    return SilenceRule(pipeline=pipeline, metric=metric, until=until, reason=reason)
