# Kraken CLI

**One binary. Many tentacles.** Local-first CLI plugin runner.

JSON in → policy → exec → JSON out.

[![License: MIT](https://img.shields.io/badge/License-MIT-2FD0C6.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-0B1220.svg)](https://www.python.org/downloads/)

## Open source

Kraken is **MIT licensed, free, and self-hosted.** The core CLI, every arm in
this repo, and the static frontends are open. Fork it, read it, run it on a Pi
with no account and no network. The whole contract is a JSON envelope on
stdin/stdout — there is nothing to reverse and nothing to call home to.

```
git clone https://github.com/toptacos/kraken-builder
cd kraken-builder && sh ./install.sh
kraken demo
```

Not `pip install -e .`. An editable install freezes the absolute path of your
checkout into an import finder, so moving or renaming the directory leaves a
`kraken` on PATH that fails with `ModuleNotFoundError: No module named
'kraken'` while `pip show` still reports a healthy install. The installer writes
a launcher that re-resolves the source on every run instead.
See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

| Open (MIT) | Metered, not secret |
|---|---|
| Core CLI + `kraken up` | Kraken seats for premium arms |
| Every arm in this repo | Hub Pro storage / quota |
| `sites/*.yaml` site config | Featured restaurant listing |
| The JSON v1 contract | API quota on `api.topta.co` |

Two rules the project holds to: **there is no closed paid arm** — a premium
action is a *license check* on an MIT arm, never a hidden binary — and
**nothing in `$KRAKEN_HOME` is ever uploaded**. Sealed secrets stay sealed, and
`keeps` has no code path that writes to `api.topta.co`.

Optional billing lives in `kraken.billing` and is **not required to run
anything**. `KRAKEN_OFFLINE=1` is the default posture for telemetry.

![Kraken tentacle-K](https://kraken.topta.co/og-1200x630.jpg)

```
curl -fsSL https://kraken.topta.co/install.sh | sh
kraken demo
```

That install puts `kraken` and `k` on PATH, installs vanilla tentacles, and prints one geo lookup JSON. First success in under 60s.

```
kraken doctor
kraken run filesort scan --payload '{"path":"."}'
kraken grant expose
kraken run expose plan --payload '{"host":"panel.kraken.localhost"}'
```

Moving or renaming your checkout afterwards is one line, not a reinstall:

```bash
KRAKEN_SRC="$HOME/new/path/to/kraken-builder" sh ./install.sh
```

`kraken doctor` reports which source tree is actually running, its git
revision, and whether a competing `kraken` is on PATH — the three facts that
explain `ModuleNotFoundError`.

## Configuration

Three scopes — system (`/etc/kraken/config.yaml`), user
(`$KRAKEN_HOME/.kraken/config.yaml`), and project (`.kraken/config.yaml`
walking up from the cwd). Later scopes win per key; project beats user, which
is why a project config belongs in version control.

```bash
kraken config list          # every setting, marked * when not the default
kraken config explain KEY   # which file won, and what it overrode
kraken config validate      # check every file, exit 2 on problems
kraken config init          # write a commented example
```

Thirteen settings, all typed and validated. Committed examples live in
`examples/config/`, generated from the same function `config init` uses.
Full reference: [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## `kraken up` — the shared network

Core owns one Docker network, named `kraken`. Arms only *plan*; core runs it.
`berth` turns a `project.yaml` into a compose plan, and `kraken up` reconciles
that plan with core's network policy.

```
kraken run berth up --payload '{"yaml":"name: demo\nservices:\n  api:\n    image: nginx:alpine"}'
kraken up                # plan only — prints the plan, starts nothing
kraken up --start        # docker network create kraken && docker compose up -d
```

`kraken up` is plan-only unless you pass `--start`, so it is safe to run in a
script or on a laptop you did not mean to change. It refuses to start when
`KRAKEN_OFFLINE=1` is set, and it reports `network_mismatch` if a service in
the plan is attached to a different network than core's — the failure mode
where a container silently never joins.

> Not Payward, not `api.kraken.com`. This is a TopTaco product on
> `topta.co`. Core never imports an arm's source.

## Public input

| Channel | Use |
|---------|-----|
| [Discussions · install](https://github.com/toptacos/kraken-builder/discussions) | Install, PATH, python wrapper |
| [Discussions · tentacle](https://github.com/toptacos/kraken-builder/discussions) | Write an arm. Paste tentacle.yaml, no keys |
| [Discussions · showcase](https://github.com/toptacos/kraken-builder/discussions) | Homelab / Pi / consultant jobs |
| [Issues](https://github.com/toptacos/kraken-builder/issues) | Bugs with a repro. Never paste `~/.kraken/keys` |
| [Register](https://kraken.topta.co/register) | List a tentacle for catalog review |

Template: [`examples/tentacles/_template/`](examples/tentacles/_template/). Contract: JSON on stdin, JSON on stdout. Core never imports your source.

## Links

Site: https://kraken.topta.co  
Install: https://kraken.topta.co/cli  
Use cases: https://kraken.topta.co/use-cases  
Changelog: https://kraken.topta.co/changelog  
Pricing (optional, only if you want a premium arm): https://kraken.topta.co/pricing — docs/BILLING.md  
API: https://api.topta.co

Repos: [kraken-builder](https://github.com/toptacos/kraken-builder) · [tentacles](https://github.com/toptacos/kraken-tentacles) · [suckers](https://github.com/toptacos/kraken-suckers)

Homebrew:

```
brew install toptacos/kraken/kraken-cli
```

Optional billing extra (same tree, not required — everything below runs without it):

```
pip install 'kraken-cli[billing]'
```

Topics: `cli` · `homelab` · `raspberry-pi` · `plugins` · `local-first` · `self-hosted` · `open-source`

## Contributing

Issues and PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) and
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). An arm is a folder with a
`tentacle.yaml`, a `handler.sh`, and a `tests/` dir; the contract test is the
whole review surface. Never commit `~/.kraken`, `keys/`, or `licenses.json`.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 McAchran Consulting LLC.

A TopTaco product on topta.co. Brand: tentacle-K, ink `#0B1220`, teal `#2FD0C6`, foam `#E7F6F6`, gold `#e7c56a`.

<!-- SPONSORS:BEGIN -->

## Sponsoring

Kraken is MIT: the CLI, every arm, and the JSON contract. Sponsorship pays for maintenance and releases, never for features held back.

[![Sponsor](https://topta.co/donate)](https://topta.co/donate) [![What your money funds](https://topta.co/projects)](https://topta.co/projects)

| Rail | What it funds |
| --- | --- |
| [Card (Stripe)](https://topta.co/donate) | Hosting, the API, and release time. |
| [Impact Radius](https://impact.topta.co) | The open-source projects this depends on, paid directly. We take no margin. |
| [Affiliate](https://topta.co/products) | Discgolf gear and delivery commissions. Never a listing fee, never a paywall. |

Prefer not to donate? Issues, discussions and pull requests are the most useful thing you can send.

<!-- SPONSORS:END -->
