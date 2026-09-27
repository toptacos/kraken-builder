# ink

Non-negotiable. Brand night `#0B1220`, teal `#2FD0C6`, foam `#E7F6F6`, gold `#e7c56a`.

## Contract

Protocol **v1**. JSON stdin, one JSON stdout, process exit **0**.

```json
{"v":1,"id":null,"action":"ping","payload":{}}
{"v":1,"id":null,"ok":true,"result":{"arm":"<name>","version":"0.1.0","protocol":1}}
{"v":1,"id":null,"ok":false,"error":{"code":"unknown_action","message":"…"}}
```

No `kraken.core` import. Core never imports your source.

## Where data may live

| Place | Holds |
|---|---|
| `$KRAKEN_HOME/.kraken/data/<name>/` | arm state (default) |
| project `.kraken/data/<name>/` | optional project scope |
| `payload.dir` / `KRAKEN_<NAME>_DIR` | explicit |
| `~/.kraken/keys/licenses.json` | **licenses only** |
| `POST /api/kraken/catalog/register` | **tentacle metadata only** |

## Security

- Loopback only for local HTTP (Ollama, llama.cpp, bookmarklet).
- No path escape out of project/data dir.
- Tokens live in their own `0600` file, never in export or catalog.
- Marks store is AES-GCM (`store.bin`) unless `KRAKEN_MARKS_PLAIN=1`.
- Store dirs cannot be `keys/`, `licenses.json`, catalog, or `*.topta.co`.
- board `apply` needs a grant file or `KRAKEN_BOARD_APPLY=1`.
- Default-deny exec, live browse, listen-as-daemon.
- `KRAKEN_OFFLINE=1` skips model and live network.
- Multi-device marks use `merge` (per-id LWW + tag union + tombstones), not whole-file LWW.

## License and billing

- `license: free` → `assert_licensed` is a no-op.
- Premium needs a `k_` key on disk. Remote verify only if `KRAKEN_LICENSE_REMOTE=1`.
- Billing checkout is a **501** stub. Do not set `KRAKEN_BILLING=1` in CI.

## AI

Jev path ops + Ollama / llama.cpp on `127.0.0.1`. `learn` is a prompt, not training. No OpenAI/Anthropic SDK.
