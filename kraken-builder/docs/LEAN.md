# Lean binary policy

Ship the smallest `kraken` that still:

1. Merges `.kraken` config
2. Resolves a name to a binary
3. Writes one JSON request to stdin
4. Reads one JSON response
5. Runs suckers/hooks without re-entry
6. Enforces license + file modes + loopback policy when a tentacle *asks* for Docker

Do **not** put in core: compilers, language runtimes beyond what the wrapper needs, model weights, Compose, VPN daemons, note editors.

```
kraken-core          → one binary
  tentacle A.go      → one binary
  tentacle B.rs      → one binary
  sucker = hook row  → points at A or B
```

Measure later with `ls -lh` / `upx` on the release artifacts — not by vendoring toolchains.
