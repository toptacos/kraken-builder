# Kraken compared with other tools

Kraken is a **local-first CLI plugin runner**. JSON in → policy → exec → JSON out. Tentacles are separate binaries in any language. Suckers are named hooks. Core does not import tentacle source, does not ship compilers, Docker, LLM weights, or a CA.

This is not an automation SaaS, not an IaC compiler, and not an agent that decides the goal for you.

## Snapshot

| Tool | What it is | Runs where | Extension model | Language lock | Default network | Paid layer |
|---|---|---|---|---|---|---|
| **Kraken** | CLI plugin runner | Your machine | tentacle.yaml + stdin/stdout JSON | None (Python, Node, bash, osascript, Go, …) | Loopback; grant before expose/tunnel | Scourge seat / premium tentacles. Checkout on profile.topta.co |
| **n8n** | Workflow engine | Self-host or cloud | Nodes in JS/TS inside the product | Node runtime | Server opens ports; cloud is public | Cloud + enterprise |
| **Zapier / Make** | Hosted iPaaS | Their cloud | Built-in apps | None for users; you do not run code locally | Always public SaaS | Per-task pricing |
| **GitHub Actions** | CI on git events | GitHub runners | Actions (containers/JS) | YAML + whatever the action ships | GitHub network | Minutes + larger runners |
| **Terraform / OpenTofu** | Infra as code | Your machine → APIs | Providers | HCL + Go providers | Talks to cloud APIs | Support / Terraform Cloud |
| **Docker Compose** | Process + network graph | Docker engine | Compose YAML | Images, not a JSON contract | Bridge / published ports | Docker Desktop tiers |
| **just / Taskfile / make** | Command runner | Your machine | Recipes in a file | Shell | Whatever the recipe does | Free |
| **Deno tasks / npm scripts** | Package scripts | Your machine | package.json / deno.json | JS/TS ecosystem | Whatever the script does | Free |
| **Claude Computer Use / agent CLIs** | Model drives the UI | Mixed | Tools the model is allowed to call | Model + tool schema | Often cloud + local | Token billing |

## 1. n8n

n8n is a **graph of nodes** with credentials, retries, and a web editor. You host a server (or pay for n8n Cloud). Nodes are TypeScript inside n8n’s process.

Kraken has **no workflow canvas and no always-on server**. A tentacle is a process you already trust. A sucker is a hook, not a node library. If you need a 40-step CRM sync with OAuth refresh, n8n is the better product. If you need “run this AppleScript, patch the text, write a file,” Kraken is smaller and stays on the box.

**Network:** n8n listens. Kraken binds `127.0.0.1` unless you grant expose/tunnel or set docker-env `public: true`.

## 2. Zapier / Make

Those products **sell executions in someone else’s cloud**. Data leaves the laptop. Apps are a catalog Zapier maintains.

Kraken **does not proxy your Open-Meteo call or Chrome console scrape through TopTaco**. The tentacle talks to the API. The portal (api.topta.co) is for licenses, devices, and contact — not for running tentacles.

Use Zapier when the other system only offers a hosted connector. Use Kraken when the work is local (osascript, files, loopback services).

## 3. GitHub Actions

GHA is **CI attached to a git remote**. Matrix OS, secrets, artifacts. Kraken’s GitHub Actions test Kraken; they are not the product.

Kraken **runs on your PATH** (`kraken` / `k`) with no push required. A tentacle does not need to be an Action. You can still call `k run wx` from a GHA step if you want CI to use the same contract.

**Fit:** GHA for “on push, test.” Kraken for “on this machine, attach a binary.”

## 4. Terraform / OpenTofu

Terraform **converges cloud APIs to a desired state**. Providers are Go plugins with a typed protocol. State is the product.

Kraken **does not manage infra state**. `docker-env` plans Compose; it is not a replacement for `terraform apply`. Grants are allow-lists, not a plan/apply graph.

If the job is “create a VPC,” use Terraform. If the job is “fetch weather, convert units, write a report,” use Kraken.

## 5. Docker Compose

Compose **is** the process graph. Kraken may **plan** Compose (`docker-env`) but core does not embed the Docker engine. Isolation is optional and requested by the tentacle.

Compose publishes ports as you write them. Kraken’s default is loopback. That is a policy difference, not a feature checkbox.

## 6. just / Task / make

Those are **named shell recipes**. They are excellent. They do not:

- enforce a JSON contract between recipes
- default-deny expose/tunnel
- store 0600 license keys
- call `finish` after a hook returns a `patch`

Kraken is what you add when recipes become plugins other people ship in other languages. If a 20-line Makefile is enough, do not install Kraken.

## 7. Agent / Computer-Use CLIs

Those tools **choose actions**. Kraken **does not**. The user names the tentacle and action. Suckers patch; they do not invent a goal. The playground on kraken.topta.co simulates JSON and does not exec on the host.

If you want a model to drive Chrome, that is a tentacle you write (`browse-js` with `KRAKEN_CHROME=1`) plus your own policy. Core will not grow an LLM.

## What Kraken is better at

- Same contract from AppleScript, Node, Python, bash
- Data typed as `kind: text | file | media | params | json` without core parsing the bytes
- after_run sucker → `patch` → tentacle `finish`
- Default deny + 0600 keys
- Two clients only: same-device Capacitor panel, portal via api.topta.co
- MIT core; paid is a seat, not a fatter binary

## What Kraken is worse at

- Visual workflow editing (n8n / Make)
- Hosted connectors with OAuth (Zapier)
- Cloud desired-state (Terraform)
- Git-native CI UI (GitHub Actions)
- Deciding the next step for you (agents)

## One-line positioning

**Kraken is closer to a typed `make` that can run any language and refuse dangerous verbs until you grant them — not closer to n8n, Zapier, or Terraform.**
