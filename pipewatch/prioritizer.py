from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pipewatch.checker import Alert


PRIORITY_LEVELS = {"critical": 3, "high": 2, "medium": 1, "low": 0}


@dataclass
class PriorityRule:
    severity: str
    pipeline: Optional[str] = None
    metric: Optional[str] = None
    priority: str = "medium"

    def matches(self, alert: Alert) -> bool:
        if self.severity and alert.severity != self.severity:
            return False
        if self.pipeline and alert.pipeline != self.pipeline:
            return False
        if self.metric and alert.metric != self.metric:
            return False
        return True


@dataclass
class PrioritizedAlert:
    alert: Alert
    priority: str
    score: int

    def __str__(self) -> str:
        return f"[{self.priority.upper()}] {self.alert}"


class AlertPrioritizer:
    def __init__(self, rules: Optional[List[PriorityRule]] = None) -> None:
        self._rules: List[PriorityRule] = rules or []

    def add_rule(self, rule: PriorityRule) -> None:
        self._rules.append(rule)

    def _resolve_priority(self, alert: Alert) -> str:
        for rule in reversed(self._rules):
            if rule.matches(alert):
                return rule.priority
        if alert.severity == "critical":
            return "critical"
        if alert.severity == "warning":
            return "medium"
        return "low"

    def prioritize(self, alerts: List[Alert]) -> List[PrioritizedAlert]:
        prioritized = []
        for alert in alerts:
            priority = self._resolve_priority(alert)
            score = PRIORITY_LEVELS.get(priority, 0)
            prioritized.append(PrioritizedAlert(alert=alert, priority=priority, score=score))
        return sorted(prioritized, key=lambda p: p.score, reverse=True)

    def top(self, alerts: List[Alert], n: int = 5) -> List[PrioritizedAlert]:
        return self.prioritize(alerts)[:n]

    def group_by_priority(self, alerts: List[Alert]) -> Dict[str, List[PrioritizedAlert]]:
        groups: Dict[str, List[PrioritizedAlert]] = {k: [] for k in PRIORITY_LEVELS}
        for pa in self.prioritize(alerts):
            groups.setdefault(pa.priority, []).append(pa)
        return groups
