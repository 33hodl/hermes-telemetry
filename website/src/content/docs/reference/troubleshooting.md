---
title: Troubleshooting
description: Fixes for the most common hermes-telemetry problems.
---

## `/stats cron week` shows "No cron runs in the last 7 days"

The gateway loaded before the plugin was enabled. Restart it and run a cron job again:

```bash
hermes gateway restart
```

## Budget limits are missing or out of date

`/budget` shows `(no limit set)`, or an old limit, after you edited `budget.yaml` by hand.

The plugin caches the budget configuration in memory. It reloads the file automatically when the `watchdog` package is installed. If it is not, use `/budget set global daily <amount>`, which writes the file and reloads at once, or restart the gateway. Also check `telemetry.log`: a YAML syntax error disables budgets rather than crashing, and logs a warning.

## Cost is `$0.00` for every session

The model is not in the pricing table. Look in `telemetry.log` for a one-time warning such as:

```text
hermes-telemetry: unknown model 'openrouter/some-model' — cost recorded as $0.00
```

or, when the call carried a provider name:

```text
hermes-telemetry: no price for model 'some-model' under provider 'nous' — cost recorded as $0.00
```

Add the model to `pricing.yaml` under the provider's native model id. Running `/setup pricing auto` also works, but it overwrites the whole file and discards hand edits, so back it up first. See [Pricing](/hermes-telemetry/guides/pricing/). If `/stats models` marks the row `free tier` or `subscription/free-tier`, the zero is intentional.

## `Est%` is above zero for my provider

Your provider returns `usage=None` for some or all calls, so tokens are estimated. Check `/stats providers` to see which providers are affected. If `Est%` is 100% for your main provider, all of its spend is estimated, and under the default `warn_only` mode hard budget verdicts degrade to soft. See [Provider probe](/hermes-telemetry/guides/provider-probe/).

## A hard breach did not stop the session

Budgets block tool calls, not model calls. A session that only generates text never reaches the gate, and the response already in flight when a limit is crossed still completes. Also check whether the verdict was degraded by estimated data (`~est` in `/budget`), and whether the plugin is running in `observe` mode. See [Budgets](/hermes-telemetry/guides/budgets/).

## The plugin is not loading at all

Check `telemetry.log` for errors. Common causes:

- `pyyaml` is missing from the gateway's Python environment: `pip install pyyaml`.
- The plugin is not listed in `plugins.enabled` in `config.yaml`: `hermes plugins enable hermes-telemetry`.
- A syntax error in `pricing.yaml` or `budget.yaml`.
- A second copy of the plugin, such as a backup directory, sits in `~/.hermes/plugins/`. Hermes indexes plugins by the `name` in their manifest, and when two directories share a name, one silently shadows the other, often the backup over the active copy. Keep backups outside `~/.hermes/plugins/`.

## `hermes-telemetry stats efficiency` fails with "invalid choice"

The standalone CLI does not include the `efficiency`, `smells`, and `raw` views. Use the in-chat `/stats efficiency` and `/stats smells`, or the dashboard. See [Standalone CLI](/hermes-telemetry/guides/standalone-cli/).

## The Telemetry tab does not appear in the Hermes dashboard

Reload the page after the dashboard process has started. The dashboard discovers plugins at startup from `~/.hermes/plugins/<name>/dashboard/manifest.json`; if you installed the plugin while the dashboard was running, restart the dashboard process. See [Installation](/hermes-telemetry/getting-started/installation/#dashboard-plugin).

## The standalone dashboard is unreachable from another machine

By default it binds to `127.0.0.1` only. Use an SSH tunnel, as described in [Dashboard](/hermes-telemetry/guides/dashboard/#accessing-it-from-another-host).
