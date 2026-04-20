"""Auto-tagging module: applies tag rules to alerts based on pipeline and metric patterns."""

from dataclasses import dataclass, field
from typing import Optional
from pipewatch.checker import Alert


@dataclass
class TagRule:
    pipeline: str  # '*' for wildcard
    metric: str    # '*' for wildcard
    tags: list[str] = field(default_factory=list)

    def matches(self, alert: Alert) -> bool:
        pipeline_match = self.pipeline == "*" or self.pipeline == alert.pipeline
        metric_match = self.metric == "*" or self.metric == alert.metric
        return pipeline_match and metric_match


@dataclass
class TaggedAlert:
    alert: Alert
    tags: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        tag_str = ", ".join(self.tags) if self.tags else "none"
        return f"{self.alert} [tags: {tag_str}]"


class AlertTagger:
    def __init__(self) -> None:
        self._rules: list[TagRule] = []

    def add_rule(self, rule: TagRule) -> None:
        self._rules.append(rule)

    def tag(self, alert: Alert) -> TaggedAlert:
        collected: list[str] = []
        for rule in self._rules:
            if rule.matches(alert):
                for t in rule.tags:
                    if t not in collected:
                        collected.append(t)
        return TaggedAlert(alert=alert, tags=collected)

    def tag_all(self, alerts: list[Alert]) -> list[TaggedAlert]:
        return [self.tag(a) for a in alerts]

    def rules(self) -> list[TagRule]:
        return list(self._rules)

    def clear(self) -> None:
        self._rules.clear()
