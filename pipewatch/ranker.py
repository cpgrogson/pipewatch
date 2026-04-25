from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.checker import Alert


@dataclass
class RankedAlert:
    alert: Alert
    rank: int
    score: float
    reason: str

    def __str__(self) -> str:
        return f"[Rank #{self.rank}] {self.alert.pipeline}/{self.alert.metric} score={self.score:.2f} ({self.reason})"


SEVERITY_WEIGHTS = {
    "critical": 3.0,
    "warning": 2.0,
    "info": 1.0,
}

METRIC_WEIGHTS = {
    "error_rate": 2.5,
    "duration": 1.5,
    "row_count": 1.0,
}


class AlertRanker:
    def __init__(
        self,
        severity_weights: Optional[dict] = None,
        metric_weights: Optional[dict] = None,
    ):
        self.severity_weights = severity_weights or SEVERITY_WEIGHTS
        self.metric_weights = metric_weights or METRIC_WEIGHTS

    def _compute_score(self, alert: Alert) -> tuple[float, str]:
        sev_w = self.severity_weights.get(alert.severity, 1.0)
        met_w = self.metric_weights.get(alert.metric, 1.0)
        score = round(sev_w * met_w, 4)
        reason = f"severity={alert.severity}(x{sev_w}) metric={alert.metric}(x{met_w})"
        return score, reason

    def rank(self, alerts: List[Alert]) -> List[RankedAlert]:
        scored = []
        for alert in alerts:
            score, reason = self._compute_score(alert)
            scored.append((score, reason, alert))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            RankedAlert(alert=a, rank=i + 1, score=s, reason=r)
            for i, (s, r, a) in enumerate(scored)
        ]

    def top(self, alerts: List[Alert], n: int = 5) -> List[RankedAlert]:
        return self.rank(alerts)[:n]
