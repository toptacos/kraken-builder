# Articles

Longer-form, worked end to end. Every command block in these articles is
executed by `scripts/verify_articles.py`, in an isolated `KRAKEN_HOME`
(`KRAKEN_OFFLINE=1`, no network), and the output block under it is the real
output — never hand-written. `verify_articles.py --check` fails CI if an
article's published output drifts from what its commands now produce, which
is the only way documentation stays true.

| Article | What it proves |
|---|---|
| [Your first tentacle](first-tentacle.md) | Scaffold → install → run → refuse correctly → break it on purpose. The contract in five minutes. |
| [Polyglot: one contract, six languages](polyglot.md) | The same tentacle in sh, python, node, php, ruby, perl, and go, then all of them in one parallel workflow. |
| [Hooks: after_run, patch, and finish](hooks.md) | A hook tentacle returns a patch; core calls `finish` with it. Includes the optional/required distinction that gates a run. |
| [Offline first, grants before exposure](offline-first.md) | Works with the network cut; what can leave the box, proven by parsing core's imports; default-deny exposure. |

## Running the articles yourself

```bash
python3 scripts/verify_articles.py            # execute and refresh outputs
python3 scripts/verify_articles.py --check    # verify only, fail on drift
```

Each article runs in its own temporary home and workspace, so running them
cannot touch your `$KRAKEN_HOME`. Blocks tagged `run,expect-fail` assert the
failure they describe; everything else asserts a clean exit code.

## Writing a new one

1. Write the article with `run,sh` blocks followed by empty `output` blocks.
2. Run `scripts/verify_articles.py`; it fills the outputs and fails on any
   non-zero exit (blocks run under `set -e`, so a failing line anywhere is a
   failure, not just the last one).
3. Re-run: the second pass must produce a byte-identical file.
4. Reference repo files via `$KRAKEN_REPO_ROOT` — never an absolute path
   from your machine.
5. Add a row to the table above.
