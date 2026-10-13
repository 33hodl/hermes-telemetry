---
title: Installation
description: Install and enable hermes-telemetry, set up the command-line tool, and install or update the dashboard plugin.
---

Hermes plugins are opt-in: you must both install and enable the plugin.

## Requirements

- A working [Hermes Agent](https://github.com/NousResearch/hermes-agent) install.
- Python 3.8 or newer in the environment that runs the Hermes gateway.
- `pyyaml` in that same environment. The plugin reads and writes `pricing.yaml` and `budget.yaml` with it. The standalone dashboard needs it only for its budget features.
- `watchdog` lets the plugin hot-reload `budget.yaml` when it changes outside the gateway process. The code treats it as optional, but the package metadata declares it as a dependency, so `pip install` pulls it in. Without it, in-chat `/budget set` still applies immediately, but manual edits and CLI changes need a gateway restart.

## Option A: install from GitHub

```bash
hermes plugins install nujovich/hermes-telemetry
hermes plugins enable hermes-telemetry
```

## Option B: manual install

```bash
git clone https://github.com/nujovich/hermes-telemetry ~/.hermes/plugins/hermes-telemetry
hermes plugins enable hermes-telemetry
```

## Restart the gateway

Plugin changes take effect only after the gateway restarts, because the gateway loads its plugin registry at startup.

```bash
hermes gateway restart
```

:::caution
If you enable the plugin and cron jobs never show up in `/stats cron week`, a missing gateway restart is the most likely cause. Cron runs that started before the restart have no telemetry.
:::

## Command-line tool (optional)

To run `hermes-telemetry` from a terminal outside of Hermes sessions, link the bundled launcher onto your `PATH` once:

```bash
chmod +x ~/.hermes/plugins/hermes-telemetry/hermes-telemetry
ln -s ~/.hermes/plugins/hermes-telemetry/hermes-telemetry ~/.local/bin/hermes-telemetry
```

A later `git pull` updates the tool in place, so there is no need to re-link. The launcher detects the Python interpreter that Hermes uses; set `HERMES_PYTHON` to override it.

If your Hermes version supports plugin CLI commands, the same subcommands are also available as `hermes telemetry ...`. See [Standalone CLI](/hermes-telemetry/guides/standalone-cli/).

## Dashboard plugin

hermes-telemetry also ships as a Hermes dashboard plugin. When the Hermes web dashboard starts, it scans `~/.hermes/plugins/<name>/dashboard/manifest.json` and discovers the plugin from the same install path. There is nothing extra to install: you get a **Telemetry** tab plus widgets on the built-in pages. See [Dashboard](/hermes-telemetry/guides/dashboard/) for what it shows.

The standalone dashboard (`dashboard/serve.py`) and the plugin manifest (`dashboard/manifest.json`) live in the same directory, so one `git pull` updates both surfaces together.

## Update

For a manual install (Option B), or an Option A install that is a git checkout:

```bash
cd ~/.hermes/plugins/hermes-telemetry
git pull
hermes gateway restart
```

The dashboard picks up front-end changes on a page reload. If an update changes the plugin's backend routes, restart the Hermes dashboard process as well, because its Python backend is loaded at startup.

Hermes also exposes `GET /api/dashboard/plugins/rescan` to force a plugin rescan without a restart. Like the rest of the dashboard API, it requires the dashboard session token, so a plain unauthenticated `curl` returns `401`.

## Next steps

- [Quick start](/hermes-telemetry/getting-started/quick-start/)
- [Setup wizard](/hermes-telemetry/getting-started/setup-wizard/): what the plugin creates on first load.
