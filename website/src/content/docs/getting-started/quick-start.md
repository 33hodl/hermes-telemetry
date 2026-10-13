---
title: Quick start
description: Capture your first telemetry in four steps.
---

1. [Install and enable](/hermes-telemetry/getting-started/installation/) the plugin.
2. Restart the gateway: `hermes gateway restart`.
3. Run any Hermes session, then type `/stats` to see what was captured.
4. Optionally review `pricing.yaml` and `budget.yaml`, which the [setup wizard](/hermes-telemetry/getting-started/setup-wizard/) generates on first load.

The plugin captures data automatically through Hermes hooks. No agent action is required.

## Check that it works

Inside a session:

```text
/stats              # last 24 hours: sessions, tokens, cost, top tools
/budget             # spend versus limits for every scope
```

Outside a session:

```bash
hermes-telemetry stats today
hermes-telemetry budget
```

Then run the one-time [provider probe](/hermes-telemetry/guides/provider-probe/) to confirm that your provider reports real token usage.

## Where to go next

- [Slash commands](/hermes-telemetry/guides/slash-commands/): `/stats` and `/budget` in detail.
- [Budgets](/hermes-telemetry/guides/budgets/): set limits and understand what enforcement can and cannot do.
- [Dashboard](/hermes-telemetry/guides/dashboard/): the visual interface.
- [Troubleshooting](/hermes-telemetry/reference/troubleshooting/): if `/stats` shows nothing.
