# Notes, tunnel, LLM

```
kraken tentacle add examples/tentacles/notes
kraken run notes put --payload '{"name":"jump","body":"box-a"}'
kraken run notes search --payload '{"q":"box"}'
```

Notes live in `~/.kraken/data/notes/*.md` mode 0600. Pair with `vault` if you want ciphertext instead of markdown.

```
kraken run tunnel plan --payload '{"host":"10.0.0.4","key":"~/.ssh/id_ed25519","local_port":18080}'
```

Local forward only (`127.0.0.1`). You must already have the key. Kraken does not open a VPN for you.

```
kraken run llm plan --payload '{"enabled":false,"ingest":["notes","media"]}'
```

Plans `docker run` on `kraken_llm` with ingest mounts `:ro` and publish `127.0.0.1:11434`. No weights in the repo.
