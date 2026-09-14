# Testing

```bash
PYTHONPATH=. python3 -m pytest
make e2e
php tests/test_control_plane.php
php tests/test_laravel_lite.php
```

GitHub Actions runs `make e2e` on every push.
