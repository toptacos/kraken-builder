# Using board

```bash
cd /path/to/your/app
kraken tentacle add /path/to/kraken-tentacle-board
kraken run board init
kraken run board open
```

`open` returns a boxed terminal frame in `result.frame` plus structured `panels`. Kraken’s invoke is one JSON line, so this is a snapshot dashboard, not a resident PTY multiplexer. Re-run `open` or bind it to a watch tick.

## Actions

| Action | Payload | Result |
|---|---|---|
| `init` | `root` | writes `.kraken/board.yaml` |
| `open` / `layout` | `root` | panels + ASCII frame |
| `snapshot` / `status` | `root` | panels only |
| `repo` | `root` | branch, sha, dirty files |
| `project` | `root` | markers (go.mod, package.json, …) |
| `ai` | `prompt` | local infer or offline fixture |
| `analyze` | `prompt` | infer over repo+project snapshot |
| `apply` | `file`, `operations` | Jev path edits inside the project |
| `finish` | `raw`, `patch` | sucker merge |

Project root is `payload.root`, else `KRAKEN_BOARD_ROOT`, else cwd, then walk up for `.kraken/board.yaml` or `.git`.
