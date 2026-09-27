# keel

First timber. Tick before you register.

- [ ] `tentacle.yaml` — `name` `/^[a-z0-9-]+$/`, `license`, `actions`, `platforms`
- [ ] `handler.sh` (+ Go binary or `handler.py`)
- [ ] `ping`, unknown action, `finish` (sucker merge), `clear`
- [ ] `where` if more than one store scope
- [ ] `platforms.*.tested: true` only on OSes that ran the binary
- [ ] `handler.sh` stages off `noexec` mounts
- [ ] One sucker under `suckers/` and an `after_run` row
- [ ] One workflow under `workflows/`
- [ ] Tests: `test_<name>.py`, `e2e_scenarios.py`, `test_suckers.py`, `test_license_roles.py`
- [ ] Logs in `docs/test-logs/`
- [ ] Docs: USAGE, ARCHITECTURE, SECURITY, TESTING, SUCKERS, DOCKER, DIRECTORY, LAUNCH
- [ ] CI matrix linux / darwin / windows
- [ ] Dockerfile **or** Go `CGO_ENABLED=0` matrix with receipts
- [ ] `branding/index.html` + one still
- [ ] `schemas/catalog.json`
- [ ] README + MIT LICENSE

Go arms: `build.sh`, `dist/*`, `SHA256SUMS`, `go version -m`.  
Python arms: the handler *is* the portable artifact (jev-ai pattern).
