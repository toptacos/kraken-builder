# TopTaco + Kraken — understanding, brand, money, steps

2026-09-26. Company: **TopTaco**. Zone: **topta.co**.  
CLI product: **Kraken**. Site: https://kraken.topta.co. Hub: https://topta.co.

## 1. What this actually is

**TopTaco** is a small-team ecosystem: one account, many side-project frontends on a cheap DigitalOcean droplet, and **one API box** that holds data and job queues.

**Kraken** is the developer product in that grid: a **single small binary** that runs **tentacles**. Core does shared work (policy, grants, optional Docker network `kraken`, optional billing). A tentacle is any number of functions behind JSON stdin/stdout. berth is the tentacle that **parses project config into a local compose/network plan**; core’s verb is **`kraken up`**.

They are not an exchange. They are not a franchise of restaurant reviews only. Taco discovery, music trivia, disc golf, blog, portfolio, and Kraken are **sites mounted on the same account**.

```
*.topta.co  frontend  (droplet, small)
      ↓
api.topta.co          (data + queues)
      ↓
optional: kraken CLI on a laptop  (local arms, shared docker net)
```

## 1b. Playground + meter

Open the code. Treat https://topta.co as the showcase. MIT on arms and static fronts (`docs/OPEN-SOURCE-POLICY.md`). Meter listings, Pro, seats, API quota. Site yaml lives in `sites/`.

## 2. Branding strategy

**Name split (do not collapse):**

| String | Use |
|---|---|
| TopTaco | Company and spoken name |
| topta.co | DNS zone and hub |
| Kraken | CLI product only |
| tentacle / reef | How modules attach |

Never call the site “Topta.” Always write full hosts: https://topta.co, https://kraken.topta.co, https://api.topta.co, https://profile.topta.co.

**Palette (already in use):** ink `#0B1220`, teal `#2FD0C6`, foam `#E7F6F6`, gold `#e7c56a`.  
**Line:** *One binary. Many tentacles.*  
**Marks:** type + geometric TT / tentacle-K. No food mascot on the CLI. Food photography belongs on https://tacos.topta.co and the blog only.

**Strategy:** one login, many faces. Each new project is a tentacle of **brand + host + jobs**, not a new company. Kraken’s monster metaphor is “many arms, one body.” The hub’s metaphor is “many storefronts, one kitchen (the API).”

**Do not:** mix Payward/Kraken.com art, sell tacos-as-currency on the public web, or put CLI screenshots on the restaurant pages.

## 3. Monetization strategy

Sell **access and listing**, not points and not processing of other people’s money.

| SKU | Who | Price to test | Fulfills |
|---|---|---|---|
| Hub free | everyone | $0 | profile + 1–2 sites at tight quotas |
| Hub Pro | humans using tacos/music/notes | ~$10–30/mo (hub already shows $9.99 / $29.99) | more storage, featured listing |
| Restaurant featured | owners on tacos.topta.co | hub already says $29.99/mo | discovery placement |
| Kraken core | developers | $0 MIT | binary + vanilla arms |
| Kraken seats | teams using premium arms (taco) | site pricing $19 / $49 / $149 | license verify |
| Kraken instance | small team, taco only | $29/mo ≤25 users (plan) | one invoice |
| Receipts add-on | orgs that want api.topta.co copies | $5/mo | aggregates, anon default |
| Donate / “buy a taco” | fans | $3–25 | not a product |

**Rules that keep margin:**

- Droplet serves files. API runs queues. Never put job workers on the public frontend box.
- Tentacles do not pull Slack/MLS/GitHub. Inbound only.
- Do not sell peer tacos. Do not host public chat bots.
- License verify is the only required paid call from the CLI.
- Featured restaurant listing is the consumer SKU; Kraken seats are the builder SKU. Do not discount one to prop up the other.

**Sequence of cash:** featured listings + hub Pro (already on the homepage) → Kraken seats once `init` 402s against https://api.topta.co → receipts last.

## 4. Exact implementation steps

### A. Hub droplet (frontends)

1. One nginx (or caddy) on the droplet: `topta.co`, `tacos`, `blog`, `music`, `discgolf`, `kraken`, `profile`, `portfolio`.
2. Each vhost is a directory or a small SPA. No job workers.
3. Add-site = drop a `sites/<name>.yaml` (host, brand colors, public routes, which API collections).
4. TLS already implied; keep one cert wildcard `*.topta.co` if the registrar allows.

### B. API box (data + queues)

1. Bring https://api.topta.co out of 404: `GET /health`, `POST /v1/auth`, collection routes per site.
2. Queue: one worker process (sidekiq / rq / something you already know). Jobs: geocode, thumbnail, email, later taco receipts.
3. API keys for “build & scale” as the hub already promises. Scope keys per site tentacle.
4. License verify for Kraken premium: `POST /v1/kraken/license/verify` → 200 or 402. This is the only CLI billing hook.

### C. Kraken binary (local)

1. Keep core tiny. No tentacle source imported.
2. Contract stays JSON v1 stdin/stdout.
3. `kraken up` reads berth’s compose plan and joins Docker network `kraken` when Docker exists.
4. `kraken <arm> init` uses after_install + prompt envelope.
5. Premium actions 402 until verify succeeds. ping/help free.
6. Cross-compile with `CGO_ENABLED=0` when you ship Go arms (watch). Python arms stay `handler.sh`.
7. Sign drops with minisign; HMAC fixture is CI-only.

### D. Tentacles as two kinds

| Kind | Lives | Example |
|---|---|---|
| Site tentacle | droplet yaml + API collection | tacos, music, discgolf |
| CLI tentacle | `$KRAKEN_HOME` + optional network | berth, taco, watch, keeps |

Same word, two mounts. `tentacle.yaml` should carry `mount: site | cli | both`.

### E. Order of work (do in this order)

1. `GET https://api.topta.co/health` returns 200.
2. Wildcard (or explicit) vhosts on the droplet from `sites/*.yaml`.
3. Profile login actually gates the other hosts.
4. berth `plan`/`up` + document `kraken up` on https://kraken.topta.co/docs.
5. License verify endpoint + taco gated actions.
6. Catalog register for CLI arms (checksum + minisig).
7. Featured listing checkout for restaurants (already priced).
8. Seats checkout for Kraken Pro.
9. Receipts add-on only after a paying org asks.

### F. Done tests

- Curl health on API.
- Add a fake site yaml, see a new vhost without SSH spaghetti.
- `echo '{"v":1,"action":"plan","payload":{"file":"project.yaml"}}' | berth` prints network `kraken`.
- Unlicensed `taco give` → `payment_required`.
- Licensed give after a stub verify file.
- minisign -Vm on a zip.

## 5. What not to do

Do not stand up a second billing system inside a tentacle.  
Do not run Docker on the public droplet.  
Do not scrape MLS or Slack.  
Do not name the company Topta.  
Do not merge this with api.kraken.com.
