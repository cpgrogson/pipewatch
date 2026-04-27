"""Tests for pipewatch.normalizer."""

import pytest
from pipewatch.checker import Alert
from pipewatch.normalizer import AlertNormalizer, NormalizationResult, NormalizedAlert


@pytest.fixture
def normalizer():
    return AlertNormalizer()


def _alert(pipeline="pipe1", metric="error_rate", severity="warning", message="too high", value=0.5):
    return Alert(pipeline=pipeline, metric=metric, severity=severity, message=message, value=value)


def test_normalize_returns_normalized_alert(normalizer):
    alerts = [_alert()]
    result = normalizer.normalize(alerts)
    assert len(result.normalized) == 1
    assert isinstance(result.normalized[0], NormalizedAlert)


def test_normalize_severity_alias_warn(normalizer):
    alerts = [_alert(severity="warn")]
    result = normalizer.normalize(alerts)
    assert result.normalized[0].severity == "warning"


def test_normalize_severity_alias_crit(normalizer):
    alerts = [_alert(severity="crit")]
    result = normalizer.normalize(alerts)
    assert result.normalized[0].severity == "critical"


def test_normalize_severity_unknown_passthrough(normalizer):
    alerts = [_alert(severity="urgent")]
    result = normalizer.normalize(alerts)
    assert result.normalized[0].severity == "urgent"


def test_normalize_metric_lowercased_and_stripped(normalizer):
    alerts = [_alert(metric=" Error_Rate ")]
    result = normalizer.normalize(alerts)
    assert result.normalized[0].metric == "error_rate"


def test_normalize_metric_spaces_to_underscores(normalizer):
    alerts = [_alert(metric="row count")]
    result = normalizer.normalize(alerts)
    assert result.normalized[0].metric == "row_count"


def test_normalize_pipeline_stripped(normalizer):
    alerts = [_alert(pipeline="  my_pipeline  ")]
    result = normalizer.normalize(alerts)
    assert result.normalized[0].pipeline == "my_pipeline"


def test_normalize_message_stripped(normalizer):
    alerts = [_alert(message="  something is wrong  ")]
    result = normalizer.normalize(alerts)
    assert result.normalized[0].message == "something is wrong"


def test_drop_unknown_metrics_skips_alert():
    norm = AlertNormalizer(drop_unknown_metrics=True)
    alerts = [_alert(metric="latency")]
    result = norm.normalize(alerts)
    assert len(result.normalized) == 0
    assert len(result.skipped) == 1


def test_known_metric_not_skipped_when_drop_enabled():
    norm = AlertNormalizer(drop_unknown_metrics=True)
    alerts = [_alert(metric="error_rate")]
    result = norm.normalize(alerts)
    assert len(result.normalized) == 1
    assert len(result.skipped) == 0


def test_normalization_result_total(normalizer):
    alerts = [_alert(), _alert(metric="error_rate")]
    result = normalizer.normalize(alerts)
    assert result.total == 2


def test_normalization_result_summary_string(normalizer):
    alerts = [_alert(), _alert()]
    result = normalizer.normalize(alerts)
    summary = result.summary()
    assert "normalized" in summary
    assert "2" in summary


def test_normalized_alert_str(normalizer):
    alerts = [_alert(pipeline="p1", metric="error_rate", severity="critical", message="too high", value=0.9)]
    result = normalizer.normalize(alerts)
    s = str(result.normalized[0])
    assert "CRITICAL" in s
    assert "p1" in s
    assert "error_rate" in s


def test_original_alert_preserved(normalizer):
    a = _alert()
    result = normalizer.normalize([a])
    assert result.normalized[0].original is a


def test_empty_alerts_returns_empty_result(normalizer):
    result = normalizer.normalize([])
    assert result.total == 0
    assert result.normalized == []
    assert result.skipped == []
