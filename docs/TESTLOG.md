# Test log

2026-09-10 19:45 EDT

```
tests/test_free_apis.py
tests/test_sync.py
tests/test_notify_ntfy.py
tests/test_example_packs.py
tests/test_runtime.py
........  8 passed
```

Covered: offline Open-Meteo + ip-api fixtures, account session, ntfy quiet emit, pi-net/filesort/sites, runtime plan with data `:ro`.

2026-09-12 13:33 EDT

```
tests/test_sync.py test_runtime.py test_hooks.py test_contract.py
test_free_apis.py test_tentacle_install.py test_cli_e2e.py test_site_e2e.py
test_dev_tentacles.py
.......................... + site/dev  passed
```

Added website/security.html, website/docker.html, docs/USERNS.md. Brand kit in website/img/kit-2026/. Training shorts train-*.mp4.

Not run in this slice: full site E2E + hello-world compilers (slow on this image).
