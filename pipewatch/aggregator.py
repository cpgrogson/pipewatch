"""Aggregates metrics across multiple pipeline runs for trend analysis."""
from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.history import HistoryEntry


@dataclass
class PipelineTrend:
    pipeline_name: str
    avg_duration: float
    avg_error_rate: float
    avg_rows_processed: float
    run_count: int
    alert_rate: float  # fraction of runs that had alerts

    def is_degrading(self, duration_threshold: float = 0.2, error_threshold: float = 0.05) -> bool:
        """Heuristic: flagged as degrading if error_rate or duration is above thresholds."""
        return self.avg_error_rate > error_threshold or self.avg_duration > duration_threshold * 3600


@dataclass
class AggregationReport:
    trends: List[PipelineTrend] = field(default_factory=list)

    def degrading_pipelines(self) -> List[PipelineTrend]:
        return [t for t in self.trends if t.is_degrading()]

    def summary(self) -> str:
        lines = [f"Aggregation over {len(self.trends)} pipeline(s)"]
        for t in self.trends:
            status = "DEGRADING" if t.is_degrading() else "OK"
            lines.append(
                f"  [{status}] {t.pipeline_name}: runs={t.run_count}, "
                f"avg_duration={t.avg_duration:.1f}s, avg_error_rate={t.avg_error_rate:.3f}, "
                f"alert_rate={t.alert_rate:.2%}"
            )
        return "\n".join(lines)


def aggregate_entries(entries: List[HistoryEntry]) -> AggregationReport:
    """Group entries by pipeline name and compute averages."""
    grouped: dict = {}
    for entry in entries:
        grouped.setdefault(entry.pipeline_name, []).append(entry)

    trends = []
    for name, group in grouped.items():
        run_count = len(group)
        avg_duration = sum(e.duration for e in group) / run_count
        avg_error_rate = sum(e.error_rate for e in group) / run_count
        avg_rows = sum(e.rows_processed for e in group) / run_count
        alert_rate = sum(1 for e in group if e.alert_count > 0) / run_count
        trends.append(PipelineTrend(
            pipeline_name=name,
            avg_duration=avg_duration,
            avg_error_rate=avg_error_rate,
            avg_rows_processed=avg_rows,
            run_count=run_count,
            alert_rate=alert_rate,
        ))

    return AggregationReport(trends=trends)
