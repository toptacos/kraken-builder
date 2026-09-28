# Configuration

Everything Kraken reads, where it reads it from, and what each setting does.

The schema in `kraken/core/config_schema.py` is the source of truth. This
document, `kraken config list`, the generated examples, and the test suite are
all derived from it, so they cannot drift apart — `test_config.py` fails if any
of them do.

## Inspect it first

```bash
kraken config list                 # every setting, with its effective value
kraken config list | jq            # same, as JSON
kraken config get docker           # one setting
kraken config explain data_dir     # which file won, and what it overrode
kraken config path                 # the chain of files, in order
kraken config validate             # check everything; exit 2 on problems
kraken config init --scope project # write a commented example
```

`config list` marks a line with `*` when the value is not the default, and
tells you which scope set it. That is usually the whole answer to "why is it
doing that".

## Three scopes, weakest to strongest

| Scope | Path | Who it is for |
|---|---|---|
| system | `/etc/kraken/config.yaml` | machine-wide defaults for everyone on this host |
| user | `$KRAKEN_HOME/.kraken/config.yaml` | this person |
| project | `<dir>/.kraken/config.yaml`, walking up from the cwd | this project, travels with it |

`kraken config path` prints the chain in the order it is applied. A setting set
in more than one place takes the value from the strongest scope that mentions
it. **A project config beats your user config** — that is the point of project
scope, and it is why a project file belongs in version control.

### Merge rules

- **Maps merge per key.** A project can change `docker.driver` without
  restating `docker.enabled`.
- **Lists replace.** Overriding a list means "this is the list", not "these
  too". Two scopes that both list `telemetry.events` do not concatenate.
- **A setting that no scope mentions keeps its default**, so a partial file is
  always a complete config.
- **Unknown keys pass through `load_config` unchanged**, so a config written by
  a newer Kraken does not lose settings to an older one. `kraken config
  validate` reports them instead.

### Environment

A few settings are better driven by the environment than by a file, because
they depend on the machine rather than the intent. For those, the environment
wins over every scope:

| Variable | Effect |
|---|---|
| `KRAKEN_HOME` | Where the user config and data live |
| `KRAKEN_SYSTEM_DIR` | Where the system config lives (default `/etc/kraken`) |
| `KRAKEN_OFFLINE=1` | Forces `telemetry.enabled` off, and makes `kraken up --start` refuse |
| `KRAKEN_DOCKER_CONFIG_URL` | Supplies `docker` config from a URL — skipped entirely when offline |
| `KRAKEN_LICENSE_REMOTE=0` | Keeps licence verification local |
| `KRAKEN_NOTIFY_WEBHOOK`, `KRAKEN_NTFY_TOPIC`, `KRAKEN_NTFY_URL` | Credentials for those notify channels |
| `KRAKEN_NOTIFY_STDOUT=1` | Required before the stdout channel prints anything |

A notify channel whose variable is unset is **skipped**, not an error. A
notification must never fail the action that triggered it.

## The settings

Thirteen, in the order the docs read them.

### `version` — integer, default `1`

Config schema version, not the CLI version. Bumped only when a key changes
meaning or a new required key appears. A `version` newer than the build
understands is reported by `validate` rather than ignored.

### `data_dir`, `log_dir`, `cache_dir`, `key_dir` — strings

Directory names under `$KRAKEN_HOME/.kraken`. `data_dir` is honoured by the
arms, by `kraken up`, and by `kraken doctor`.

Changing `data_dir` after arms have written data **leaves that data behind**
rather than moving it. Migrate it yourself, or leave the default.

`cache_dir` is safe to delete. `key_dir` holds 0600 secrets: never uploaded,
never printed, and `keeps` refuses to sync it.

### `allow` — map, all false by default

Capability grants. **Default deny**: a capability that is absent or false is
off.

```yaml
allow:
  tunnel: false
  remote_config: false
  scourge: false
  llm: false
  expose: false
```

Manage it with `kraken grant <name> on|off` rather than by hand — that writes
the file atomically and keeps it at 0600. An unknown name is rejected.

Grants are honoured at every scope, so a project can lock a capability off even
if the user enabled it:

```yaml
# project .kraken/config.yaml
allow:
  expose: false     # not in this repo, thank you
```

