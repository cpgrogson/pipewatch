"""Alert normalizer: standardizes alert fields to consistent formats before processing."""

from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.checker import Alert


SEVERITY_ALIASES = {
    "warn": "warning",
    "crit": "critical",
    "err": "error",
    "info": "info",
}

KNOWN_METRICS = {
    "error_rate",
    "row_count",
    "duration",
}


@dataclass
class NormalizedAlert:
    pipeline: str
    metric: str
    severity: str
    message: str
    value: float
    original: Alert

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.pipeline}/{self.metric}: {self.message} (value={self.value})"


@dataclass
class NormalizationResult:
    normalized: List[NormalizedAlert] = field(default_factory=list)
    skipped: List[Alert] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.normalized) + len(self.skipped)

    def summary(self) -> str:
        return (
            f"{len(self.normalized)} normalized, {len(self.skipped)} skipped "
            f"out of {self.total} alerts"
        )


class AlertNormalizer:
    def __init__(
        self,
        severity_aliases: Optional[dict] = None,
        known_metrics: Optional[set] = None,
        drop_unknown_metrics: bool = False,
    ):
        self.severity_aliases = severity_aliases or SEVERITY_ALIASES
        self.known_metrics = known_metrics or KNOWN_METRICS
        self.drop_unknown_metrics = drop_unknown_metrics

    def _normalize_severity(self, severity: str) -> str:
        s = severity.strip().lower()
        return self.severity_aliases.get(s, s)

    def _normalize_metric(self, metric: str) -> str:
        return metric.strip().lower().replace(" ", "_")

    def _normalize_pipeline(self, pipeline: str) -> str:
        return pipeline.strip()

    def normalize(self, alerts: List[Alert]) -> NormalizationResult:
        result = NormalizationResult()
        for alert in alerts:
            metric = self._normalize_metric(alert.metric)
            if self.drop_unknown_metrics and metric not in self.known_metrics:
                result.skipped.append(alert)
                continue
            normalized = NormalizedAlert(
                pipeline=self._normalize_pipeline(alert.pipeline),
                metric=metric,
                severity=self._normalize_severity(alert.severity),
                message=alert.message.strip(),
                value=alert.value,
                original=alert,
            )
            result.normalized.append(normalized)
        return result
