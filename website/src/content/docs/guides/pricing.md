---
title: Pricing
description: How cost is calculated, how to override prices in pricing.yaml, and how auto-refresh and pricing snapshots work.
---

Cost is always an **estimate**: token counts reported by the provider multiplied by a price. hermes-telemetry never calls an external pricing API at call time. Prices come from Hermes core's own tariff snapshots, from `pricing.yaml`, and from a built-in table.

## How a price is resolved

For each LLM call the plugin picks the first match in this order:

1. **A declared subscription entry or a `:free` model.** An exact `pricing.yaml` entry tagged `_subscription: true` wins over everything, because Hermes core cannot know about your flat-rate deal. A model id that ends in `:free` resolves to `$0`.
2. **A core pricing snapshot.** The tariff Hermes core itself resolved for this exact `(provider, model)` pair, recorded locally the first time the model is called. This is the primary price source once a snapshot exists.
3. **A `pricing.yaml` entry:** an exact, case-insensitive match, whether hand-written or auto-fetched.
4. **The built-in price table:** an exact match.
5. **A longest-prefix match** over all of the above plus a table of model families. For example, `claude-sonnet` matches `claude-sonnet-4-6-future`.
6. **The Google alternate form.** `gemini-X` and `google/gemini-X` are treated as the same model.
7. **Unknown.** Cost is recorded as `$0.00` and a one-time warning is written to `telemetry.log`.

Every candidate from step 3 onward is filtered by the call's provider, so a price sourced from one provider is never applied to a call served by another. For example, an OpenRouter rate must not price a Nous Portal call that happens to share a model name. Auto-fetched OpenRouter entries carry `_source: openrouter` and are skipped for other providers. Hand-added and built-in entries are provider-neutral. If the only match is one the guard rejected, it is still applied as a best-effort estimate and the call is flagged as provider-assumed: it counts toward spend, and the `Asm%` column in `/stats providers` makes the assumption visible so you can pin the rate.

Cache and reasoning prices default sensibly: cache read and write are derived from the input price with multipliers, and reasoning defaults to the output price.

## `pricing.yaml`

Prices are in USD per 1 million tokens. The file lives in the [telemetry directory](/hermes-telemetry/reference/configuration/). Without entries, an unknown model records `$0.00`.

```yaml
models:
  # Free model
  "openrouter/owl-alpha":
    input: 0.00
    output: 0.00

  # Paid model with the full cache and reasoning split
  "openrouter/anthropic/claude-sonnet-4-6":
    input: 3.00
    output: 15.00
    cache_read: 0.30
    cache_write: 3.75
    reasoning: 15.00

  # Minimal override: cache prices come from the multipliers below
  "openrouter/anthropic/claude-opus-4-7":
    input: 5.00
    output: 25.00

defaults:
  cache_read_multiplier: 0.10    # cache_read = input * 0.10 when not specified
  cache_write_multiplier: 1.25   # cache_write = input * 1.25 when not specified
```

Entries that the plugin writes carry metadata tags that start with an underscore:

| Tag | Meaning |
| --- | --- |
| `_source` | Which source wrote the entry (`openrouter`, `google-ai`, `core-snapshot`). Drives the provider guard described above. |
| `_auto` | Written on auto-fetched entries. Informational: refresh decides manual versus auto from `_meta.auto_models`. |
| `_estimated_price` | The model has no fixed price. It is normalized to `$0.00` and flagged. |
| `_subscription` | A declared `$0` flat-rate or free-tier price, added by hand. |

A refresh never overwrites a hand-written entry. It decides this from the `_meta.auto_models` list in `pricing.yaml`: a model that is not in that list counts as manual.

## Free-tier and subscription models

A model can legitimately cost `$0` for two different reasons, and the plugin keeps both distinct from a lookup miss. `/stats models` labels them in its `Notes` column.

**A `:free` suffix.** Any id that ends in `:free` resolves to `$0` automatically, including the dated ids that gateways send, such as `tencent/hy3-20260706:free`. It is recorded as known-free, so it never triggers the estimated-price warning, and it arms the free-to-paid alert. You do not need a `pricing.yaml` entry.

**A bare native id on a flat subscription.** If a provider serves a model for free under its native id, with no `:free` suffix, declare it with `_subscription: true`. Use the **exact id the gateway records**: a non-dated key does not match a dated id. Check `/stats models` for the recorded id.

