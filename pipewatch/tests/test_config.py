"""Tests for the config loader."""

import os
import textwrap

import pytest

from pipewatch.config import load_config


@pytest.fixture
def config_file(tmp_path):
    content = textwrap.dedent("""
        default_thresholds:
          max_duration_seconds: 600
          max_error_rate: 0.1

        pipelines:
          etl_daily:
            tags: [production]
            thresholds:
              max_duration_seconds: 300
              min_rows_processed: 1000
          etl_hourly:
            tags: [staging]
            thresholds:
              max_lag_seconds: 30
    """)
    p = tmp_path / "pipewatch.yaml"
    p.write_text(content)
    return str(p)


def test_load_config_pipelines(config_file):
    cfg = load_config(config_file)
    assert "etl_daily" in cfg.pipelines
    assert "etl_hourly" in cfg.pipelines


def test_load_config_default_thresholds(config_file):
    cfg = load_config(config_file)
    assert cfg.default_thresholds.max_duration_seconds == 600
    assert cfg.default_thresholds.max_error_rate == 0.1


def test_pipeline_specific_thresholds(config_file):
    cfg = load_config(config_file)
    daily = cfg.pipelines["etl_daily"]
    assert daily.thresholds.max_duration_seconds == 300
    assert daily.thresholds.min_rows_processed == 1000


def test_pipeline_tags(config_file):
    cfg = load_config(config_file)
    assert "production" in cfg.pipelines["etl_daily"].tags


def test_missing_config_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(str(tmp_path / "nonexistent.yaml"))
