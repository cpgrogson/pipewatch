import pytest
from datetime import datetime, timedelta, timezone
from pipewatch.acknowledger import AcknowledgementEntry, AcknowledgementStore


@pytest.fixture
def store(tmp_path):
    return AcknowledgementStore(path=str(tmp_path / "acks.json"))


def make_entry(pipeline="pipeline_a", metric="duration", expires_at=None):
    return AcknowledgementEntry(
        pipeline=pipeline,
        metric=metric,
        acknowledged_by="alice",
        reason="Planned maintenance",
        expires_at=expires_at,
    )


def test_empty_store_returns_not_acknowledged(store):
    assert not store.is_acknowledged("pipeline_a", "duration")


def test_acknowledge_marks_as_acknowledged(store):
    entry = make_entry()
    store.acknowledge(entry)
    assert store.is_acknowledged("pipeline_a", "duration")


def test_different_metric_not_acknowledged(store):
    entry = make_entry(metric="duration")
    store.acknowledge(entry)
    assert not store.is_acknowledged("pipeline_a", "error_rate")


def test_different_pipeline_not_acknowledged(store):
    entry = make_entry(pipeline="pipeline_a")
    store.acknowledge(entry)
    assert not store.is_acknowledged("pipeline_b", "duration")


def test_expired_entry_not_acknowledged(store):
    past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    entry = make_entry(expires_at=past)
    store.acknowledge(entry)
    assert not store.is_acknowledged("pipeline_a", "duration")


def test_future_expiry_still_acknowledged(store):
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    entry = make_entry(expires_at=future)
    store.acknowledge(entry)
    assert store.is_acknowledged("pipeline_a", "duration")


def test_active_entries_excludes_expired(store):
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    store.acknowledge(make_entry(metric="duration", expires_at=past))
    store.acknowledge(make_entry(metric="error_rate", expires_at=future))
    active = store.active_entries()
    assert len(active) == 1
    assert active[0].metric == "error_rate"


def test_clear_removes_all_entries(store):
    store.acknowledge(make_entry())
    store.clear()
    assert store.active_entries() == []
    assert not store.is_acknowledged("pipeline_a", "duration")


def test_persists_to_disk(tmp_path):
    path = str(tmp_path / "acks.json")
    s1 = AcknowledgementStore(path=path)
    s1.acknowledge(make_entry())
    s2 = AcknowledgementStore(path=path)
    assert s2.is_acknowledged("pipeline_a", "duration")
