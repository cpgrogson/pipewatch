"""Alert severity scorer — assigns a numeric score to alerts based on metric type,
severity level, and configurable weights for downstream prioritization."""

from dataclasses import dataclass, field
from typing import Dict, Optional
from pipewatch.checker import Alert


DEFAULT_SEVERITY_WEIGHTS: Dict[str, float] = {
    "critical": 10.0,
    "warning": 5.0,
    "info": 1.0,
}

DEFAULT_METRIC_WEIGHTS: Dict[str, float] = {
    "error_rate": 3.0,
    "duration": 2.0,
    "row_count": 1.5,
}


@dataclass
class ScoredAlert:
    alert: Alert
    score: float

    def __str__(self) -> str:
        return (
            f"[score={self.score:.2f}] {self.alert.pipeline} | "
            f"{self.alert.metric} | {self.alert.severity}"
        )


@dataclass
class AlertScorer:
    severity_weights: Dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_SEVERITY_WEIGHTS)
    )
    metric_weights: Dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_METRIC_WEIGHTS)
    )

    def score(self, alert: Alert) -> ScoredAlert:
        severity_score = self.severity_weights.get(alert.severity.lower(), 1.0)
        metric_score = self.metric_weights.get(alert.metric.lower(), 1.0)
        total = round(severity_score * metric_score, 4)
        return ScoredAlert(alert=alert, score=total)

    def score_all(self, alerts: list[Alert]) -> list[ScoredAlert]:
        scored = [self.score(a) for a in alerts]
        return sorted(scored, key=lambda s: s.score, reverse=True)

    def top(self, alerts: list[Alert], n: int = 5) -> list[ScoredAlert]:
        return self.score_all(alerts)[:n]
