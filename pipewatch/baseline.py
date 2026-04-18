"""Baseline management: capture and compare pipeline metric baselines."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
import json
from pathlib import Path


@dataclass
class BaselineEntry:
    pipeline: str
    avg_duration: float
    avg_error_rate: float
    avg_rows_processed: float

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "BaselineEntry":
        return cls(**data)


@dataclass
class BaselineDrift:
    pipeline: str
    duration_delta: float
    error_rate_delta: float
    rows_delta: float

    def is_significant(self, threshold: float = 0.2) -> bool:
        return (
            abs(self.duration_delta) > threshold
            or abs(self.error_rate_delta) > threshold
            or abs(self.rows_delta) > threshold
        )

    def summary(self) -> str:
        return (
            f"{self.pipeline}: duration_delta={self.duration_delta:+.2f}s "
            f"error_rate_delta={self.error_rate_delta:+.2%} "
            f"rows_delta={self.rows_delta:+.0f}"
        )


class BaselineStore:
    def __init__(self, path: str = ".pipewatch_baseline.json"):
        self._path = Path(path)
        self._baselines: dict[str, BaselineEntry] = self._load()

    def _load(self) -> dict[str, BaselineEntry]:
        if not self._path.exists():
            return {}
        data = json.loads(self._path.read_text())
        return {k: BaselineEntry.from_dict(v) for k, v in data.items()}

    def save(self, entry: BaselineEntry) -> None:
        self._baselines[entry.pipeline] = entry
        self._path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._baselines.items()}, indent=2)
        )

    def get(self, pipeline: str) -> Optional[BaselineEntry]:
        return self._baselines.get(pipeline)

    def compare(self, entry: BaselineEntry) -> Optional[BaselineDrift]:
        base = self.get(entry.pipeline)
        if base is None:
            return None
        return BaselineDrift(
            pipeline=entry.pipeline,
            duration_delta=entry.avg_duration - base.avg_duration,
            error_rate_delta=entry.avg_error_rate - base.avg_error_rate,
            rows_delta=entry.avg_rows_processed - base.avg_rows_processed,
        )

    def all(self) -> list[BaselineEntry]:
        return list(self._baselines.values())
