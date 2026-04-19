from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pipewatch.checker import Alert


@dataclass
class EscalationRule:
    pipeline: str
    metric: str
    repeat_window_minutes: int = 30
    max_escalations: int = 3

    def key(self) -> str:
        return f"{self.pipeline}:{self.metric}"


@dataclass
class EscalationRecord:
    first_seen: datetime
    last_seen: datetime
    count: int = 1

    def increment(self, now: datetime) -> None:
        self.last_seen = now
        self.count += 1


@dataclass
class EscalationStore:
    rules: List[EscalationRule] = field(default_factory=list)
    _records: Dict[str, EscalationRecord] = field(default_factory=dict)

    def add_rule(self, rule: EscalationRule) -> None:
        self.rules.append(rule)

    def _find_rule(self, alert: Alert) -> Optional[EscalationRule]:
        for rule in self.rules:
            if rule.pipeline == alert.pipeline and rule.metric == alert.metric:
                return rule
        return None

    def record(self, alert: Alert, now: Optional[datetime] = None) -> bool:
        """Returns True if alert should be escalated."""
        now = now or datetime.utcnow()
        rule = self._find_rule(alert)
        if rule is None:
            return False

        key = rule.key()
        window = timedelta(minutes=rule.repeat_window_minutes)

        if key not in self._records:
            self._records[key] = EscalationRecord(first_seen=now, last_seen=now)
            return False

        rec = self._records[key]
        if now - rec.last_seen > window:
            self._records[key] = EscalationRecord(first_seen=now, last_seen=now)
            return False

        rec.increment(now)
        return rec.count >= rule.max_escalations

    def clear(self) -> None:
        self._records.clear()
