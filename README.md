# pipewatch

> CLI tool to monitor and alert on ETL pipeline health with configurable thresholds

## Installation

```bash
pip install pipewatch
```

## Usage

```bash
# Monitor a pipeline with default thresholds
pipewatch monitor --pipeline my_etl_job

# Run with a custom config file
pipewatch monitor --config pipewatch.yaml

# Check pipeline status and view recent alerts
pipewatch status --pipeline my_etl_job --last 24h
```

**Example `pipewatch.yaml`:**

```yaml
pipelines:
  my_etl_job:
    max_duration_minutes: 60
    max_failure_rate: 0.05
    alert:
      email: ops-team@example.com
      slack_webhook: https://hooks.slack.com/...
```

```bash
# Trigger an immediate health check
pipewatch check --pipeline my_etl_job
```

## Features

- Real-time monitoring of ETL pipeline runs
- Configurable thresholds for duration, failure rate, and data volume
- Alerts via email, Slack, or PagerDuty
- Simple YAML-based configuration
- Lightweight CLI with minimal dependencies

## Requirements

- Python 3.8+
- Access to your pipeline's metadata store or scheduler API

## License

This project is licensed under the [MIT License](LICENSE).

---

Contributions welcome! Open an issue or submit a pull request.