# spawn

Spawn an arm. JSON in → policy → JSON out. Do not import `kraken.core`.

```
kraken tentacle add <source>
kraken run <name> ping
```

## The three words

- **spawn** — this kit and the act of creating the tentacle.
- **ink** — the contract and security rules that do not move. See [INK.md](INK.md).
- **keel** — the ordered checklist you lay first. See [KEEL.md](KEEL.md).

## Runtime

| Kind | When | Example |
|---|---|---|
| Go `CGO_ENABLED=0` + `handler.sh` | portable binary | watch, marks |
| Python `handler.py` | Jev, Ollama, local tools | jev-ai, board |

Command users want: `kraken <name> …` with fallback `kraken run <name> <action>`.

## After spawn

1. Lay the keel (`KEEL.md`).
2. Stay inside the ink (`INK.md`).
3. Tag `v0.1.0`, set `schemas/catalog.json` `source`, `POST /api/kraken/catalog/register`.
4. Site page `/catalog/tentacles/<name>`. Copy: `kraken tentacle add <url>` then `kraken run <name> ping`.
