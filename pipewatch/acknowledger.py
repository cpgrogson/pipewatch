from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import json
import os

ACK_FILE = ".pipewatch_acks.json"


@dataclass
class AcknowledgementEntry:
    pipeline: str
    metric: str
    acknowledged_by: str
    reason: str
    acknowledged_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    expires_at: Optional[str] = None

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        expiry = datetime.fromisoformat(self.expires_at)
        now = datetime.now(timezone.utc)
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return now > expiry

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "metric": self.metric,
            "acknowledged_by": self.acknowledged_by,
            "reason": self.reason,
            "acknowledged_at": self.acknowledged_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AcknowledgementEntry":
        return cls(**data)


class AcknowledgementStore:
    def __init__(self, path: str = ACK_FILE):
        self.path = path
        self._entries: list[AcknowledgementEntry] = self._load()

    def _load(self) -> list[AcknowledgementEntry]:
        if not os.path.exists(self.path):
            return []
        with open(self.path) as f:
            return [AcknowledgementEntry.from_dict(d) for d in json.load(f)]

    def _save(self) -> None:
        with open(self.path, "w") as f:
            json.dump([e.to_dict() for e in self._entries], f, indent=2)

    def acknowledge(self, entry: AcknowledgementEntry) -> None:
        self._entries.append(entry)
        self._save()

    def is_acknowledged(self, pipeline: str, metric: str) -> bool:
        for entry in self._entries:
            if entry.pipeline == pipeline and entry.metric == metric:
                if not entry.is_expired():
                    return True
        return False

    def active_entries(self) -> list[AcknowledgementEntry]:
        return [e for e in self._entries if not e.is_expired()]

    def clear(self) -> None:
        self._entries = []
        self._save()
