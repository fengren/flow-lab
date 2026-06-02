---
name: observability-local-stack
description: Use this skill when the user asks to verify behavior through logs, metrics, traces, dashboards, Loki, Grafana, analytics events, local monitoring, or "日志没有报错". Trigger on "日志", "Loki", "Grafana", "analytics", "埋点", "监控", "看板", "trace", "metrics", or when code changes need runtime evidence.
---

# Observability Local Stack

Use this workflow to turn logs and metrics into verification evidence.

## Verification Flow

1. Identify the user action or system event to verify.
2. Identify expected signals: log line, metric, trace span, analytics event, dashboard value.
3. Run or reproduce the action.
4. Query the narrowest log/metric window.
5. Compare expected vs actual.
6. Report evidence and gaps.

## Signal Checklist

- Logs include request id, user/project id when safe, operation, status, duration.
- Metrics count success/failure and latency where relevant.
- Traces connect frontend/backend/external calls when available.
- Analytics events avoid sensitive payloads.
- Dashboards distinguish zero data from broken ingestion.

## Debug Pattern

If a signal is missing:

- Check event emission.
- Check transport/exporter.
- Check ingestion credentials/config.
- Check query labels and time range.
- Check dashboard panel filters.

## Final Response

Include:

- Query or command used.
- Expected signal.
- Observed result.
- Whether behavior is verified or still inconclusive.
