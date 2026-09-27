# Security notes

watch is a homelab observer for **your** machine.

- Do not point browser/media targets at other people’s sessions or displays.
- Screen attach is an explicit local capture for an alert you already own.
- `KRAKEN_WATCH_EXEC=1` is equivalent to `hotreload`’s command runner: whoever can `kraken run` owns the shell.
- `kraken grant watch` is core default-deny. Live browse/capture still also need env flags.
- Hook binaries see the main `result`. Keep suckers cheap; do not log secrets from `payload`.
- `start` writes user-level units only. Systemd system units and launch daemons are out of scope on purpose.
- Dist artifacts must be `CGO_ENABLED=0`. `scripts/verify-dist.sh` is the check.
- `tentacle add` from git is the same trust model as `curl | sh`. Only add trees you built or reviewed.
- Never commit `~/.kraken/keys`.
