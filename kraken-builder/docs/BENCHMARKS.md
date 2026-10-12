# Benchmarks

How Kraken is measured, against what, and what the numbers say. Every claim
here comes from a script in this repo — run them yourself rather than
trusting a table.

| Script | Measures |
|---|---|
| `scripts/bench_contract.py` | The transport: interpreter floor, envelope encode/decode by payload size, `invoke_binary` round trip |
| `scripts/bench_alternatives.py` | Wall time, peak RSS, and installed size against the alternatives (make, go-task, node, bash) |

## Method

Two properties of a shared mac make naive benchmarks lie, so both scripts
are built around them.

- **Load is not constant.** A box running an LLM or an editor rebuild swings
  5-10x between minutes. `bench_alternatives.py` therefore measures every
  tool once per iteration, round-robin, and reports the **minimum**: all
  tools share a spike inside one iteration, so the min is the cleanest
  moment each tool had, not the luckiest. `bench_contract.py` reports best
  of 3 passes and interleaves its floor measurement with the real call so
  drift cancels out of the delta.
- **RSS has to come from the direct child.** `RUSAGE_CHILDREN` is a
  high-water mark for the whole process and would blame the first big child
  for everyone after it. `run_once()` uses `os.fork` + `os.wait4` so each
  number belongs to the command above it.

Kraken's `run` is measured from a neutral cwd, **without** this repo's
project-scope config — a user's box has no demo hooks registered.

## Results (macOS, Apple Silicon, python 3.14)

Recorded on a box under load (load average 143). Wall times are inflated by
that for every tool; the *ranking* and the *ratios* are the meaningful part,
and RSS is unaffected by load.

| command | min (ms) | peak RSS (MB) |
|---|---|---|
| `kraken --help` | 142.7 | 16.2 |
| `kraken run <tentacle> ping` | 330.1 | 19.2 |
| `make ping` | 28.5 | 1.0 |
| `node -e echo` | 86.6 | 30.3 |
| `bash -c echo` | 16.8 | 2.6 |

Installed size: **0.4 MB** kraken source, **0.5 MB** as Homebrew installs it,
against a single dependency (python >= 3.11 + pyyaml). A tentacle brings its
own runtime; adding fifty of them adds nothing to that list.

## Where the time goes

One `invoke_binary` is one interpreter start. `bench_contract.py` splits it:

- interpreter floor (`python -c pass`): the dominant term, ~50-60 ms of a
  ~60-70 ms round trip on an idle box
- contract core (env prep, encode, argv, decode): the envelope micros —
  sub-millisecond at 1 KB, ~1 ms at 64 KB, ~11 ms at 1 MB
- the handler's own body

The honest reading: **the spawn is the cost, not Kraken.** Against `make`,
which is a 0.1 MB binary, Kraken is an order of magnitude slower per invoke
and will stay slower — a Python CLI cannot out-run C at process start. What
was in Kraken's control has been taken:

## What was optimized (2026-10)

| Change | Before | After |
|---|---|---|
| `import kraken.core.cli` cost | 372.6 ms | 61.8 ms |
| YAML parses per `kraken run` (profile) | 14 | ~4 |
| `_subprocess_env` fast path (root already importable) | 113 µs | 0.7 µs |
| Homebrew libexec footprint | 33.3 MB | 0.5 MB |

- `kraken/core/__init__.py` and `cli.py` resolve their public names lazily
  (PEP 562). Before, `kraken --help` paid for urllib (via license), yaml (via
  loader), and the workflow thread pool (via concurrent.futures) — none of
  which a help screen touches. `monkeypatch.setattr("kraken.core.cli.X")`
  still works: `_resolve()` skips names already bound, which is exactly what
  a patch does.
- `license.py`, `notify.py`, `workflow.py`, `loader.py` import their heavy
  dependencies (urllib, concurrent.futures, yaml) inside the functions that
  call them.
- `config.load_yaml` caches by (path, mtime_ns, size). One `kraken run` used
  to parse the same three-scope config chain three or four times over.
- The formula ships `examples/tentacles` but drops `examples/hello-world`'s
  vendored rust/go toolchains (16 MB of demo sources a git checkout provides).

## What Kraken is faster at

Raw invoke speed is not the bet, and claiming it against `make` would be
false advertising. The bet is *capability per unit of footprint*:

- **vs node:** a JS tentacle's floor is node's own startup (86.6 ms here).
  Kraken's CLI boots the same Python it would anyway and spawns the tentacle
  in its own runtime — py, sh, js, php, rb, pl, go, osascript — from one
  0.4 MB core with one dependency.
- **vs n8n / Zapier:** those products are a server plus a hosted connector
  catalog. Kraken is 0.4 MB, binds loopback by default, and has no call-home
  path (`KRAKEN_OFFLINE=1` is the default posture; only billing/license
  verification can talk out, and only when a user opts in).
- **Parallel work:** `kraken workflow` fans out across tentacles on a thread
  pool, so N tentacles cost one CLI process plus N spawns — not N CLIs.

## Reproduce

```bash
python3 scripts/bench_contract.py            # transport, ~2 min
python3 scripts/bench_alternatives.py        # vs the field, ~5 min
python3 scripts/bench_alternatives.py --runs 8
```

Prefer an idle box. If load average is in the dozens, the absolute numbers
are junk for every tool and only the ratios survive — the round-robin design
keeps the comparison fair, not the clock honest.
