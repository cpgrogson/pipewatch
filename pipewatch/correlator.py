"""Alert correlation: group related alerts across pipelines into incidents."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

from pipewatch.checker import Alert


@dataclass
class Incident:
    incident_id: str
    alerts: List[Alert] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def pipelines(self) -> List[str]:
        return list({a.pipeline for a in self.alerts})

    @property
    def metrics(self) -> List[str]:
        return list({a.metric for a in self.alerts})

    @property
    def severities(self) -> List[str]:
        return list({a.severity for a in self.alerts})

    @property
    def size(self) -> int:
        return len(self.alerts)

    def summary(self) -> str:
        return (
            f"Incident '{self.incident_id}': {self.size} alert(s) across "
            f"{len(self.pipelines)} pipeline(s) — metrics: {', '.join(self.metrics)}"
        )


@dataclass
class CorrelationRule:
    group_by: str  # 'metric' | 'severity' | 'pipeline'
    min_alerts: int = 2


VALID_GROUP_BY_FIELDS = frozenset({"metric", "severity", "pipeline"})


class AlertCorrelator:
    def __init__(self, rules: Optional[List[CorrelationRule]] = None):
        self.rules: List[CorrelationRule] = rules or []
        self._validate_rules()

    def _validate_rules(self) -> None:
        """Raise ValueError if any rule references an unsupported group_by field."""
        for rule in self.rules:
            if rule.group_by not in VALID_GROUP_BY_FIELDS:
                raise ValueError(
                    f"Invalid group_by field '{rule.group_by}'. "
                    f"Must be one of: {', '.join(sorted(VALID_GROUP_BY_FIELDS))}"
                )
            if rule.min_alerts < 1:
                raise ValueError(
                    f"min_alerts must be at least 1, got {rule.min_alerts}"
                )

    def correlate(self, alerts: List[Alert]) -> List[Incident]:
        """Group alerts into incidents based on configured rules."""
        if not alerts or not self.rules:
            return []

        incidents: List[Incident] = []
        for rule in self.rules:
            groups: Dict[str, List[Alert]] = {}
            for alert in alerts:
                key = getattr(alert, rule.group_by, None)
                if key is None:
                    continue
                groups.setdefault(key, []).append(alert)

            for group_key, group_alerts in groups.items():
                if len(group_alerts) >= rule.min_alerts:
                    incident_id = f"{rule.group_by}:{group_key}"
                    # avoid duplicate incidents with same id
                    existing_ids = {i.incident_id for i in incidents}
                    if incident_id not in existing_ids:
                        incidents.append(
                            Incident(incident_id=incident_id, alerts=group_alerts)
                        )
        return incidents
