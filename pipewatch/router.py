from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.checker import Alert
from pipewatch.notifier import NotifierBackend, LogNotifier


@dataclass
class RoutingRule:
    name: str
    severities: List[str] = field(default_factory=list)
    pipelines: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    notifier: NotifierBackend = field(default_factory=LogNotifier)

    def matches(self, alert: Alert) -> bool:
        if self.severities and alert.severity not in self.severities:
            return False
        if self.pipelines and alert.pipeline not in self.pipelines:
            return False
        return True


@dataclass
class AlertRouter:
    rules: List[RoutingRule] = field(default_factory=list)
    fallback: Optional[NotifierBackend] = field(default_factory=LogNotifier)

    def add_rule(self, rule: RoutingRule) -> None:
        self.rules.append(rule)

    def route(self, alerts: List[Alert]) -> None:
        routed: dict = {}
        unrouted: List[Alert] = []

        for alert in alerts:
            matched = False
            for rule in self.rules:
                if rule.matches(alert):
                    routed.setdefault(id(rule.notifier), (rule.notifier, []))
                    routed[id(rule.notifier)][1].append(alert)
                    matched = True
                    break
            if not matched:
                unrouted.append(alert)

        for _, (notifier, batch) in routed.items():
            notifier.send(batch)

        if unrouted and self.fallback:
            self.fallback.send(unrouted)
