"""Integration tests: retrier interacts with notifier retry loop."""
from pathlib import Path
from unittest.mock import MagicMock, call

from pipewatch.checker import Alert
from pipewatch.retrier import RetryStore


def _alert(pipeline: str = "sales", metric: str = "row_count") -> Alert:
    return Alert(pipeline=pipeline, metric=metric, value=0, threshold=100, severity="critical")


def _flush_due(store: RetryStore, notify_fn, backoff: float = 0.0) -> int:
    """Attempt to re-notify all due entries; return number processed."""
    due = store.due()
    for entry in due:
        try:
            notify_fn(entry)
            # success — remove by exhausting
            entry.attempts = entry.max_attempts
            store._entries = [e for e in store._entries if not e.is_exhausted()]
            store._save()
        except Exception:
            store.mark_attempted(entry, backoff=backoff)
    return len(due)


def test_successful_retry_removes_entry(tmp_path: Path) -> None:
    store = RetryStore(path=tmp_path / "r.json")
    store.enqueue(_alert(), max_attempts=3)
    notify = MagicMock()
    processed = _flush_due(store, notify, backoff=0)
    assert processed == 1
    assert store.all() == []
    notify.assert_called_once()


def test_failed_retry_keeps_entry(tmp_path: Path) -> None:
    store = RetryStore(path=tmp_path / "r.json")
    store.enqueue(_alert(), max_attempts=3)

    def failing_notify(entry):
        raise RuntimeError("send failed")

    _flush_due(store, failing_notify, backoff=0)
    remaining = store.all()
    assert len(remaining) == 1
    assert remaining[0].attempts == 1


def test_multiple_alerts_queued(tmp_path: Path) -> None:
    store = RetryStore(path=tmp_path / "r.json")
    store.enqueue(_alert("a", "m1"))
    store.enqueue(_alert("b", "m2"))
    assert len(store.all()) == 2
    assert len(store.due()) == 2


def test_exhausted_not_in_due(tmp_path: Path) -> None:
    store = RetryStore(path=tmp_path / "r.json")
    store.enqueue(_alert(), max_attempts=1)
    entry = store.due()[0]
    store.mark_attempted(entry, backoff=0)
    assert store.due() == []
    assert store.all() == []
