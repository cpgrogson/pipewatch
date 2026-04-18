"""Tests for baseline capture and drift detection."""
import pytest
from pipewatch.baseline import BaselineEntry, BaselineDrift, BaselineStore


@pytest.fixture
def store(tmp_path):
    return BaselineStore(str(tmp_path / "baseline.json"))


def make_entry(pipeline="pipe1", duration=10.0, error_rate=0.01, rows=1000.0):
    return BaselineEntry(
        pipeline=pipeline,
        avg_duration=duration,
        avg_error_rate=error_rate,
        avg_rows_processed=rows,
    )


def test_empty_store_returns_none(store):
    assert store.get("pipe1") is None


def test_save_and_retrieve(store):
    entry = make_entry()
    store.save(entry)
    result = store.get("pipe1")
    assert result is not None
    assert result.avg_duration == 10.0


def test_persists_to_disk(tmp_path):
    path = str(tmp_path / "baseline.json")
    s1 = BaselineStore(path)
    s1.save(make_entry())
    s2 = BaselineStore(path)
    assert s2.get("pipe1") is not None


def test_compare_returns_none_without_baseline(store):
    drift = store.compare(make_entry())
    assert drift is None


def test_compare_computes_deltas(store):
    store.save(make_entry(duration=10.0, error_rate=0.01, rows=1000.0))
    current = make_entry(duration=15.05, rows=800.0)
    drift = store.compare(current)
    assert drift is not None
    assert drift.duration_delta == pytest.approx(5.0)
    assert drift.error_rate_delta == pytest.approx(0.04)
    assert drift.rows_delta == pytest.approx(-200.0)


def test_drift_is_significant_above_threshold():
    drift = BaselineDrift("pipe1", duration_delta=5.0, error_rate_delta=0.0, rows_delta=0.0)
    assert drift.is_significant(threshold=0.2)


def test_drift_not_significant_below_threshold():
    drift = BaselineDrift("pipe1", duration_delta=0.1, error_rate_delta=0.01, rows_delta=5.0)
    assert not drift.is_significant(threshold=0.2)


def test_drift_summary_format():
    drift = BaselineDrift("pipe1", duration_delta=2.5, error_rate_delta=0.03, rows_delta=-100.0)
    summary = drift.summary()
    assert "pipe1" in summary
    assert "+2.50s" in summary


def test_store_all_returns_all_entries(store):
    store.save(make_entry("a"))
    store.save(make_entry("b"))
    assert len(store.all()) == 2
