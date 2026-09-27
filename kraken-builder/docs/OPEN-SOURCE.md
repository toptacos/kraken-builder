# Open source + meter

TopTaco playground. Zone https://topta.co.

**Open, MIT, forever:** Kraken core, every arm, the static frontends, and
`sites/*.yaml`. If you can read the source, you can run it. There is no
closed paid arm — a premium action is a *license check* against an MIT arm,
never a hidden binary you cannot inspect.

**Metered, not secret:** API quota, featured listing, hub Pro, optional Kraken
seats, storage. These are prices, not features behind a wall. The free tier is
a real product, not a trial.

**Never in git:** review PII dumps, API keys, `$KRAKEN_HOME`, license private
keys, `keys/`, `licenses.json`, catalog dumps. The CLI refuses those paths at
runtime too — see `kraken/core/paths.py` and the per-arm `jail()`.

## What the code will not do

These are refusals, not omissions. Each has a local substitute.

| Refused | Why | Instead |
|---|---|---|
| Vendor pull (Slack, GitHub, MLS) | A daemon that logs into someone else's system on your behalf is a liability, and MLS data is licensed | Inbound JSON via `connectors/` |
| Public bind | An arm that listens on `0.0.0.0` is a remote shell with extra steps | `127.0.0.1` + a token (`marks listen`) |
| A second Stripe inside an arm | Two billing systems in one tree is how customers get double-charged | One `POST /api/kraken/licenses/verify` → 200 or 402 |
| Docker on the public droplet | The frontend box serves files. That is the whole job | `kraken up` runs on your machine, not ours |
| HMAC sold as Ed25519 | minisign is the real thing; an HMAC fixture is a test, not a signature | minisign, `.minisig` artifacts |

## Telemetry

`KRAKEN_OFFLINE=1` is the default posture. Opt-in events only: `install_ok`,
`demo_ok`, `second_cmd`, `arm_add`, `d7_return`. No argv. No paths. No file
contents. Turn the rest off and nothing leaves the machine.

## Catalog

The catalog at https://kraken.topta.co/catalog lists signed OSS arms and
suckers. Registration records a sha256 and a minisig; `install.sh` verifies
both before anything lands on PATH. `listed: false` is respected everywhere —
an arm stays private until a human approves it.
