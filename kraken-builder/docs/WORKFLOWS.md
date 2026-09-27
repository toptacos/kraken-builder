# Workflows

A workflow is a YAML goal: tentacle requests and responses, **one after another** or **in parallel**.

This is not a hook (side effect) and not middleware (HTTP). It is an explicit plan.

```bash
python3 bin/kraken workflow run examples/workflows/polyglot-goal.yaml
```

## Schema

```yaml
name: polyglot-goal
goal: human description
steps:
  - id: seed
    tentacle: echo
    action: ping
  - id: fanout
    parallel:
      - id: js
        tentacle: echo-js
        action: ping
        payload: { from: $seed }
  - id: fold
    tentacle: echo
    action: echo
    payload:
      langs: $fanout
```

- Sequential steps run in list order.
- `parallel:` runs children on a thread pool; the parent result is `{ child_id: response }`.
- `$step_id` and `$step_id.result.field` interpolate prior results into the next payload.
- Each step still goes through `resolve`, licenses, and hooks.

## vs queue vs compose vs hooks

| Tool | Use |
|---|---|
| `kraken run` | One tentacle |
| `--compose` | Run *declared deps* of one tentacle |
| `kraken queue` | FIFO in-process jobs |
| hooks | Side effects around a run |
| **workflow** | A named goal with seq + fan-out and `$refs` |

## Language compatibility

Same contract in every tentacle under `examples/tentacles/polyglot/`:

| File | Runtime | Tentacle name |
|---|---|---|
| `echo-bin.py` | python3 | echo-bin |
| `echo.sh` | bash | echo-sh |
| `echo.js` | node | echo-js |
| `echo.php` | php | echo-php |
| `echo.rb` | ruby | echo-rb |
| `echo.pl` | perl | echo-pl |
| `echo.go` | go run | echo-go |

Rust/C/Java compile to a binary and set `binary:` to that file. Core only cares about stdin/stdout JSON. See `docs/CONTRACT.md`.

`seq-forecast.yaml` is the geo → weather-pro chain (install + license first).
