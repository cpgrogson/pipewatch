"""Alert sampler: probabilistically or deterministically sample alerts to reduce noise."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.checker import Alert


@dataclass
class SampleRule:
    pipeline: str  # '*' for wildcard
    metric: str    # '*' for wildcard
    rate: float    # 0.0 - 1.0, fraction of alerts to keep
    seed: Optional[str] = None  # if set, use deterministic sampling via hash

    def matches(self, alert: Alert) -> bool:
        pipeline_match = self.pipeline == "*" or self.pipeline == alert.pipeline
        metric_match = self.metric == "*" or self.metric == alert.metric
        return pipeline_match and metric_match

    def should_keep(self, alert: Alert) -> bool:
        """Return True if this alert should be kept (not sampled away)."""
        if self.rate >= 1.0:
            return True
        if self.rate <= 0.0:
            return False
        if self.seed is not None:
            raw = f"{self.seed}:{alert.pipeline}:{alert.metric}:{alert.message}"
            digest = hashlib.md5(raw.encode()).hexdigest()
            value = int(digest[:8], 16) / 0xFFFFFFFF
            return value < self.rate
        return random.random() < self.rate


@dataclass
class SampledResult:
    kept: List[Alert] = field(default_factory=list)
    dropped: List[Alert] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.kept) + len(self.dropped)

    def summary(self) -> str:
        return (
            f"Sampled {self.total} alerts: "
            f"{len(self.kept)} kept, {len(self.dropped)} dropped"
        )


class AlertSampler:
    def __init__(self, rules: Optional[List[SampleRule]] = None) -> None:
        self.rules: List[SampleRule] = rules or []

    def add_rule(self, rule: SampleRule) -> None:
        self.rules.append(rule)

    def sample(self, alerts: List[Alert]) -> SampledResult:
        result = SampledResult()
        for alert in alerts:
            rule = self._find_rule(alert)
            if rule is None or rule.should_keep(alert):
                result.kept.append(alert)
            else:
                result.dropped.append(alert)
        return result

    def _find_rule(self, alert: Alert) -> Optional[SampleRule]:
        for rule in self.rules:
            if rule.matches(alert):
                return rule
        return None
