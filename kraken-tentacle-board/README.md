# board

Free Kraken tentacle. MIT. Do not import `kraken.core`.

Terminal project dashboard. Panels for git, project markers, local AI (Ollama / llama.cpp / official `jev-ai`), and a terminal snapshot. Layout comes from a config file in the **project root**.

```
kraken tentacle add .
kraken run board init
kraken run board open
kraken run board analyze --payload '{"prompt":"safest next commit"}'
```

## Config

Looks for, in order:

1. `<project>/.kraken/board.yaml`
2. `<project>/board.yaml`

`kraken run board init` writes the first one. Example is in `board.yaml` at the tentacle root.

## AI (open source only)

| Backend | How |
|---|---|
| **Ollama** (default) | `POST http://127.0.0.1:11434/api/generate` |
| **llama.cpp** | `POST http://127.0.0.1:8080/completion` |
| **jev-ai** | `kraken run jev-ai infer` if that tentacle is installed |
| **Jev ops** | in-process path get/set/delete/merge (`apply`) |

`KRAKEN_OFFLINE=1` never calls a model. No OpenAI/Anthropic client is bundled.

## Docs

- [docs/USAGE.md](docs/USAGE.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/SECURITY.md](docs/SECURITY.md)
- [docs/DIRECTORY.md](docs/DIRECTORY.md)