> A **commented-out** line is not a grant. This was a real bug: the resolver
> used to grep the file text for `expose: true`, so
>
> ```yaml
> # I do NOT want this grant:
> # expose: true
> ```
>
> granted it. The resolver parses YAML now. `test_config.py` pins it.

### `policy` — map

```yaml
policy:
  default: deny      # deny | allow
  grants: []          # capabilities arms may use
  network: kraken     # shared Docker network name
```

`network` feeds the Docker resolver. An arbitrary label is namespaced to
`kraken_<label>`, so two projects cannot collide on one host. `kraken` itself
passes through unchanged.

`default: allow` exists for CI and throwaway containers. Leave it `deny`
anywhere you care about.

### `notify` — map

```yaml
notify:
  channels: [stdout]   # stdout | webhook | ntfy
  on_success: true
  on_error: true
```

The config picks the channels; the environment supplies each channel's
credentials. `stdout` is the only one that stays on the machine.

`notify: local` — the shorthand older installs wrote — still works and means
`channels: [stdout]`. `notify: none` means no channels, which is different
from omitting the setting.

> `webhook` and `ntfy` send data off the machine. That is the one place Kraken
> is not local-first, so it is opt-in and never the default.

### `docker` — map

```yaml
docker:
  enabled: false       # false means Kraken starts no daemon
  name: kraken
  driver: bridge
  public: false
  isolated: false
  provider: local
  config_url: ""
```

`enabled` is false by default. `kraken up` is plan-only unless `--start`, and
refuses to start when `KRAKEN_OFFLINE=1`.

`public: true` is rejected by `validate` — Kraken will not publish a network.

`config_url` is an outbound fetch. It is skipped entirely under
`KRAKEN_OFFLINE=1`, which reports `fetch_skipped: offline` rather than
silently reaching out.

### `hooks` — map

Arms to run around another arm's actions. Keyed by event:

```yaml
hooks:
  after_install:
    - tentacle: echo-bin
      action: ping
      optional: true
  after_run:
    - tentacle: ledger
      action: append
      when: [watch, "*"]
      priority: 10
```

Events: `after_install`, `after_up`, `before_run`, `after_run`,
`before_remove`. An unknown event is a typo that would never fire, so
`validate` rejects it.

A bare string means `{tentacle: <name>, action: ping}`. `when` filters by
target arm. Lower `priority` runs first. A hook naming its own target is
skipped, so a cycle cannot form.

### `tentacles` — list

```yaml
tentacles:
  - name: geo
    kind: binary
    binary: examples/tentacles/geo
    actions: [lookup]
    needs_docker: false
```

Arms installed under `tentacles/` are discovered automatically, so use this to
pin order, declare `requires`, or register a binary that is not on disk. Not
for declaring an arm that already exists on disk.

### `telemetry` — map

```yaml
telemetry:
  enabled: false
  events: [install_ok, demo_ok, second_cmd]
```

Off unless enabled. Never sends argv, paths, or file contents.
`KRAKEN_OFFLINE=1` forces it off regardless of what the file says.

### `license` — map

```yaml
license:
  api_base: https://api.topta.co
  remote: true
  offline: false
```

The answer is two-state: **200** means a paid, current seat; **402** means buy
one. `remote: false` keeps verification local, which is what the test suite
does.

## Writing an example

```bash
kraken config init --scope system   # /etc/kraken/config.yaml
kraken config init --scope user     # $KRAKEN_HOME/.kraken/config.yaml
kraken config init --scope project  # ./.kraken/config.yaml
```

`init` never overwrites an existing file. The committed examples in
`examples/config/` are generated from the same function, and a test asserts
they are byte-identical — if one drifts, the suite fails.

## What to commit

Commit a project `.kraken/config.yaml`. It holds no secrets by design: keys
live in `key_dir` under the user home and are never read from a project file.

Do not commit anything under `$KRAKEN_HOME` — `grants.json`, `licenses.json`,
`keys/`, or data directories.

## Testing a config change

```bash
kraken config validate        # before you commit it
python3 -m pytest tests/test_config.py -q
```

`test_config.py` walks the schema rather than hand-picking keys, so a setting
added without a test fails the suite.
