# Arms

Required `arm.yaml` keys: `name`, `version`, `entrypoint`.

Optional: `description`, `triggers`, `actions`.

`entrypoint` is `module.path:function`. The function signature is:

```python
def handle(action: str, payload: dict, manifest) -> dict:
    ...
```

If `actions` is non-empty, unknown actions raise `PermissionError`.

Discovery path: `<root>/arms/*/arm.yaml`. Extra roots can be passed to `load_arms`.

Arms are **in-process plugins**. External tools are **tentacles** (`docs/wiki/Tentacles.md`, `docs/PLUGINS.md`). `kraken run` tries arms first, then installed tentacles.
