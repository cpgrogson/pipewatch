"""Alert dispatcher: routes, enriches, deduplicates, and sends alerts via notifiers."""

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.checker import Alert
from pipewatch.notifier import NotifierBackend
from pipewatch.deduplicator import DeduplicatorStore
from pipewatch.silencer import SilenceStore
from pipewatch.router import AlertRouter
from pipewatch.enricher import AlertEnricher
from pipewatch.prioritizer import AlertPrioritizer


@dataclass
class DispatchResult:
    sent: List[Alert] = field(default_factory=list)
    deduplicated: List[Alert] = field(default_factory=list)
    silenced: List[Alert] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.sent) + len(self.deduplicated) + len(self.silenced)

    def summary(self) -> str:
        return (
            f"Dispatched {len(self.sent)} alerts "
            f"({len(self.deduplicated)} deduplicated, {len(self.silenced)} silenced)"
        )


class AlertDispatcher:
    def __init__(
        self,
        notifiers: List[NotifierBackend],
        deduplicator: Optional[DeduplicatorStore] = None,
        silencer: Optional[SilenceStore] = None,
        router: Optional[AlertRouter] = None,
        enricher: Optional[AlertEnricher] = None,
        prioritizer: Optional[AlertPrioritizer] = None,
    ):
        self.notifiers = notifiers
        self.deduplicator = deduplicator
        self.silencer = silencer
        self.router = router
        self.enricher = enricher
        self.prioritizer = prioritizer

    def dispatch(self, alerts: List[Alert]) -> DispatchResult:
        result = DispatchResult()

        for alert in alerts:
            if self.silencer and self.silencer.is_silenced(alert.pipeline, alert.metric):
                result.silenced.append(alert)
                continue

            if self.deduplicator and self.deduplicator.is_duplicate(alert):
                result.deduplicated.append(alert)
                continue

            if self.deduplicator:
                self.deduplicator.record(alert)

            enriched = self.enricher.enrich([alert])[0] if self.enricher else alert
            prioritized = self.prioritizer.prioritize([enriched])[0] if self.prioritizer else enriched

            if self.router:
                targets = self.router.route([prioritized])
                for notifier_key, routed_alerts in targets.items():
                    for notifier in self.notifiers:
                        if getattr(notifier, 'name', None) == notifier_key or notifier_key == 'fallback':
                            notifier.send(routed_alerts)
            else:
                for notifier in self.notifiers:
                    notifier.send([prioritized])

            result.sent.append(alert)

        return result
