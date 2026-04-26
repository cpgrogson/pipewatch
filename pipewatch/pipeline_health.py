"""Pipeline health scoring and status summarization.

Combines alerts, trends, anomalies, and baseline drift into a single
health score per pipeline, providing an at-a-glance view of pipeline status.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum

from pipewatch.checker import Alert
from pipewatch.aggregator import PipelineTrend
from pipewatch.anomaly import AnomalyResult
from pipewatch.baseline import BaselineDrift


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class PipelineHealthScore:
    """Health score for a single pipeline."""

    pipeline: str
    score: float  # 0.0 (worst) to 1.0 (best)
    status: HealthStatus
    alert_count: int = 0
    critical_alert_count: int = 0
    is_degrading: bool = False
    has_anomalies: bool = False
    has_baseline_drift: bool = False
    contributing_factors: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        factors = ", ".join(self.contributing_factors) if self.contributing_factors else "none"
        return (
            f"[{self.status.value.upper()}] {self.pipeline} "
            f"score={self.score:.2f} factors=({factors})"
        )


def compute_health_score(
    pipeline: str,
    alerts: Optional[List[Alert]] = None,
    trend: Optional[PipelineTrend] = None,
    anomalies: Optional[List[AnomalyResult]] = None,
    drift: Optional[BaselineDrift] = None,
) -> PipelineHealthScore:
    """Compute a composite health score for a pipeline.

    Scoring model:
      - Starts at 1.0 (fully healthy)
      - Deducts for critical alerts (-0.25 each, capped at -0.5)
      - Deducts for warning alerts (-0.10 each, capped at -0.3)
      - Deducts for degrading trend (-0.15)
      - Deducts for detected anomalies (-0.10 per anomaly, capped at -0.2)
      - Deducts for significant baseline drift (-0.10)
    """
    score = 1.0
    factors: List[str] = []

    pipeline_alerts = alerts or []
    critical_alerts = [a for a in pipeline_alerts if a.severity == "critical"]
    warning_alerts = [a for a in pipeline_alerts if a.severity == "warning"]

    # Deduct for critical alerts
    if critical_alerts:
        deduction = min(0.25 * len(critical_alerts), 0.5)
        score -= deduction
        factors.append(f"{len(critical_alerts)} critical alert(s)")

    # Deduct for warning alerts
    if warning_alerts:
        deduction = min(0.10 * len(warning_alerts), 0.3)
        score -= deduction
        factors.append(f"{len(warning_alerts)} warning alert(s)")

    # Deduct for degrading trend
    is_degrading = False
    if trend is not None and trend.is_degrading():
        score -= 0.15
        is_degrading = True
        factors.append("degrading trend")

    # Deduct for anomalies
    active_anomalies = anomalies or []
    has_anomalies = len(active_anomalies) > 0
    if has_anomalies:
        deduction = min(0.10 * len(active_anomalies), 0.2)
        score -= deduction
        factors.append(f"{len(active_anomalies)} anomaly/anomalies detected")

    # Deduct for significant baseline drift
    has_drift = False
    if drift is not None and drift.is_significant():
        score -= 0.10
        has_drift = True
        factors.append("significant baseline drift")

    score = max(0.0, round(score, 4))

    # Determine status from score
    if score >= 0.75:
        status = HealthStatus.HEALTHY
    elif score >= 0.40:
        status = HealthStatus.DEGRADED
    else:
        status = HealthStatus.CRITICAL

    return PipelineHealthScore(
        pipeline=pipeline,
        score=score,
        status=status,
        alert_count=len(pipeline_alerts),
        critical_alert_count=len(critical_alerts),
        is_degrading=is_degrading,
        has_anomalies=has_anomalies,
        has_baseline_drift=has_drift,
        contributing_factors=factors,
    )


def summarize_health(scores: List[PipelineHealthScore]) -> Dict[str, int]:
    """Return a count of pipelines in each health status."""
    summary: Dict[str, int] = {
        HealthStatus.HEALTHY: 0,
        HealthStatus.DEGRADED: 0,
        HealthStatus.CRITICAL: 0,
        HealthStatus.UNKNOWN: 0,
    }
    for s in scores:
        summary[s.status] = summary.get(s.status, 0) + 1
    return summary
