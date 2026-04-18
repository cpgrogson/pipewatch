"""Alert deduplication: suppress repeated alerts within a cooldown window."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional

from pipewatch.checker import Alert


@dataclass
class DeduplicationRule:
    cooldown_minutes: int = 30

    def cooldown(self) -> timedelta:
        return timedelta(minutes=self.cooldown_minutes)


@dataclass
class DeduplicatorStore:
    rule: DeduplicationRule = field(default_factory=DeduplicationRule)
    _seen: Dict[str, datetime] = field(default_factory=dict, init=False)

    def _key(self, alert: Alert) -> str:
        return f"{alert.pipeline}:{alert.metric}"

    def is_duplicate(self, alert: Alert, now: Optional[datetime] = None) -> bool:
        """Return True if this alert was already seen within the cooldown window."""
        now = now or datetime.utcnow()
        key = self._key(alert)
        last = self._seen.get(key)
        if last is None:
            return False
        return (now - last) < self.rule.cooldown()

    def record(self, alert: Alert, now: Optional[datetime] = None) -> None:
        """Record the alert as seen at the given time."""
        now = now or datetime.utcnow()
        self._seen[self._key(alert)] = now

    def filter_alerts(self, alerts: list[Alert], now: Optional[datetime] = None) -> list[Alert]:
        """Return only alerts that are not duplicates, recording new ones."""
        now = now or datetime.utcnow()
        result = []
        for alert in alerts:
            if not self.is_duplicate(alert, now):
                self.record(alert, now)
                result.append(alert)
        return result

    def clear(self) -> None:
        self._seen.clear()
