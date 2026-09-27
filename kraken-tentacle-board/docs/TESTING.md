# Testing

```bash
KRAKEN_OFFLINE=1 python3 tests/test_board.py -v
KRAKEN_OFFLINE=1 python3 tests/e2e_scenarios.py -v
KRAKEN_OFFLINE=1 python3 tests/test_suckers.py -v
KRAKEN_OFFLINE=1 python3 tests/test_license_roles.py -v
```

CI: `.github/workflows/ci.yml` (ubuntu / macos / windows). Image job is optional; host path does not need Docker.
