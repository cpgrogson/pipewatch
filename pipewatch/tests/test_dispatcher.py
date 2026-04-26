"""Tests for AlertDispatcher."""

from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

import pytest

from pipewatch.checker import Alert
from pipewatch.dispatcher import AlertDispatcher, DispatchResult
from pipewatch.notifier import LogNotifier


def make_alert(pipeline="pipe_a", metric="error_rate", severity="critical"):
    return Alert(pipeline=pipeline, metric=metric, value=0.9, threshold=0.1, severity=severity)


@pytest.fixture
def alert():
    return make_alert()


@pytest.fixture
def notifier():
    n = MagicMock()
    n.name = "mock"
    return n


def test_dispatch_sends_to_notifier(alert, notifier):
    dispatcher = AlertDispatcher(notifiers=[notifier])
    result = dispatcher.dispatch([alert])
    notifier.send.assert_called_once()
    assert len(result.sent) == 1
    assert result.total == 1


def test_dispatch_empty_alerts(notifier):
    dispatcher = AlertDispatcher(notifiers=[notifier])
    result = dispatcher.dispatch([])
    notifier.send.assert_not_called()
    assert result.total == 0


def test_dispatch_skips_silenced_alert(alert, notifier):
    silencer = MagicMock()
    silencer.is_silenced.return_value = True
    dispatcher = AlertDispatcher(notifiers=[notifier], silencer=silencer)
    result = dispatcher.dispatch([alert])
    notifier.send.assert_not_called()
    assert len(result.silenced) == 1
    assert len(result.sent) == 0


def test_dispatch_skips_duplicate_alert(alert, notifier):
    deduplicator = MagicMock()
    deduplicator.is_duplicate.return_value = True
    dispatcher = AlertDispatcher(notifiers=[notifier], deduplicator=deduplicator)
    result = dispatcher.dispatch([alert])
    notifier.send.assert_not_called()
    assert len(result.deduplicated) == 1


def test_dispatch_records_non_duplicate(alert, notifier):
    deduplicator = MagicMock()
    deduplicator.is_duplicate.return_value = False
    dispatcher = AlertDispatcher(notifiers=[notifier], deduplicator=deduplicator)
    dispatcher.dispatch([alert])
    deduplicator.record.assert_called_once_with(alert)


def test_dispatch_result_summary():
    result = DispatchResult()
    result.sent = [make_alert()]
    result.deduplicated = [make_alert(), make_alert()]
    result.silenced = [make_alert()]
    assert result.total == 4
    assert "1 alerts" in result.summary()
    assert "2 deduplicated" in result.summary()
    assert "1 silenced" in result.summary()


def test_dispatch_multiple_alerts_mixed(notifier):
    silencer = MagicMock()
    silencer.is_silenced.side_effect = lambda p, m: p == "pipe_b"
    deduplicator = MagicMock()
    deduplicator.is_duplicate.return_value = False
    alerts = [make_alert("pipe_a"), make_alert("pipe_b"), make_alert("pipe_c")]
    dispatcher = AlertDispatcher(notifiers=[notifier], silencer=silencer, deduplicator=deduplicator)
    result = dispatcher.dispatch(alerts)
    assert len(result.sent) == 2
    assert len(result.silenced) == 1
