---
title: Provider probe
description: Verify once that your provider returns real token usage.
---

Budget verdicts are only as good as the usage data behind them. Run this probe **once** after enabling the plugin to find out whether your provider reports real usage.

1. Run one short session. Any minimal task works.
2. Run `/stats providers`.
3. Read the `Est%` column for your provider.

| `Est%` | Meaning |
| --- | --- |
| `0%` | The provider returns real usage data, and budget verdicts rest on real numbers. Consider setting `on_estimated.mode: enforce` for strict enforcement. |
| Above `0%` | The provider omits usage in some responses. Those calls are estimated locally and flagged, and under the default `warn_only` mode hard budget verdicts are degraded to soft. For Nous Portal providers, `telemetry.log` also records a one-time warning; for other providers, rely on the `Est%` column. |

If `Est%` is 100% for your main provider, all spend is estimated.

See [Estimated data and budget degradation](/hermes-telemetry/guides/budgets/#estimated-data-and-budget-degradation) for what each mode does, and [Metrics: real vs estimated](/hermes-telemetry/internals/metrics-real-vs-estimated/) for how each metric is sourced.
