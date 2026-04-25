from dataclasses import dataclass, field
from typing import Optional
from pipewatch.checker import Alert


@dataclass
class LabelRule:
    pipeline: str  # '*' for wildcard
    metric: str    # '*' for wildcard
    label_key: str
    label_value: str

    def matches(self, alert: Alert) -> bool:
        pipeline_match = self.pipeline == "*" or self.pipeline == alert.pipeline
        metric_match = self.metric == "*" or self.metric == alert.metric
        return pipeline_match and metric_match


@dataclass
class LabeledAlert:
    alert: Alert
    labels: dict = field(default_factory=dict)

    def __str__(self) -> str:
        label_str = ", ".join(f"{k}={v}" for k, v in self.labels.items())
        base = str(self.alert)
        return f"{base} [{label_str}]" if label_str else base


class AlertLabeler:
    def __init__(self, rules: Optional[list[LabelRule]] = None):
        self.rules: list[LabelRule] = rules or []

    def add_rule(self, rule: LabelRule) -> None:
        self.rules.append(rule)

    def label(self, alert: Alert) -> LabeledAlert:
        labels: dict = {}
        for rule in self.rules:
            if rule.matches(alert):
                labels[rule.label_key] = rule.label_value
        return LabeledAlert(alert=alert, labels=labels)

    def label_all(self, alerts: list[Alert]) -> list[LabeledAlert]:
        return [self.label(a) for a in alerts]
