import pytest
from pipewatch.checker import Alert
from pipewatch.tracer import AlertTracer, AlertTrace, TraceEvent


@pytest.fixture
def alert():
    return Alert(pipeline="etl_orders", metric="error_rate", severity="critical", message="too many errors")


@pytest.fixture
def tracer():
    return AlertTracer()


def test_trace_creates_alert_trace(tracer, alert):
    t = tracer.trace(alert)
    assert isinstance(t, AlertTrace)
    assert t.alert is alert
    assert t.events == []


def test_add_event_appends_to_trace(tracer, alert):
    t = tracer.trace(alert)
    t.add_event(stage="check", detail="threshold exceeded")
    assert len(t.events) == 1
    e = t.events[0]
    assert e.stage == "check"
    assert e.detail == "threshold exceeded"
    assert e.pipeline == "etl_orders"
    assert e.metric == "error_rate"


def test_multiple_events_ordered(tracer, alert):
    t = tracer.trace(alert)
    t.add_event("check", "first")
    t.add_event("notify", "second")
    t.add_event("archive", "third")
    assert [e.stage for e in t.events] == ["check", "notify", "archive"]


def test_summary_includes_stages(tracer, alert):
    t = tracer.trace(alert)
    t.add_event("check", "ok")
    t.add_event("route", "sent")
    s = t.summary()
    assert "etl_orders" in s
    assert "error_rate" in s
    assert "check" in s
    assert "route" in s


def test_all_traces_returns_all(tracer):
    a1 = Alert(pipeline="p1", metric="m1", severity="warning", message="")
    a2 = Alert(pipeline="p2", metric="m2", severity="critical", message="")
    tracer.trace(a1)
    tracer.trace(a2)
    assert len(tracer.all_traces()) == 2


def test_for_pipeline_filters_correctly(tracer):
    a1 = Alert(pipeline="etl_orders", metric="m1", severity="warning", message="")
    a2 = Alert(pipeline="etl_users", metric="m2", severity="warning", message="")
    a3 = Alert(pipeline="etl_orders", metric="m3", severity="critical", message="")
    tracer.trace(a1)
    tracer.trace(a2)
    tracer.trace(a3)
    results = tracer.for_pipeline("etl_orders")
    assert len(results) == 2
    assert all(t.alert.pipeline == "etl_orders" for t in results)


def test_clear_removes_all_traces(tracer, alert):
    tracer.trace(alert)
    tracer.trace(alert)
    tracer.clear()
    assert tracer.all_traces() == []


def test_trace_event_to_dict_and_from_dict(alert):
    t = AlertTrace(alert=alert)
    t.add_event("dispatch", "sent to slack")
    e = t.events[0]
    d = e.to_dict()
    assert d["stage"] == "dispatch"
    assert d["pipeline"] == "etl_orders"
    restored = TraceEvent.from_dict(d)
    assert restored.stage == e.stage
    assert restored.detail == e.detail
