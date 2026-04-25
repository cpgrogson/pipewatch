from dataclasses import dataclass, field
from typing import Optional
from pipewatch.checker import Alert


@dataclass
class ClassificationRule:
    pipeline: str  # '*' for wildcard
    metric: str    # '*' for wildcard
    category: str
    description: str = ""

    def matches(self, alert: Alert) -> bool:
        pipeline_match = self.pipeline == "*" or self.pipeline == alert.pipeline
        metric_match = self.metric == "*" or self.metric == alert.metric
        return pipeline_match and metric_match


@dataclass
class ClassifiedAlert:
    alert: Alert
    category: str
    description: str = ""

    def __str__(self) -> str:
        base = str(self.alert)
        return f"[{self.category}] {base}" + (f" ({self.description})" if self.description else "")


class AlertClassifier:
    def __init__(self, rules: Optional[list[ClassificationRule]] = None):
        self._rules: list[ClassificationRule] = rules or []
        self._defaults: dict[str, str] = {
            "error_rate": "data_quality",
            "duration": "performance",
            "row_count": "volume",
        }

    def add_rule(self, rule: ClassificationRule) -> None:
        self._rules.append(rule)

    def classify(self, alert: Alert) -> ClassifiedAlert:
        for rule in self._rules:
            if rule.matches(alert):
                return ClassifiedAlert(
                    alert=alert,
                    category=rule.category,
                    description=rule.description,
                )
        # Fall back to metric-based default
        category = self._defaults.get(alert.metric, "unknown")
        return ClassifiedAlert(alert=alert, category=category)

    def classify_all(self, alerts: list[Alert]) -> list[ClassifiedAlert]:
        return [self.classify(a) for a in alerts]

    def group_by_category(self, alerts: list[Alert]) -> dict[str, list[ClassifiedAlert]]:
        result: dict[str, list[ClassifiedAlert]] = {}
        for classified in self.classify_all(alerts):
            result.setdefault(classified.category, []).append(classified)
        return result
