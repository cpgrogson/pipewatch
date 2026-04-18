"""Anomaly detection for pipeline metrics based on historical data."""
from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.history import HistoryEntry


@dataclass
class AnomalyResult:
    pipeline: str
    metric: str
    current_value: float
    mean: float
    std_dev: float
    z_score: float
    is_anomaly: bool

    def __str__(self) -> str:
        status = "ANOMALY" if self.is_anomaly else "ok"
        return (
            f"[{status}] {self.pipeline}/{self.metric}: "
            f"value={self.current_value:.2f}, mean={self.mean:.2f}, "
            f"z={self.z_score:.2f}"
        )


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std_dev(values: List[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return variance ** 0.5


def detect_anomalies(
    pipeline: str,
    entries: List[HistoryEntry],
    current: HistoryEntry,
    z_threshold: float = 2.5,
) -> List[AnomalyResult]:
    """Detect anomalies in current metrics compared to historical entries."""
    if not entries:
        return []

    results = []
    metrics = {
        "duration": ([e.duration for e in entries], current.duration),
        "error_rate": ([e.error_rate for e in entries], current.error_rate),
        "rows_processed": ([e.rows_processed for e in entries], current.rows_processed),
    }

    for metric_name, (historical, current_val) in metrics.items():
        if current_val is None:
            continue
        historical = [v for v in historical if v is not None]
        if not historical:
            continue
        mean = _mean(historical)
        std = _std_dev(historical, mean)
        if std == 0.0:
            z = 0.0
        else:
            z = abs((current_val - mean) / std)
        results.append(
            AnomalyResult(
                pipeline=pipeline,
                metric=metric_name,
                current_value=current_val,
                mean=mean,
                std_dev=std,
                z_score=z,
                is_anomaly=z >= z_threshold,
            )
        )
    return results
