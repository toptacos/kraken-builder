# berth — local full setup

Kraken is **one small binary**. Custom commands stay in tentacles. Core owns shared server resources on a **Docker network named `kraken`**.

Documented core verb used here: **`up`** (`kraken up`). berth **parses** project config and writes compose. Core (or docker compose on the host) attaches the network. This sandbox does not start a daemon.

```
project.yaml  →  berth plan  →  compose.yaml + hook list
              →  berth up    →  state under $KRAKEN_HOME/.kraken/data/berth
              →  kraken up   →  core joins services to network `kraken`
```

A tentacle may expose **any number of functions**. berth’s are plan, up, down, status, hook, services.

Third-party services are **names and URLs only**. Secrets stay in keeps.

Hub context: frontends on https://topta.co subdomains; jobs on https://api.topta.co. This arm is the local docker twin of that split.
