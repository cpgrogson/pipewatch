"""Snapshot module: capture and compare pipeline metric snapshots."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional
import json
import os


@dataclass
class MetricSnapshot:
    pipeline_name: str
    captured_at: str
    duration_seconds: float
    error_rate: float
    rows_processed: int

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MetricSnapshot":
        return cls(**data)


@dataclass
class SnapshotDiff:
    pipeline_name: str
    duration_delta: float
    error_rate_delta: float
    rows_delta: int
    improved: bool

    def summary(self) -> str:
        direction = "improved" if self.improved else "degraded"
        return (
            f"{self.pipeline_name} {direction}: "
            f"duration {self.duration_delta:+.2f}s, "
            f"error_rate {self.error_rate_delta:+.4f}, "
            f"rows {self.rows_delta:+d}"
        )


class SnapshotStore:
    def __init__(self, path: str = ".pipewatch_snapshots.json"):
        self.path = path
        self._snapshots: dict[str, MetricSnapshot] = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.path):
            return {}
        with open(self.path) as f:
            raw = json.load(f)
        return {k: MetricSnapshot.from_dict(v) for k, v in raw.items()}

    def _save(self):
        with open(self.path, "w") as f:
            json.dump({k: v.to_dict() for k, v in self._snapshots.items()}, f, indent=2)

    def save_snapshot(self, snapshot: MetricSnapshot):
        self._snapshots[snapshot.pipeline_name] = snapshot
        self._save()

    def get_snapshot(self, pipeline_name: str) -> Optional[MetricSnapshot]:
        return self._snapshots.get(pipeline_name)

    def diff(self, new: MetricSnapshot) -> Optional[SnapshotDiff]:
        old = self.get_snapshot(new.pipeline_name)
        if old is None:
            return None
        dur_delta = new.duration_seconds - old.duration_seconds
        err_delta = new.error_rate - old.error_rate
        rows_delta = new.rows_processed - old.rows_processed
        improved = dur_delta <= 0 and err_delta <= 0
        return SnapshotDiff(
            pipeline_name=new.pipeline_name,
            duration_delta=dur_delta,
            error_rate_delta=err_delta,
            rows_delta=rows_delta,
            improved=improved,
        )

    def all_snapshots(self) -> list[MetricSnapshot]:
        return list(self._snapshots.values())
