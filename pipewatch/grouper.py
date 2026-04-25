"""Alert grouping: batch related alerts into named groups for cleaner reporting."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pipewatch.checker import Alert


@dataclass
class GroupRule:
    group_name: str
    pipeline: str = "*"
    metric: str = "*"
    severity: str = "*"

    def matches(self, alert: Alert) -> bool:
        pipeline_ok = self.pipeline == "*" or self.pipeline == alert.pipeline
        metric_ok = self.metric == "*" or self.metric == alert.metric
        severity_ok = self.severity == "*" or self.severity == alert.severity
        return pipeline_ok and metric_ok and severity_ok


@dataclass
class AlertGroup:
    name: str
    alerts: List[Alert] = field(default_factory=list)

    def size(self) -> int:
        return len(self.alerts)

    def severities(self) -> List[str]:
        return list({a.severity for a in self.alerts})

    def pipelines(self) -> List[str]:
        return list({a.pipeline for a in self.alerts})

    def summary(self) -> str:
        return (
            f"Group '{self.name}': {self.size()} alert(s) across "
            f"{len(self.pipelines())} pipeline(s), "
            f"severities={self.severities()}"
        )


class AlertGrouper:
    def __init__(self, rules: Optional[List[GroupRule]] = None, fallback: str = "ungrouped"):
        self.rules: List[GroupRule] = rules or []
        self.fallback = fallback

    def add_rule(self, rule: GroupRule) -> None:
        self.rules.append(rule)

    def group(self, alerts: List[Alert]) -> Dict[str, AlertGroup]:
        groups: Dict[str, AlertGroup] = {}
        for alert in alerts:
            name = self._match(alert)
            if name not in groups:
                groups[name] = AlertGroup(name=name)
            groups[name].alerts.append(alert)
        return groups

    def _match(self, alert: Alert) -> str:
        for rule in self.rules:
            if rule.matches(alert):
                return rule.group_name
        return self.fallback