```yaml
models:
  qwen3.7-plus:           # Nous Portal's native id, not the OpenRouter qwen/ form
    input: 0.0
    output: 0.0
    _subscription: true   # a declared $0 that survives every OpenRouter refresh
```

`_subscription` is the wrong tool for a model served with a `:free` suffix: the suffix rule already handles it.

**Free-to-paid alert.** When a model that was previously free starts incurring cost, for example when a promotional period ends and the gateway drops the `:free` suffix, the plugin injects a one-time warning into the conversation. For a declared subscription entry, remove it or set the real price so the model is billed correctly again.

## Automatic refresh

The plugin can fetch model prices so that you do not have to maintain `pricing.yaml` by hand.

- **Sources.** The OpenRouter public models API (`https://openrouter.ai/api/v1/models`, no authentication) and a built-in table of Google AI Studio direct prices. Google publishes no pricing API, so that table is maintained in the plugin and updated manually with releases. NVIDIA NIM is covered by built-in seed prices for the Nemotron lineup rather than by a refresh source.
- **Frequency.** At most once per 24 hours, tracked with a sentinel file (`.pricing_refresh`) in the telemetry directory. Delete the sentinel to force a refresh the next time the plugin loads.
- **Trigger.** When the plugin loads, which means at gateway startup, or on demand from the command line (below). A long-running gateway does not refresh until it restarts.
- **Merge.** Manual entries are always preserved, new models are added, and models that were auto-fetched earlier are updated when their price changes. The refresh that runs at plugin load reloads prices in-process. A manual `pricing_refresh.py` run, or `pricing drift --apply`, happens in another process and the gateway caches `pricing.yaml` in memory, so restart the gateway to pick those up.

Run a refresh by hand:

```bash
# Dry run: show what would change
python3 ~/.hermes/plugins/hermes-telemetry/pricing_refresh.py --check

# Apply
python3 ~/.hermes/plugins/hermes-telemetry/pricing_refresh.py

# Verbose
python3 ~/.hermes/plugins/hermes-telemetry/pricing_refresh.py --verbose
```

Example output:

```text
Updated 3 model(s):

  ~ stepfun/step-3.7-flash  (openrouter)
      input: 0.9999 → 0.2000
      output: 9.9999 → 1.1500

  + anthropic/claude-opus-4.8  (openrouter)
      input=5.0000 output=25.0000
```

Where a differing remote price exists for a manual entry, the command lists it under "Manual overrides preserved" so you can decide whether to update it.

### Estimated-price models

Some OpenRouter models have no fixed price, such as `auto` routing and experimental models. The API represents them with negative prices. The plugin normalizes these to `$0.00`, so they do not distort cost calculations, and flags them `_estimated_price: true`. The budget engine notices when spend uses them, and under the default `on_estimated.mode: warn_only` it degrades hard verdicts to soft. See [Budgets](/hermes-telemetry/guides/budgets/#estimated-data-and-budget-degradation).

### Extending with new sources

Add a pricing source by subclassing `PricingSource` in `pricing_refresh.py` and registering it:

```python
class AnthropicSource(PricingSource):
    name = "anthropic"

    def fetch(self) -> dict[str, dict]:
        # Return {model_id: {"input": ..., "output": ..., ...}} in USD per 1M tokens.
        ...

register_source(AnthropicSource)
```

`register_source` appends the class to the `_SOURCES` list in `pricing_refresh.py`. Each refresh cycle fetches every registered source in turn, and the first source to supply a model wins.

## Core pricing snapshots

On every real LLM call the plugin records the tariff that Hermes core resolved for the model, together with its provenance. At most one lookup per model happens every few hours per process. This gives an auditable ground truth to compare `pricing.yaml` against, and it is why costs stay accurate even when `pricing.yaml` is out of date.

Two CLI commands work with that history; both are dry-run by default:

- `hermes-telemetry pricing backfill` seeds snapshots for historical models that never received one, mainly dated model ids.
- `hermes-telemetry pricing drift` compares `pricing.yaml` with the snapshots and can rewrite drifted entries.

See [Standalone CLI](/hermes-telemetry/guides/standalone-cli/#pricing-snapshots) for the options, and [Pricing engine](/hermes-telemetry/internals/pricing-engine/) for the design.
