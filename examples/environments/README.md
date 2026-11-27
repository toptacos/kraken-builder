# Environment workstations

Local developer toolkit. Kraken plans compose. mycelium (optional) runs the
shift. This is not production serving.

| Path | What it is |
|---|---|
| [compose/](compose/) | Plan-only nginx + redis on loopback. `kraken init --env` copies it. |

Full orchestrated recipe (isolated homes, mycelium workflow):

https://github.com/toptacos/mycelium/tree/main/examples/04-kraken-compose

```bash
kraken init --env
kraken up --file compose.yaml
```

Do not pass `--start` unless you mean to create containers. Suggested prompt:
"Plan my local stack (no containers)".
