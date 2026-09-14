# Why Kraken

Audio for this page lives in `website/media/voice/` (`intro`, `pitch`, `why`, `why-local`, `why-any-language`, `why-not-saas`, `why-compose`, `why-privacy`, `why-indie`, `why-ops`). Kit copy: `brand/voice/`. Index: `docs/VOICE_KIT.md`.

## One sentence

A single local binary that loads tools (tentacles) from any repo, runs them as JSON in/out, and can gate premium ones with a key.

## Compared to what people already have

| They have | What breaks | What Kraken does |
|---|---|---|
| A `scripts/` folder | No contract, no deps, no license | `tentacle.yaml` + invoke |
| n8n / Zapier | Cloud, vendor lock, your data leaves | Same idea, process stays on the box |
| “just write a CLI” | Every tool reinvents flags and config | Core owns config, queue, hooks |
| Docker compose of five services | Heavy for a lookup | One file, optional compose |

## Example: weather for a city from an IP

1. `geo` tentacle (free) returns `{ "city": "Kernersville" }`.
2. Workflow interpolates `$geo.city` into `weather-pro` (licensed).
3. `weather-pro` returns the forecast JSON.
4. Core notifies or writes the file. You never wrote a new orchestrator.

Commands:

```
kraken tentacle add examples/tentacles/geo
kraken tentacle add examples/tentacles/weather-pro
kraken license set weather-pro YOUR_KEY
kraken workflow run examples/workflows/geo-then-weather.yaml
```

## Example: sell an arm without forking core

Ship `weather-pro` as its own repo. User installs Kraken once. They add your tentacle path or catalog slug. Your handler only implements the JSON contract. Core handles keys via `api.topta.co` or a local licenses file.

Personas and jobs: `docs/USE_CASES.md`, `website/use-cases.html`.

## What we do not claim

- Not a replacement for Kubernetes.
- Not an LLM. Tentacles can call models; core does not require one.
- Not the Kraken exchange.
