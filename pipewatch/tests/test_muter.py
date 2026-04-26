"""Tests for pipewatch.muter."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

import pytest

from pipewatch.checker import Alert
from pipewatch.muter import MuteRule, MuteStore


@pytest.fixture
def alert() -> Alert:
    return Alert(pipeline="pipe_a", metric="error_rate", value=0.15, threshold=0.10, severity="critical")


@pytest.fixture
def store(tmp_path) -> MuteStore:
    return MuteStore(path=str(tmp_path / "mutes.json"))


# --- MuteRule ---

def test_mute_rule_matches_exact(alert):
    rule = MuteRule(pipeline="pipe_a", metric="error_rate")
    assert rule.matches(alert)


def test_mute_rule_no_match_wrong_pipeline(alert):
    rule = MuteRule(pipeline="pipe_b", metric="error_rate")
    assert not rule.matches(alert)


def test_mute_rule_wildcard_pipeline(alert):
    rule = MuteRule(pipeline="*", metric="error_rate")
    assert rule.matches(alert)


def test_mute_rule_wildcard_metric(alert):
    rule = MuteRule(pipeline="pipe_a", metric="*")
    assert rule.matches(alert)


def test_mute_rule_expired_does_not_match(alert):
    past = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    rule = MuteRule(pipeline="pipe_a", metric="error_rate", expires_at=past)
    assert not rule.matches(alert)


def test_mute_rule_future_expiry_matches(alert):
    future = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    rule = MuteRule(pipeline="pipe_a", metric="error_rate", expires_at=future)
    assert rule.matches(alert)


# --- MuteStore ---

def test_empty_store_not_muted(store, alert):
    assert not store.is_muted(alert)


def test_add_rule_mutes_alert(store, alert):
    store.add(MuteRule(pipeline="pipe_a", metric="error_rate"))
    assert store.is_muted(alert)


def test_filter_alerts_removes_muted(store, alert):
    other = Alert(pipeline="pipe_b", metric="duration", value=10, threshold=5, severity="warning")
    store.add(MuteRule(pipeline="pipe_a", metric="error_rate"))
    result = store.filter_alerts([alert, other])
    assert result == [other]


def test_prune_expired_removes_old_rules(store, alert):
    past = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
    store.add(MuteRule(pipeline="pipe_a", metric="error_rate", expires_at=past))
    removed = store.prune_expired()
    assert removed == 1
    assert not store.is_muted(alert)


def test_clear_removes_all_rules(store, alert):
    store.add(MuteRule(pipeline="pipe_a", metric="error_rate"))
    store.clear()
    assert not store.is_muted(alert)
    assert store.all_rules() == []


def test_persists_to_disk(tmp_path, alert):
    path = str(tmp_path / "mutes.json")
    s1 = MuteStore(path=path)
    s1.add(MuteRule(pipeline="pipe_a", metric="error_rate"))
    s2 = MuteStore(path=path)
    assert s2.is_muted(alert)
