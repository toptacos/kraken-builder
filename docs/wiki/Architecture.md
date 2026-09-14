# Architecture

```
kraken-builder/
  kraken/core/     # loader, registry, queue, cli
  arms/<name>/     # arm.yaml + handler
  tests/
  docs/
```

Core responsibilities: find manifests, register arms, enqueue jobs, invoke entrypoints **or tentacle binaries**.

Two plugin kinds — see `docs/PLUGINS.md`:

- **Arms** (`arms/*/arm.yaml`) — imported in-process.
- **Tentacles** (`tentacle.yaml` + binary) — exec, JSON stdin/stdout.

Not core: HTTP servers, cloud APIs, mail, payments, persistent brokers. Those are tentacles (or thin arms while prototyping).

Reload: process restart or image rebuild. Slice 1 does not hot-reload.

Queue: in-memory FIFO. A Redis/SQS arm can replace `WorkflowQueue` later without changing manifests.

Executable: `Dockerfile` runs `kraken`. Multi-arch PyInstaller/Go wrapper is documented in `docs/dev/DOCKER_BUILD.md`, not shipped as signed binaries yet.
