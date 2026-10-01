# Changelog

## 0.3.1 — 2026-10-01

### Fixed
- **`ModuleNotFoundError: No module named 'kraken'` after moving the checkout.**
  `pip install -e .` writes a pip console script with two absolute paths frozen
  into it: the interpreter in the shebang, and the checkout location in
  `__editable___kraken_cli_*.py`. Rename or move the repo and the interpreter
  still runs, the `dist-info` still reports a healthy install, and the import
  fails — with an error that names neither a path nor the finder, so it reads
  as "not installed". `scripts/kraken` now re-resolves its source tree on every
  invocation, validating each candidate for `kraken/core/cli.py` instead of
  trusting a recorded path, and prints the fix instead of a traceback when no
  candidate resolves.
- **`install.sh` baked the checkout path into the wrapper it wrote.** It now
  installs `scripts/kraken` and records the chosen tree in
  `$HOME/.kraken/source`, so moving a checkout is a one-line repair. The
  installer also warns when a `kraken` earlier on `PATH` would shadow the
  launcher — the other half of this failure, since `/usr/local/bin` usually
  precedes `~/.local/bin`.
- **The install guard tested the wrong file.** `install.sh` accepted any tree
  containing `kraken/__main__.py`, which passes for a checkout that has lost
  `kraken/core`. It now checks the module the console entry actually imports.

### Added
- **`kraken doctor` reports the install.** New `install.*` checks name the
  source tree that is running, its git revision and dirty state, any competing
  `kraken_cli-*.dist-info` on `sys.path`, whether `$HOME/.kraken/source` agrees
  with the tree that ran, and where `kraken` and `k` resolve on `PATH`. Only
  `install.source`, `install.pip_kraken_cli`, and `install.on_path` can fail —
  a non-git tree is reported, not penalised, so the checks stay meaningful for
  a Homebrew or pip install.
- `docs/TROUBLESHOOTING.md` — `ModuleNotFoundError`, source-tree resolution,
  shadowing, two-clone drift, and a dangling `.git` file, each with the cause
  before the fix.
- `tests/test_install_wrapper.py` — 11 tests covering pointer resolution,
  `KRAKEN_SRC` precedence, the dead-source message, and the install guard.

### Fixed
- **`timeout_sec` in tentacle.yaml was dead config.** `invoke_binary` defaulted
  to 30 and no caller passed anything, so every arm silently got 30s. An arm
  declaring 120s could never spend its budget: core killed it first, and the
  handler had no chance to report anything but a stack trace. The manifest
  value is now read and clamped to `MAX_TIMEOUT_SEC`, so an arm may ask for
  less than the default but never for an unbounded run.
- **berth and ledger wrote a correct error body and then exited 1.**
  `docs/CONTRACT.md` is explicit that a non-zero exit is a transport failure
  and an application failure is `"ok": false` with exit 0. Both did the
  opposite, so core discarded the body and raised — asking berth why it failed
  produced a `RuntimeError` and a stack trace instead of "no project config".
  Both now exit 0. A scan of all 61 handlers found these two and no others.
