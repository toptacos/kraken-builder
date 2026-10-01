# reef

One body. Many arms. A reef, not a vendor.

The catalog may list the reef. It does not hold user data.

Arms built in this workspace:

| Tentacle | Runtime | Job |
|---|---|---|
| watch | Go | tasks, notify, browse snapshot |
| marks | Go | local bookmarks + loopback bookmarklet |
| board | Python | project dashboard + local Jev/Ollama |
| keeps | Go | sealed secrets (AES-GCM) |
| card | PHP | HTML card from JSON |
| pulse | vanilla JS (Node, no deps) | validate / wrap v1 envelopes |
| facts | bash | host snapshot for hooks |
| spawn | docs | spawn · ink · keel · reef |
| twin | Python | exact duplicate scan including archives |
| inlet | Python | loopback host UI + roster |
| taco | Python | premium local kudos ledger |
| berth | Python | project.yaml → shared `kraken` docker network plan |

Brand line: **reef**. Palette: ink `#0B1220` teal `#2FD0C6` foam `#E7F6F6` gold `#e7c56a`.
Marketing page: `kraken-reef/branding/index.html`

## Ideas not built

- **drift** — diff two sealed keeps/marks stores without revealing values
- **wake** — cron-shaped wrapper that only calls `kraken run` (no daemon of its own)
- **harbor** — pack a project `.kraken/` into a tarball and verify checksums
- **reef** — list installed tentacles from disk, not catalog
- **inkwell** — signed receipt for `catalog/register` payloads you are about to send
- **eddy** — sample last N hook envelopes, redact, write a local report
- **barnacle** — attach a small sidecar note file to a git commit without touching remotes
- **sonde** — probe loopback Ollama/llama.cpp and print board-compatible status
- **ledger** — append-only JSONL of `kraken run` results (no secrets)
- **wax** — age/minisign wrapper around keeps export
- **shoal** — run a workflow YAML with $ref using only bash
- **mirage** — fake browser snapshot for watch tests (fixture server on 127.0.0.1)
- **quay** — install a tentacle from a local zip, refuse http
- **brine** — backup `$KRAKEN_HOME/.kraken/data` excluding `keys/`
- **knot** — pin tentacle.yaml versions and verify SHA256SUMS
- **lantern** — one-page local catalog renderer (static HTML, listed=false respected)
- **trawl** — ripgrep-shaped search over project `.kraken` only
- **mooring** — grant files (apply/listen/browse) as first-class tentacle
- **spawn-cli** — scaffold a new arm from KEEL.md
- **echo** — official-style contract dummy in Rust/Zig if CGO-free is the point

Do not build a cloud sync tentacle that writes bookmarks or secrets to `api.topta.co`.

## Implemented this pass

reef, brine, ledger, sonde, quay, knot, mooring, harbor, trawl, drift, wake, lantern.

CI matrix is ubuntu / macos / windows via GitHub Actions. This host proved the Linux path. Cross-OS is the same Python handler + protocol tests, not a device farm.

## clip
Local Facebook/share URL index. Does not download the reel.

## wax
minisign/age wrapper; HMAC fixture when binaries missing.

## twin
Exact-duplicate scan over declared drives, including archive members.

## inlet
Loopback control plane. Optional cloudflared. No remote shell.

## taco
Premium gamification ledger. Inbound events only.
