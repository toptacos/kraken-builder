# Platforms and when Docker is used

Core never compiles a tentacle and never starts Docker by itself.

A tentacle declares what it already built and what CI tested:

```yaml
needs_docker: false
platforms:
  linux-amd64: { tested: true, binary: dist/linux-amd64 }
  linux-arm64: { tested: true, binary: dist/linux-arm64 }
  darwin-arm64: { tested: false }
```

`kraken list` prints `platforms` and `needs_docker`. The catalog can copy the same fields after CI posts results to `/api/kraken/catalog`.

| Tentacle | Docker? |
|---|---|
| hello-*, filesort, pi-net, vault, store, hotreload | no |
| runtime build/invoke | only if you asked to compile inside an image |
| docker-env up, sites up | yes, isolated `kraken_*` network, 127.0.0.1 publishes |

Write in any language. Ship the smallest binary your toolchain produces. Missing platform → flag `tested: false`, do not pretend it runs.
