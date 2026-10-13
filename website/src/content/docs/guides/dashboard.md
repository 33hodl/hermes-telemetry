---
title: Dashboard
description: The standalone web dashboard and the Hermes dashboard plugin, and when to use each.
---

hermes-telemetry ships two dashboards that read the same SQLite database. They share no Python code: the isolation is enforced by `tests/test_dashboard_plugin_isolation.py`.

| Surface | Lives at | Best for |
| --- | --- | --- |
| **Standalone** | `dashboard/serve.py`, started with `python3 serve.py` and served at `http://localhost:8765` | Headless or SSH access, cron-only deployments, and environments without the Hermes web dashboard. |
| **Hermes plugin** | `dashboard/manifest.json` and `dashboard/plugin_api.py` | Interactive use alongside other Hermes features: theming, header and sidebar slots, and the dashboard's native authentication. |

Both surfaces expose the intelligence features (efficiency scores, smell detection, burn-rate forecast).

[![Dashboard overview](https://github.com/nujovich/hermes-telemetry/raw/main/docs/screenshots/dashboard-overview.png)](https://github.com/nujovich/hermes-telemetry/raw/main/docs/screenshots/dashboard-overview.png)

## Standalone dashboard

A self-contained HTML dashboard for people who prefer a visual interface over slash commands. It needs no web framework and no build step: it is the Python standard library, plus `pyyaml` for the budget features (without it the budget panel falls back to raw text), and Chart.js is served from a vendored local copy.

### Run it

```bash
cd ~/.hermes/plugins/hermes-telemetry/dashboard
python3 serve.py                  # http://localhost:8765, loopback only
python3 serve.py --port 9090      # custom port, still loopback
python3 serve.py 9090             # positional port (kept for compatibility)
```

Then open `http://localhost:8765` in a browser. The dashboard reads the telemetry database from the [shared telemetry home](/hermes-telemetry/guides/profiles/) when `HERMES_TELEMETRY_HOME` is set, and from `HERMES_HOME` otherwise.

### What it shows

- **Home:** summary cards, editable budget bars, daily cost, top tools, cron cost, provider distribution, cron jobs, and recent sessions.
- **Breakdown:** token breakdown, provider cost breakdown, cache efficiency, model efficiency, model usage trends, model share delta, a daily token table, and the investigation workspace.
- **Request:** provider health and anomaly signals, request forensics, and a request detail drawer.
- **Tool:** tool analytics and a tool failure heatmap.
- **Error:** run-status groups, failed tools, recent incidents, and a cron failure and waste center.
- **Investigation workspace:** click-through drilldown by provider, model, day, status, platform, cron job, tool, and free-text search.
- **Drawers:** session and request detail side drawers, with chips that lead back into filtered investigation views.
- **Viewer-local timestamps:** dates and times follow the browser's timezone, and budget windows are computed for that timezone too.
- **Soft-hidden deleted sessions:** sessions marked deleted in Hermes metadata are hidden from session tables by default. Aggregate historical totals stay intact.
- **View time selector** (in the settings menu): All time (the default), Today, This week, This month, and several rolling ranges from the last 15 minutes up to the last year.
- **Language toggle:** English, with a Russian translation. See [Dashboard i18n](/hermes-telemetry/internals/dashboard-i18n-enru-toggle/).

### Auto-refresh

A header selector offers `Off`, `5s`, `10s`, `20s`, and `1min`. The default is 20 seconds. The choice is saved in the browser's `localStorage`, and background refreshes keep the current page visible rather than blanking the UI.

### Budgets in the standalone dashboard

Unlike the plugin, the standalone dashboard can edit budgets. The budget bars on the Home tab write to `budget.yaml` through `POST /api/budget`. Anyone who can reach the dashboard can therefore change your limits, which is one more reason to keep it off untrusted networks.

### Accessing it from another host

:::danger
The standalone dashboard has **no authentication**. Anyone who can reach the port sees every captured token count, cost, and tool-call detail, and can edit budgets. By default it binds to `127.0.0.1`, which other machines cannot reach.
:::

If your Hermes server is headless, such as a Raspberry Pi, VPS, or NAS, and you browse from a laptop, you have two options.

**Recommended: an SSH tunnel.** It needs no server-side change and leaves the safe default in place.

```bash
# Start the dashboard on the server as usual
ssh server "cd ~/.hermes/plugins/hermes-telemetry/dashboard && python3 serve.py &"

# Tunnel from your client
ssh -L 8765:localhost:8765 -N server &

# Browse on the client
open http://localhost:8765
```

**Trusted-LAN shortcut: `--host 0.0.0.0`.**

```bash
python3 serve.py --host 0.0.0.0
```

The script prints a warning when it binds to any non-loopback interface. Use this only on a network where you trust every host, and never expose it to the public internet. The dashboard ships without an auth layer by design; see `CONTRIBUTING.md` in the repository if you want to add one.

## Hermes dashboard plugin

When the Hermes web dashboard runs, it discovers the plugin from the same install path with no extra steps. You get a dedicated **Telemetry** tab plus widgets on the built-in pages. See [Installation](/hermes-telemetry/getting-started/installation/#dashboard-plugin) for installing and updating it.

### The Telemetry tab

The `/telemetry` tab has seven sub-tabs: **Summary**, **Runs**, **Requests**, **Providers**, **Cron**, **Budgets**, and **Efficiency**.

**Summary.** Six stat cards for the last 24 hours: cost, total runs (with the failed count), API calls, tokens in and out, and average latency.

[![Summary](https://github.com/nujovich/hermes-telemetry/raw/main/docs/plugin/01-summary.png)](https://github.com/nujovich/hermes-telemetry/raw/main/docs/plugin/01-summary.png)

**Runs.** One row per session from the last 7 days: start time, session id, platform, model, provider, status, cost, and token counts. Cron sessions appear as `cron_<job>_...`.

[![Runs](https://github.com/nujovich/hermes-telemetry/raw/main/docs/plugin/02-runs.png)](https://github.com/nujovich/hermes-telemetry/raw/main/docs/plugin/02-runs.png)

**Requests.** Per-API-call detail: timestamp, model, provider, tokens, cost, latency, and an `Est?` column that flags rows recorded with `estimated=1` because the provider returned no usage.

[![Requests](https://github.com/nujovich/hermes-telemetry/raw/main/docs/plugin/03-requests.png)](https://github.com/nujovich/hermes-telemetry/raw/main/docs/plugin/03-requests.png)

**Providers.** Totals aggregated by provider: calls, how many were estimated, cost, and tokens. Useful for spotting a provider whose share of the bill is out of proportion to its share of traffic.

[![Providers](https://github.com/nujovich/hermes-telemetry/raw/main/docs/plugin/04-providers.png)](https://github.com/nujovich/hermes-telemetry/raw/main/docs/plugin/04-providers.png)

**Cron.** Runs aggregated by cron job: total runs, the ok and failed split, cost, and last execution.

[![Cron tab](https://github.com/nujovich/hermes-telemetry/raw/main/docs/plugin/05-cron-tab.png)](https://github.com/nujovich/hermes-telemetry/raw/main/docs/plugin/05-cron-tab.png)

**Budgets.** Global daily and monthly budgets read live from `budget.yaml`, with a traffic-light badge: the hard badge appears once spend exceeds the hard cap, and soft and ok states use distinct variants. A burn-rate forecast is shown here as well.

[![Budgets tab](https://github.com/nujovich/hermes-telemetry/raw/main/docs/plugin/06-budgets-tab.png)](https://github.com/nujovich/hermes-telemetry/raw/main/docs/plugin/06-budgets-tab.png)

**Efficiency.** Per-session efficiency scores and their average.

Free-to-paid model transitions and model-unavailable alerts also appear on the Telemetry page when any fall in the recent window.

### Slot widgets

The plugin injects widgets into four slots of the Hermes shell.

| Slot | Page | What it shows |
| --- | --- | --- |
| `sessions:top` | Sessions | A pinned card with the most recent run that had real activity: cost, tokens in and out, and model. |
| `cron:top` | Cron | Aggregate 7-day cron cost, plus a `N FAILED` badge when any job failed in the window. |
| `header-right` | Header | Compact 24-hour spend and its percentage of the global daily cap. The badge turns destructive on a hard breach. |
| `analytics:bottom` | Analytics | A daily cost chart. Chart.js is served from a vendored local asset, with a CDN fallback only. |

[![sessions:top slot](https://github.com/nujovich/hermes-telemetry/raw/main/docs/plugin/07-slot-sessions-top.png)](https://github.com/nujovich/hermes-telemetry/raw/main/docs/plugin/07-slot-sessions-top.png)

[![header-right slot](https://github.com/nujovich/hermes-telemetry/raw/main/docs/plugin/09-slot-header-right.png)](https://github.com/nujovich/hermes-telemetry/raw/main/docs/plugin/09-slot-header-right.png)

### Profile filter

When telemetry is consolidated through `HERMES_TELEMETRY_HOME`, a selector in the Telemetry tab filters the views by Hermes profile. It is hidden when no profile data is present. See [Profiles and shared home](/hermes-telemetry/guides/profiles/).

### Backend routes

The plugin exposes a read-only FastAPI router at `/api/plugins/hermes-telemetry/*`. It opens the database with `PRAGMA query_only=ON` and never writes to `telemetry.db`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Smoke endpoint. |
| GET | `/summary?window_hours=24` | Run and LLM-call totals plus the daily cost series. |
| GET | `/token-breakdown?window_hours=24` | Tokens by component. |
| GET | `/profiles` | Distinct profiles present in the data (feeds the profile filter). |
| GET | `/runs?limit=50&window_hours=0` | Recent runs. |
| GET | `/requests?limit=100&window_hours=0` | Recent LLM calls. |
| GET | `/providers?window_hours=24` | Per-provider totals. |
| GET | `/cron?window_hours=168` | Per-cron-job aggregate. |
| GET | `/session/{session_id}` | Single-session detail. |
| GET | `/budget` | Global daily and monthly budget status. |
| GET | `/efficiency?window_hours=24` | Per-session efficiency scores and the average. |
| GET | `/smells?window_hours=24` | Detected anti-patterns. |
| GET | `/forecast?window=monthly` | Global burn-rate projection. |
| GET | `/tier-transitions?window_hours=72` | Recent free-to-paid model transitions. |
| GET | `/model-unavailable?window_hours=72` | Recent model-unavailable alerts. |

The aggregate routes accept an optional `profile` query parameter. For how the plugin is wired into the Hermes shell, including the slot catalogue and why the two surfaces share no code, see [Dashboard plugin surface](/hermes-telemetry/internals/dashboard-plugin-surface/).

:::tip
`tools/seed_demo_data.py` populates an isolated `HERMES_HOME` with realistic demo data, which is handy for trying the dashboards without touching real telemetry.
:::
