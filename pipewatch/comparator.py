"""Alert comparator: compare two sets of alerts and surface new, resolved, and persisting issues."""
from dataclasses import dataclass, field
from typing import List, Set
from pipewatch.checker import Alert


@dataclass
class ComparisonResult:
    new_alerts: List[Alert] = field(default_factory=list)
    resolved_alerts: List[Alert] = field(default_factory=list)
    persisting_alerts: List[Alert] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.new_alerts) + len(self.resolved_alerts) + len(self.persisting_alerts)

    def summary(self) -> str:
        parts = []
        if self.new_alerts:
            parts.append(f"{len(self.new_alerts)} new")
        if self.resolved_alerts:
            parts.append(f"{len(self.resolved_alerts)} resolved")
        if self.persisting_alerts:
            parts.append(f"{len(self.persisting_alerts)} persisting")
        if not parts:
            return "No changes detected."
        return "Alert changes: " + ", ".join(parts) + "."

    def has_changes(self) -> bool:
        return bool(self.new_alerts or self.resolved_alerts)


def _alert_key(alert: Alert) -> str:
    return f"{alert.pipeline}::{alert.metric}::{alert.severity}"


def compare_alerts(
    previous: List[Alert],
    current: List[Alert],
) -> ComparisonResult:
    """Compare previous and current alert lists.

    Returns a ComparisonResult describing what changed.
    """
    prev_keys: Set[str] = {_alert_key(a) for a in previous}
    curr_keys: Set[str] = {_alert_key(a) for a in current}

    prev_map = {_alert_key(a): a for a in previous}
    curr_map = {_alert_key(a): a for a in current}

    new_keys = curr_keys - prev_keys
    resolved_keys = prev_keys - curr_keys
    persisting_keys = prev_keys & curr_keys

    return ComparisonResult(
        new_alerts=[curr_map[k] for k in sorted(new_keys)],
        resolved_alerts=[prev_map[k] for k in sorted(resolved_keys)],
        persisting_alerts=[curr_map[k] for k in sorted(persisting_keys)],
    )
