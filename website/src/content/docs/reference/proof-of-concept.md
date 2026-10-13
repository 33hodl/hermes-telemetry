---
title: Proof of concept
description: A recorded end-to-end validation of cost capture and budget enforcement.
---

:::note
This validation was recorded against hermes-telemetry v0.2.0 on a development gateway. It is kept as a worked example of the capture, pricing, and budget flow. Current behavior is described in [Budgets](/hermes-telemetry/guides/budgets/) and [Pricing](/hermes-telemetry/guides/pricing/); in particular, enforcement is a tool gate, so a model response already in flight still completes and is billed.
:::

## Setup

- Hermes gateway on Linux (WSL), default model `openrouter/owl-alpha` (free tier).
- hermes-telemetry v0.2.0, loaded in the gateway process, with six cron jobs configured and two used for this run.

## Pricing capture

Models were added to `pricing.yaml`:

```yaml
models:
  "openrouter/owl-alpha":
    input: 0.00
    output: 0.00
  "openrouter/anthropic/claude-sonnet-4-6":
    input: 3.00
    output: 15.00
    cache_read: 0.30
    cache_write: 3.75
  "openrouter/anthropic/claude-opus-4-7":
    input: 5.00
    output: 25.00
    cache_read: 0.50
    cache_write: 6.25
```

`on_estimated.mode` was set to `enforce` for deterministic enforcement.

## Budget enforcement test

**Step 1: trigger a hard breach.** With `global.daily_usd: 0.001`, the MCP Lead Gen job (`claude-sonnet-4-6`) spent $0.1812 on its first run, which is 18,120% of the daily limit. That is a hard breach, and in v0.2.0 the job was paused. Current versions pause a job only when its own `cron_job` budget is breached; a `global` breach blocks tool calls but does not pause jobs. See [Budgets](/hermes-telemetry/guides/budgets/).

```text
█ global    $0.1812 / $0.00    18120%  [daily]
                         ↑ 0.001 rounded to 0.00 in the display
```

**Step 2: raise the limit.**

```text
/budget set global daily 2.00
```

```text
global    $0.1812 / $2.00    9%  [daily]
```

**Step 3: verify the job runs normally.** MCP Lead Gen re-ran successfully under the $2.00 daily budget, with `state: scheduled` and `paused_at: null`.

## Cron job cost comparison

| Job | Model | Price (input / output) |
| --- | --- | --- |
| MCP Lead Gen | `claude-sonnet-4-6` | $3.00 / $15.00 per 1M tokens |
| Marketing Highlights | `claude-opus-4-7` | $5.00 / $25.00 per 1M tokens |
| Base sessions (CLI) | `owl-alpha` | $0.00 / $0.00 (free) |

Results from SQLite after all runs:

- **CLI sessions** (`owl-alpha`, free): about 1M tokens in, costing $0.00.
- **MCP Lead Gen** (`claude-sonnet-4-6`): about 892K tokens in, costing $0.314.
- **Marketing Highlights** (`claude-opus-4-7`): about 445K tokens in, costing $2.23.

## Results

| Component | Result |
| --- | --- |
| Token capture from the provider | Real usage (`estimated=0`) |
| Cost estimation with the pricing table | Accurate to the pricing YAML |
| Cron job session tracking | Captured through the `session_id` pattern |
| Budget soft alerts | One-time context injection |
| Budget hard enforcement | Job paused at $0.001 per day (v0.2.0 result; current behavior differs, see [Budgets](/hermes-telemetry/guides/budgets/)) |
| Budget hot reload through `/budget set` | Cache cleared, new limit active |
| Multi-model cost comparison | Sonnet, Opus, and free tier compared |
| Pricing auto-refresh (OpenRouter API) | 320 models fetched, manual overrides preserved |
| Estimated-price model handling | Negative prices normalized to $0.00, with budget degradation |
