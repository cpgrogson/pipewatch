"""Alert enricher: attaches contextual metadata to alerts before dispatch."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.checker import Alert


@dataclass
class EnrichmentRule:
    """Defines metadata to attach when pipeline and/or metric matches."""
    pipeline: str  # '*' for wildcard
    metric: str    # '*' for wildcard
    tags: Dict[str, str] = field(default_factory=dict)
    note: Optional[str] = None

    def matches(self, alert: Alert) -> bool:
        pipeline_match = self.pipeline == "*" or self.pipeline == alert.pipeline
        metric_match = self.metric == "*" or self.metric == alert.metric
        return pipeline_match and metric_match


@dataclass
class EnrichedAlert:
    """An alert with additional context attached by enrichment rules."""
    alert: Alert
    tags: Dict[str, str] = field(default_factory=dict)
    note: Optional[str] = None

    def __str__(self) -> str:
        base = str(self.alert)
        extras = []
        if self.tags:
            tag_str = ", ".join(f"{k}={v}" for k, v in self.tags.items())
            extras.append(f"tags=[{tag_str}]")
        if self.note:
            extras.append(f"note='{self.note}'")
        suffix = f" ({', '.join(extras)})" if extras else ""
        return base + suffix


class AlertEnricher:
    """Applies enrichment rules to a list of alerts."""

    def __init__(self) -> None:
        self._rules: List[EnrichmentRule] = []

    def add_rule(self, rule: EnrichmentRule) -> None:
        self._rules.append(rule)

    def enrich(self, alerts: List[Alert]) -> List[EnrichedAlert]:
        enriched: List[EnrichedAlert] = []
        for alert in alerts:
            merged_tags: Dict[str, str] = {}
            merged_note: Optional[str] = None
            for rule in self._rules:
                if rule.matches(alert):
                    merged_tags.update(rule.tags)
                    if rule.note and merged_note is None:
                        merged_note = rule.note
            enriched.append(EnrichedAlert(alert=alert, tags=merged_tags, note=merged_note))
        return enriched
