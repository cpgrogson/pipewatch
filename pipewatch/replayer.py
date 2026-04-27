"""Alert replayer: re-process historical alerts through current pipeline logic."""

from dataclasses import dataclass, field
from typing import List, Callable, Optional
from datetime import datetime

from pipewatch.checker import Alert
from pipewatch.history import HistoryEntry, HistoryStore


@dataclass
class ReplayResult:
    replayed: int = 0
    skipped: int = 0
    errors: int = 0
    outputs: List[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        return (
            f"Replayed {self.replayed} entries, "
            f"skipped {self.skipped}, errors {self.errors}"
        )


def replay_history(
    store: HistoryStore,
    handler: Callable[[str, List[Alert]], None],
    pipeline: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: Optional[int] = None,
) -> ReplayResult:
    """Replay historical entries through a handler function.

    Args:
        store: HistoryStore to load entries from.
        handler: Callable receiving (pipeline_name, alerts) for each entry.
        pipeline: Optional pipeline name filter.
        since: Optional datetime to filter entries after.
        limit: Optional max number of entries to replay.
    """
    result = ReplayResult()
    entries: List[HistoryEntry] = store.all()

    if pipeline:
        entries = [e for e in entries if e.pipeline == pipeline]

    if since:
        entries = [e for e in entries if e.timestamp >= since]

    if limit is not None:
        entries = entries[:limit]

    for entry in entries:
        try:
            handler(entry.pipeline, entry.alerts)
            result.replayed += 1
            result.outputs.append(
                f"[{entry.timestamp.isoformat()}] {entry.pipeline}: "
                f"{len(entry.alerts)} alert(s)"
            )
        except Exception as exc:  # noqa: BLE001
            result.errors += 1
            result.outputs.append(
                f"[ERROR] {entry.pipeline} @ {entry.timestamp.isoformat()}: {exc}"
            )

    result.skipped = len(store.all()) - result.replayed - result.errors
    return result
