# Hello world tentacles

See `examples/tentacles/hello-world/README.md`.

```bash
bash examples/tentacles/hello-world/build.sh
kraken tentacle add examples/tentacles/hello-world/python
kraken run hello-py hello --payload '{"name":"kraken"}'
```

Integration is the contract only. After `tentacle add`, `kraken run <name> hello` works the same for every language.

Bring your own compiler: docs/RUNTIME.md and examples/tentacles/runtime.
