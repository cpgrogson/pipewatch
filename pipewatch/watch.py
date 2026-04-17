"""High-level watch command that ties config, checker, notifier, and scheduler."""

import logging
from typing import List

from pipewatch.config import AppConfig, PipelineConfig
from pipewatch.checker import PipelineMetrics, check_thresholds, Alert
from pipewatch.notifier import build_notifier
from pipewatch.reporter import RunReport, PipelineReport
from pipewatch.scheduler import CheckScheduler, ScheduleConfig

logger = logging.getLogger(__name__)


def run_single_check(
    pipelines: List[PipelineConfig],
    metrics_fn,
    app_config: AppConfig,
) -> RunReport:
    """Execute one round of checks across all configured pipelines."""
    report = RunReport()
    notifier = build_notifier(app_config.notifier)
    all_alerts: List[Alert] = []

    for pipeline in pipelines:
        metrics: PipelineMetrics = metrics_fn(pipeline.name)
        alerts = check_thresholds(metrics, pipeline.thresholds)
        pr = PipelineReport(pipeline_name=pipeline.name, metrics=metrics, alerts=alerts)
        report.add(pr)
        all_alerts.extend(alerts)
        if alerts:
            logger.warning("%d alert(s) for pipeline '%s'", len(alerts), pipeline.name)

    notifier.send(all_alerts)
    return report


def start_watch(
    app_config: AppConfig,
    metrics_fn,
    interval_seconds: int = 60,
    max_runs=None,
) -> None:
    """Start the scheduler loop for continuous pipeline monitoring."""
    schedule_cfg = ScheduleConfig(
        interval_seconds=interval_seconds,
        max_runs=max_runs,
    )

    def check_fn():
        report = run_single_check(app_config.pipelines, metrics_fn, app_config)
        logger.info(
            "Check complete — healthy: %d, alerting: %d",
            report.healthy_count,
            report.alerting_count,
        )

    scheduler = CheckScheduler(schedule_cfg, check_fn)
    scheduler.start()
