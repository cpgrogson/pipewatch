from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from pipewatch.checker import Alert


@dataclass
class TraceEvent:
    timestamp: str
    stage: str
    pipeline: str
    metric: str
    detail: str

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "stage": self.stage,
            "pipeline": self.pipeline,
            "metric": self.metric,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TraceEvent":
        return cls(
            timestamp=d["timestamp"],
            stage=d["stage"],
            pipeline=d["pipeline"],
            metric=d["metric"],
            detail=d["detail"],
        )


@dataclass
class AlertTrace:
    alert: Alert
    events: List[TraceEvent] = field(default_factory=list)

    def add_event(self, stage: str, detail: str) -> None:
        event = TraceEvent(
            timestamp=datetime.utcnow().isoformat(),
            stage=stage,
            pipeline=self.alert.pipeline,
            metric=self.alert.metric,
            detail=detail,
        )
        self.events.append(event)

    def summary(self) -> str:
        stages = ", ".join(e.stage for e in self.events)
        return f"[{self.alert.pipeline}/{self.alert.metric}] stages: {stages}"


class AlertTracer:
    def __init__(self) -> None:
        self._traces: List[AlertTrace] = []

    def trace(self, alert: Alert) -> AlertTrace:
        t = AlertTrace(alert=alert)
        self._traces.append(t)
        return t

    def all_traces(self) -> List[AlertTrace]:
        return list(self._traces)

    def for_pipeline(self, pipeline: str) -> List[AlertTrace]:
        return [t for t in self._traces if t.alert.pipeline == pipeline]

    def clear(self) -> None:
        self._traces.clear()
