"""Configuration loader for pipewatch thresholds and pipeline definitions."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import yaml


@dataclass
class ThresholdConfig:
    max_duration_seconds: Optional[float] = None
    max_error_rate: Optional[float] = None
    min_rows_processed: Optional[int] = None
    max_lag_seconds: Optional[float] = None


@dataclass
class PipelineConfig:
    name: str
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    tags: List[str] = field(default_factory=list)


@dataclass
class AppConfig:
    pipelines: Dict[str, PipelineConfig] = field(default_factory=dict)
    default_thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)


def load_config(path: str) -> AppConfig:
    """Load and parse a YAML config file into an AppConfig object."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        raw = yaml.safe_load(f) or {}

    default_raw = raw.get("default_thresholds", {})
    default_thresholds = ThresholdConfig(**{k: v for k, v in default_raw.items() if k in ThresholdConfig.__dataclass_fields__})

    pipelines: Dict[str, PipelineConfig] = {}
    for name, cfg in raw.get("pipelines", {}).items():
        t_raw = cfg.get("thresholds", {})
        thresholds = ThresholdConfig(**{k: v for k, v in t_raw.items() if k in ThresholdConfig.__dataclass_fields__})
        pipelines[name] = PipelineConfig(
            name=name,
            thresholds=thresholds,
            tags=cfg.get("tags", []),
        )

    return AppConfig(pipelines=pipelines, default_thresholds=default_thresholds)
