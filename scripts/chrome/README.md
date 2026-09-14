# Chrome Default profile (matt@topta.co)

All Kraken launch automation uses the **Default** Chrome profile (`matt@topta.co`).
Do not create accounts. Do not inject JS to sign up. Open, extract, screenshot, leave.

## Layout

| File | Role |
|------|------|
| `open-profile.sh` | Launch Chrome Default with a URL |
| `inject.js` | Page probes (title, HSTS-unrelated DOM, Search Console form) |
| `chrome-ops.applescript` | Open tab, run JS, return JSON |
| `capture.sh` | Screenshots + optional timed screen recording |
| `run-launch.sh` | Full launch pass: site, GitHub, Search Console, X drafts |
| `media/` | Captured PNG/MOV from the last run |

## Env

```
KRAKEN_CHROME_PROFILE=Default
KRAKEN_CHROME=1
```

## Last run (2026-09-14)

Probe JSON in `media/launch-log.txt`:

- kraken.topta.co — MIT true, exchange false, H1 present
- /cli — Install Kraken CLI
- /docs/tentacle — Create a tentacle
- GitHub — MIT plugin runner
- Search Console — **not verified** (`Oops, you don't have access to this property`)

`screencapture` needs a logged-in Mac display. This agent session had no GUI; branded still is `media/og-still.jpg`. On your laptop:

```
KRAKEN_RECORD=1 sh scripts/chrome/capture.sh
```

## Safety

- JS is read-only except clicking an already-visible Search Console “Submit” if present.
- X compose URLs are opened; **Post is a human click**.
- Never paste `~/.kraken/keys` into a page.
