# Monitoring

`monitor` is an in-process arm.

```bash
kraken monitor
kraken monitor --url https://api.topta.co
kraken run monitor snapshot
kraken run monitor ping --payload '{"url":"https://api.topta.co"}'
kraken workflow run examples/workflows/monitor.yaml
```

`snapshot` writes `~/.kraken/logs/monitor.jsonl` and reuses `kraken doctor` checks. `ping` is an optional URL probe (fails soft).

Notify: `KRAKEN_NOTIFY_WEBHOOK` still fires on each `run`. A monitor workflow is how you batch local + remote checks.
