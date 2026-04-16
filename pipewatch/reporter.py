"""Report generation for pipeline health summaries."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from pipewatch.checker import Alert, PipelineMetrics


@dataclass
class PipelineReport:
    pipeline_name: str
    metrics: PipelineMetrics
    alerts: List[Alert]
    checked_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def healthy(self) -> bool:
        return len(self.alerts) == 0

    def summary(self) -> str:
        status = "OK" if self.healthy else "ALERT"
        lines = [f"[{status}] Pipeline: {self.pipeline_name} (checked at {self.checked_at.isoformat()}Z)"]
        lines.append(f"  duration={self.metrics.duration_seconds}s  "
                     f"error_rate={self.metrics.error_rate:.2%}  "
                     f"rows_processed={self.metrics.rows_processed}")
        for alert in self.alerts:
            lines.append(f"  ! {alert}")
        return "\n".join(lines)


@dataclass
class RunReport:
    reports: List[PipelineReport] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def add(self, report: PipelineReport) -> None:
        self.reports.append(report)

    @property
    def total(self) -> int:
        return len(self.reports)

    @property
    def healthy_count(self) -> int:
        return sum(1 for r in self.reports if r.healthy)

    @property
    def alert_count(self) -> int:
        return self.total - self.healthy_count

    def render(self, verbose: bool = False) -> str:
        lines = [f"=== PipeWatch Run Report ({self.generated_at.isoformat()}Z) ==="]
        lines.append(f"Pipelines checked: {self.total}  Healthy: {self.healthy_count}  Alerts: {self.alert_count}")
        if verbose or self.alert_count > 0:
            lines.append("")
            for r in self.reports:
                if verbose or not r.healthy:
                    lines.append(r.summary())
        return "\n".join(lines)
