"""Threshold checker: evaluates pipeline metrics against configured thresholds."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.config import ThresholdConfig


@dataclass
class PipelineMetrics:
    pipeline_name: str
    duration_seconds: Optional[float] = None
    error_rate: Optional[float] = None
    rows_processed: Optional[int] = None
    lag_seconds: Optional[float] = None


@dataclass
class Alert:
    pipeline_name: str
    field: str
    message: str
    value: float
    threshold: float

    def __str__(self) -> str:
        return f"[ALERT] {self.pipeline_name} | {self.field}: {self.value} (threshold: {self.threshold}) — {self.message}"


def check_thresholds(metrics: PipelineMetrics, thresholds: ThresholdConfig) -> List[Alert]:
    """Compare metrics against thresholds and return a list of alerts."""
    alerts: List[Alert] = []

    checks = [
        ("duration_seconds", metrics.duration_seconds, thresholds.max_duration_seconds, "exceeds max duration", lambda v, t: v > t),
        ("error_rate", metrics.error_rate, thresholds.max_error_rate, "exceeds max error rate", lambda v, t: v > t),
        ("rows_processed", metrics.rows_processed, thresholds.min_rows_processed, "below min rows processed", lambda v, t: v < t),
        ("lag_seconds", metrics.lag_seconds, thresholds.max_lag_seconds, "exceeds max lag", lambda v, t: v > t),
    ]

    for field_name, value, threshold, message, condition in checks:
        if value is not None and threshold is not None and condition(value, threshold):
            alerts.append(Alert(
                pipeline_name=metrics.pipeline_name,
                field=field_name,
                message=message,
                value=float(value),
                threshold=float(threshold),
            ))

    return alerts
