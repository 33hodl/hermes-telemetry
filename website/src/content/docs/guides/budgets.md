---
title: Budgets
description: Configure budget.yaml, and understand exactly what soft and hard enforcement can and cannot stop.
---

Budgets let you cap spend per scope and window. hermes-telemetry evaluates them from the telemetry it already records, with no network calls.

![Budget enforcement demo: a $0.001 daily global cap is set, current spend already exceeds it, and the next cron run is blocked by the resulting hard breach](https://github.com/nujovich/hermes-telemetry/raw/main/docs/budget_enforcement.gif)

*`/budget set global daily 0.001` writes the cap to `budget.yaml`. Spend ($0.0102) already exceeds it, so `/budget` re-renders at 1020% `[daily]`, a hard breach, and the next cron run is blocked by the budget.*

## What enforcement can and cannot do

Hermes does not let a plugin abort a model call that is already in flight. Return values from `pre_llm_call` and `pre_api_request` cannot cancel a call. So hermes-telemetry enforces budgets at the one place Hermes lets a plugin say no: the **tool-call gate** (`pre_tool_call`).

| Level | Trigger | Effect | Repeats |
| --- | --- | --- | --- |
| **Soft** | Spend reaches `soft_pct` of a limit (80% by default) | A one-time notice is injected into the conversation before the next model turn | Once per window per scope |
| **Hard** | Spend reaches `hard_pct` of a limit (100% by default) | A one-time notice is injected, and **every subsequent tool call is blocked** with an explanatory message | Every tool call until the window resets |
| **Cron pause** | A hard breach of a `cron_job` scope | The cron job is paused for future runs | Once per window per scope |

:::caution
The model response that is already being generated when a limit is crossed still completes and is billed. What the budget prevents is further tool-driven work. A budget is a tool-gate, not a hard spending cap on model calls.
:::

In practice, a hard breach ends the agent loop at the next tool boundary: the tool call fails with a budget message, and the agent can no longer act. Two consequences follow:

- A session that only generates text and never calls a tool never reaches the gate, so budgets cannot stop it.
- A cron pause applies only when the breached scope is `cron_job`. A breach of the `global` scope blocks tool calls in every session but does not pause jobs by itself. The plugin never resumes a paused job: resume it with Hermes's cron tooling once you have raised the limit.

### How it works

1. **Before each model turn** (`pre_llm_call`, once per turn). The plugin evaluates every scope that applies to the session. If any scope has a soft or hard verdict that has not yet been announced in the current window, it injects a one-time notice. An anti-spam ledger in the `budget_alerts` table guarantees one notice per window. The same hook captures the sender id used by `per_sender` budgets.
2. **Before every tool call** (`pre_tool_call`). The plugin re-evaluates the scopes. If any is in hard breach, it returns a block decision, which Hermes turns into an error for the model instead of running the tool. For a breached `cron_job` scope it also pauses the job.

The cron pause check also runs in step 1, so a hard-breached cron job is paused at its next model turn as well, not only at the tool gate.

Verdicts are cached for a few seconds so that the gate, which runs on every tool call, does not query SQLite each time.

Delegated work (`delegate_task`) is attributed to the cron job that started it for reporting, so `per_cron_job` spend includes subagent cost. A detached child session is still gated only against the `global` scope (plus its own sender or profile, when set) while it runs.

## Modes

Budget behavior depends on the plugin `mode` setting (`enforce` by default). In `observe` mode the plugin records and reports but never injects budget notices, blocks tools, or pauses jobs. See [Setup wizard](/hermes-telemetry/getting-started/setup-wizard/#enforcement-mode).

## `budget.yaml`

With no `budget.yaml`, budgets are disabled and nothing is enforced.

```yaml
budgets:
  global:
    daily_usd: 2.00
    monthly_usd: 50.00
  per_cron_job:
    default:
      daily_usd: 1.00
    overrides:
      daily_email_report:
        daily_usd: 3.00
  per_sender:
    default:
      daily_usd: 2.00
    overrides:
      premium_user_123:
        daily_usd: 5.00
  per_profile:
    default:
      daily_usd: 2.00
    overrides:
      coder:
        daily_usd: 10.00

thresholds:
  soft_pct: 0.80    # notice at 80% of the limit
  hard_pct: 1.00    # block at 100%

on_estimated:
  mode: warn_only   # warn_only (default) | enforce
```

### Scopes

| Scope | How spend is calculated |
| --- | --- |
| `global` | Every session and cron job combined. |
| `per_cron_job` | Sessions whose `cron_job_id` matches, plus every subagent session reachable from them through the delegation tree. |
| `per_sender` | Sessions from a specific sender (multi-user gateways). |
| `per_profile` | Sessions tagged with a specific Hermes profile. Sessions with no profile are excluded. |

A per-id entry under `overrides` wins over `default`. A scope with no configured limit for a window is not enforced for that window.

`global` always sums every session, so the other scopes only regroup the same spend: there is no double counting.

### Windows

Daily and monthly windows are computed in the machine's **local timezone**. A cron job that runs at 11:59 PM and another at 12:01 AM count against different daily windows.

### Changing limits

The in-chat `/budget set` writes `budget.yaml` atomically and applies immediately, because it runs inside the gateway process. `hermes-telemetry budget set` and manual edits run outside that process: the gateway picks them up through its file watcher when `watchdog` is installed, and otherwise only after a restart. See [Slash commands](/hermes-telemetry/guides/slash-commands/#budget).

## Estimated data and budget degradation

When a provider returns `usage=None`, the plugin estimates tokens and flags the row as `estimated=1`. Models with no fixed price, such as OpenRouter `auto` routing, are normalized to `$0.00` and flagged `_estimated_price: true`. Because numbers built on estimates may be inaccurate, the budget engine has a safety valve controlled by `on_estimated.mode`:

- **`warn_only` (default).** If a hard verdict rests partly on estimated rows or estimated-price models, it is **degraded to soft**: you get a warning, but tools are not blocked. A budget built on estimates should not hard-stop work.
- **`enforce`.** Hard verdicts take effect regardless of data quality. Use this when your provider reports real usage (`Est%` is 0 in `/stats providers`) or when estimates are acceptable to you.

A degraded verdict is shown with a `~est` marker in `/budget`:

```text
! global                       $   7.8185 / $    5.00    156%  [daily] ~est
```

Here spend is 156% of the daily limit, yet the flag is `!` (soft), not `█` (hard), because the verdict rests partly on estimated data and `warn_only` is active.

Use `/stats providers` to see the `Est%` column per provider, and run the [provider probe](/hermes-telemetry/guides/provider-probe/) once after enabling the plugin.

## Related notices

Besides budget notices, the plugin injects a one-time warning when a model that was previously free starts incurring cost. See [Pricing](/hermes-telemetry/guides/pricing/#free-tier-and-subscription-models).

## Going deeper

[Budget engine](/hermes-telemetry/internals/budget-engine/) in the Internals section documents the enforcement audit, the verdict cache, and the anti-spam ledger. [Known limitations](/hermes-telemetry/reference/known-limitations/) lists the enforcement gaps.