- **`compile-c` imported `kraken.core` and called `run_named()` in-process**,
  which `docs/CONTRACT.md` forbids outright ("It must not depend on kraken-core
  source"). It also located the runner with `parents[3]`, which resolves
  against wherever the tentacle happens to be installed, so `runtime` was
  looked up under the wrong root. It now delegates over the contract, and a
  missing or failing dependency is an answer rather than a traceback.
- **`jev-ai learn` could hang past core's kill time.** `_ollama_infer` allowed
  120s against core's 30s, and `subprocess.TimeoutExpired` was caught by
  neither `FileNotFoundError` nor `RuntimeError`, so a timeout escaped as a
  traceback. Its deadline is now under core's, and a timeout is reported as
  `ok: false`. It declares `timeout_sec: 180` for the same reason compile-c
  does: a tentacle that shells out needs more wall clock than one that does not.
- **`store import-pack` and `vault import-bundle` crashed on a missing
  argument.** `Path(p.get("pack") or "")` is `.`, so omitting the path made
  `read_text()` raise `IsADirectoryError`. Both now say what is missing.

### Added
- **`tests/test_handler_contract.py`** — two properties across every tentacle
  and example arm. First, a handler that writes `"ok": false` must exit 0; the
  exit code must not contradict the body. Second, every declared action must
  answer with one JSON object rather than a traceback. Plus a check that a
  handler's own subprocess deadline stays under the budget core enforces, which
  is what caught the `jev-ai` and `compile-c` overshoots.
- **`scripts/contract_sweep.py`** — installs every tentacle into a throwaway
  `KRAKEN_HOME` and invokes every declared action through `kraken run`, the
  path a user actually takes. The per-repo suites call a handler directly and
  read stdout, which is why none of this was visible: 195 actions across 51
  tentacles now pass with zero transport failures.

### Known
- 17 actions report a refusal as `"ok": false` with the reason at
  `result.error` rather than top-level `error`. Every one carries a
  machine-readable reason, so this is a shape difference between example arms,
  not a defect. `contract.py`'s `envelope()`/`unwrap()` (`{kind, value, meta}`)
  remain dead code — nothing in core calls them and no handler imports them —
  which is why `kind` is not asserted by the contract tests.
- `KRAKEN_HOME` is the home directory and `.kraken` is appended to it, so
  pointing it at `~/.kraken` silently nests everything one level deeper
  (`~/.kraken/.kraken/tentacles/…`) with no complaint. The resolver now warns
  once when `KRAKEN_HOME` is itself named `.kraken`. This is not hypothetical:
  the contract sweep's own harness made exactly that mistake before the guard
  existed.
- Several arms configure hooks (`keeps` → `redact-log`, `compile-c` →
  `compile-stamp`, `compile-tag`) for arms that are not installed by default,
  so `_hooks` reports `skipped: true` on every run.


## 0.3.0 — 2026-09-28

### Security
- **`allow` grants were read by grepping the file text.** `read_allow` looked
  for the literal string `"expose: true"` anywhere in config.yaml, so a line
  reading `# expose: true` granted the capability. In a default-deny system
  that is the worst possible failure: an operator writing down "I do not want
  this" silently enabled it. The resolver parses YAML now, honours all three
  scopes so a project can deny what a user allowed, and `kraken grant` writes
  through a YAML round-trip so it cannot corrupt the file.
- `kraken config validate` refuses `docker.public: true`.

### Added
- **A real configuration layer.** `kraken/core/config_schema.py` describes all
  thirteen settings — type, default, allowed scopes, and what it does. It is the
  single source for the docs, the examples, and the tests, so a setting cannot
  exist undocumented or untested.
- **`kraken config`** with `list`, `get`, `explain`, `path`, `validate`, and
  `init --scope`. `list` marks anything not at its default and names the scope
  that set it; `explain` shows every layer for a key and which one won.
- Committed examples in `examples/config/` for all three scopes, generated from
  the same function `config init` writes, with a test asserting they are
  byte-identical so they cannot drift.
- `docs/CONFIGURATION.md`.
- `tests/test_config.py` (64 tests) walks the schema rather than hand-picking
  keys, so a new setting without coverage fails the suite.

### Fixed
- **`data_dir` and `notify` were decorative.** Both were written into every
  user's config by `kraken init` and read by nothing. `data_dir` is now
  honoured by the arms, `kraken up`, and `kraken doctor`; `notify.channels`
  now selects which channels fire, with the environment still supplying each
  channel's credentials.
- `notify: none` meant "fall back to stdout" rather than "no channels".
- `kraken config` printed human text on failure even when piped. Output is now
  one JSON object on stdout whenever it is not a terminal, success or failure.
- `load_config` starts from the schema defaults rather than three hardcoded
  keys, so a partial file resolves to a complete config. Unknown keys still
  pass through for forward compatibility.

## 0.2.0 — 2026-09-27

### Added
- **`kraken up`** — the shared-network verb. Reads the compose plan `berth`
  wrote, reconciles its network against core's policy, and prints the result.
  Plan-only unless `--start` is passed, so it is safe in a script. See
  `docs/UP.md`.
  - Refuses to start under `KRAKEN_OFFLINE=1` (error code `offline`).
  - Refuses to start with no `docker` on `PATH` (error code `no_docker`).
  - Reports `network_mismatch` and names the offending services when a
    container in the plan is attached to a different network than core's — the
    failure mode where a service silently never joins.
  - Accepts an inline `compose`, a `file` path, or falls back to whichever
    planning arm wrote a plan (`berth`, `board`, `inlet`).
- `docs/OPEN-SOURCE.md` — what is MIT, what is metered, and the five
  integrations this project refuses, each with its local substitute.
- `docs/UP.md` — the `kraken up` contract.
- `tests/test_up_verb.py` (15 tests), `tests/test_license_contract.py` (8).

### Changed
- **The shared network is the bare name `kraken`.** Core previously normalized
  every name into `kraken_*`, which meant `kraken` became `kraken_kraken` and
  could never match the `kraken` network that `berth`, `sites/kraken.yaml`,
  and the docs all declare. Arbitrary labels are still namespaced
  (`lab` → `kraken_lab`), so two projects still cannot collide.
- `kraken/core/network.py` exports `normalize_network_name()` and
  `SHARED_NETWORK` instead of the private `_normalize_name()`.
- README restructured around an explicit open-source / metered split, plus a
  `kraken up` section. MIT badge, trove classifiers, and an `open-source`
  keyword added to `pyproject.toml`.
- `kraken tentacle add` progress moved from stdout to stderr, so install output
  no longer breaks the "stdout is one JSON object" contract.
- A `402` from the license API is now reported as an actionable message naming
  the seat and the pricing page, rather than a raw status line. A `5xx` still
  reads as a broken API, not a sales problem.

### Fixed
- **`KRAKEN_OFFLINE=1` no longer skips the remote `config_url` fetch.** The
  network resolver reached out regardless, which contradicted the documented
  offline-first posture. It now reports `fetch_skipped: offline` and keeps the
  local config.
- The polyglot example test pointed at flat `polyglot/echo.sh` paths after the
  fixtures were reorganised into per-language directories.

## 0.1.1 — 2026-09-14

### Product
- `kraken demo` runs vanilla `geo lookup` so first JSON lands in under 60s.
- `install.sh` runs `init` + `vanilla` + `demo` after putting `kraken`/`k` on PATH.
- `kraken doctor` and `kraken self plan` print `next` actions: geo, filesort, grant expose.
- `geo` fixture returns `city` + `ip` for 1.1.1.1 / 8.8.8.8 (offline, no network).

### Site
- Live SPA pages: use-cases, changelog, blog posts, register, long-form geo/filesort.
- Playground demos the geo contract with a city result (still does not exec on the host).
- Prerender script writes crawlable HTML for home, docs, catalog, blog.
- Optional `kraken.billing` package: local keys, hooks, verbose logs. MIT core does not require it.

### Distribution
- Homebrew formula at `Formula/kraken-cli.rb` (tap: toptacos/kraken).
- GitHub release workflow body includes install + CHANGELOG excerpt.
- Discussions templates: install, write-a-tentacle, showcase.

Brand: tentacle-K, ink `#0B1220`, teal `#2FD0C6`.
