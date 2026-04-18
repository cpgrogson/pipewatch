"""Tests for snapshot module."""
import pytest
from datetime import datetime, timezone
from pipewatch.snapshot import MetricSnapshot, SnapshotStore, SnapshotDiff


TS = datetime.now(timezone.utc).isoformat()


def make_snap(name="pipe_a", duration=10.0, error_rate=0.01, rows=1000):
    return MetricSnapshot(
        pipeline_name=name,
        captured_at=TS,
        duration_seconds=duration,
        error_rate=error_rate,
        rows_processed=rows,
    )


@pytest.fixture
def store(tmp_path):
    return SnapshotStore(str(tmp_path / "snaps.json"))


def test_empty_store_returns_none(store):
    assert store.get_snapshot("pipe_a") is None


def test_save_and_retrieve(store):
    snap = make_snap()
    store.save_snapshot(snap)
    result = store.get_snapshot("pipe_a")
    assert result is not None
    assert result.duration_seconds == 10.0
    assert result.error_rate == 0.01


def test_diff_returns_none_without_previous(store):
    snap = make_snap()
    assert store.diff(snap) is None


def test_diff_detects_degradation(store):
    old = make_snap(duration=10.0, error_rate=0.01)
    store.save_snapshot(old)
    new = make_snap(duration=15.0, error_rate=0.05)
    diff = store.diff(new)
    assert diff is not None
    assert diff.duration_delta == pytest.approx(5.0)
    assert diff.error_rate_delta == pytest.approx(0.04)
    assert diff.improved is False


def test_diff_detects_improvement(store):
    old = make_snap(duration=20.0, error_rate=0.1)
    store.save_snapshot(old)
    new = make_snap(duration=10.0, error_rate=0.01)
    diff = store.diff(new)
    assert diff.improved is True
    assert diff.duration_delta == pytest.approx(-10.0)


def test_diff_summary_format(store):
    old = make_snap(duration=10.0, error_rate=0.01, rows=500)
    store.save_snapshot(old)
    new = make_snap(duration=12.0, error_rate=0.03, rows=600)
    diff = store.diff(new)
    summary = diff.summary()
    assert "pipe_a" in summary
    assert "degraded" in summary


def test_persists_across_instances(tmp_path):
    path = str(tmp_path / "snaps.json")
    s1 = SnapshotStore(path)
    s1.save_snapshot(make_snap(name="pipe_b", duration=5.0))
    s2 = SnapshotStore(path)
    result = s2.get_snapshot("pipe_b")
    assert result is not None
    assert result.duration_seconds == 5.0


def test_all_snapshots_returns_list(store):
    store.save_snapshot(make_snap("a"))
    store.save_snapshot(make_snap("b"))
    all_snaps = store.all_snapshots()
    names = {s.pipeline_name for s in all_snaps}
    assert names == {"a", "b"}
