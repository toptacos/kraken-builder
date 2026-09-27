# Tests, e2e scenarios, benchmarks

## Layers

| Command | What it proves |
|---|---|
| `python3 tests/test_watch.py -v` | Protocol v1 against `handler.sh` / binary |
| `python3 tests/test_suckers.py -v` | Sucker YAML + watch-stamp convert |
| `python3 tests/e2e_scenarios.py -v` | User scenarios without requiring `kraken` on PATH |
| `python3 tests/e2e_kraken.py -v` | Same scenarios through `python3 -m kraken` (skipped if core missing) |
| `python3 tests/bench_watch.py` | ping / tick / snapshot timings |
| `go test ./...` | Compile of tagged OS files (few `_test.go` files) |
| `bash scripts/verify-dist.sh` | Each `dist/*` receipt is CGO-off and matches GOOS/GOARCH |
| `bash scripts/ci-test.sh` | Clone core, vanilla, add tentacles, hooks, workflow |
| `docker run --network=none kraken-watch` | Same suite inside Alpine |

## Scenario catalog (`tests/e2e_scenarios.py`)

1. `homelab_disk_tick` — system disk + load targets, offline
2. `browser_fixture` — browse kraken.topta.co without network
3. `media_fixture_attach` — capture writes a fixture file
4. `user_tree_change` — kind=user over a temp directory
5. `notify_bad_webhook_does_not_crash` — dead URL, process still ok
6. `task_exec_default_deny` — grant_required
7. `sucker_stamp_and_finish` — finish merges patch
8. `plan_emits_user_scheduler` — linux systemd-user / darwin launchd / windows schtasks
9. `multi_profile_isolation` — laptop vs pi state files
10. `unknown_action_is_app_error` — exit 0, ok false
11. `clear_removes_profile`
12. `flag_wrapper_ping` — contrib/kraken-watch.sh
13. `workflow_yaml_valid` — watch-alerts.yaml parses

`e2e_kraken.py` repeats 1–7 + workflow through the real CLI when `KRAKEN_SRC` or `PYTHONPATH` contains `kraken.core`.

## Benchmarks

`tests/bench_watch.py` prints ns/op-style timings to stdout (not a pass/fail gate). CI uploads the log. Treat numbers as smoke, not a scoreboard: this host is shared and offline fixtures dominate.

## Cross-OS honesty

GitHub Actions:

- `compile` matrix builds all six pairs on Ubuntu and runs `verify-dist.sh`
- `e2e` runs scenario + sucker + contract tests on `ubuntu-latest`, `macos-latest`, `windows-latest`
- `kraken-e2e` clones core on Ubuntu only (vanilla path)
- `image` builds and runs the Alpine image with `--network=none`

`platforms.linux-amd64.tested` is the only `true` in `tentacle.yaml` until arm64/mac/Win jobs execute the *matching* `dist/` binary (mac/Win e2e currently use `go run` / `handler.py` when the local binary cannot exec).
