# v5 examples — plan first, then a tested slice

## How to start

```json
{
  "idea": "YOUR IDEA IN 2–5 SENTENCES",
  "named_providers": ["DigitalOcean"],
  "budget_monthly_usd": 20,
  "approve_plan": false
}
```

Set `approve_plan` to `true` only after you accept the plan.

Connected in this Grok account today: GitHub, Gmail, Google Drive, Voice, Automations.
Connectable later: Vercel, Netlify, Wix, Stripe, Whop, HubSpot, X Ads.
DigitalOcean is **not** a connector here. Naming it produces a runbook + IaC + tests, not a live droplet, unless you add DO credentials in your own environment.

---

## Example A — “Full working site + DevOps + automated content”

**Idea**

```json
{
  "idea": "A small public site that lists this week's cheap weekend races near a city, with an email list and a $5/month supporter tier. I have a DigitalOcean account and want deploy + TLS + a weekly generated draft I approve before send.",
  "target_customer": "casual runners who decide Saturday morning",
  "success_metric": "100 subscribers and 5 paid supporters",
  "named_providers": ["DigitalOcean", "GitHub"],
  "budget_monthly_usd": 24,
  "approve_plan": false
}
```

### Plan the agent should emit (before any droplet)

| Workstream | Slice 1 | Later |
|---|---|---|
| Product | Static site + city page + subscribe form + “this week” list | Accounts, saved cities |
| Host | DO App Platform or $6 droplet + Caddy/nginx, reserved IP, Let’s Encrypt | Spaces CDN |
| Code | New private GitHub repo, branch `feature/weekender-mvp` | —
| Content | Generator writes `content/week.md` from a fixture calendar; does **not** send | Live scrape + human approve |
| Mail | Subscribe stores email in DB or ESP test list | Beehiiv/ConvertKit |
| Money | Stripe test-mode $5/mo (Stripe not connected → runbook + mock e2e) | Live Stripe |
| Acquisition | One SEO page + one X post draft | Ads |
| Non-goals | Native app, marketplace, multi-author CMS |

**Golden-path e2e**

1. `GET /` returns 200 and a race list from fixture data.
2. Subscribe with a test address is accepted; junk email is rejected.
3. `make generate-week` writes a draft file and does not send mail.
4. `make test` and GitHub Actions pass on the feature branch.
5. Staging URL job is **documented as skipped** until DO creds exist.

**DO runbook (not executed without creds)**

- App Platform or droplet in `nyc3`, firewall 22/80/443, Caddy for TLS.
- GitHub Action: test → build → deploy on preview tag.
- Secrets: `DO_TOKEN`, `SSH_KEY`, `STRIPE_TEST_KEY` in Actions, never in git.
- Connectivity test: `curl -fI https://staging.example.com`.

**30/60/90**

- 30: preview URL + 1 approved newsletter dry-run.
- 60: keep or kill paid tier using subscriber count.
- 90: second city or kill the product.

Only after `approve_plan: true` does the engineer create the repo, commit the site, tests, workflow, and DO files.

---

## Example B — “Single cross-platform executable + site + list + money”

**Idea**

```json
{
  "idea": "A single CLI that checks whether a website is up and prints a one-line report. Ship linux/mac/windows binaries, a one-page site, a release newsletter, and a $9 license key later.",
  "approve_plan": false
}
```

### Plan

- Types: `cross_platform_executable` + `marketing_site` + `newsletter` + monetization later.
- Slice 1: Go or Rust CLI (pick from existing skill; do not invent Dart), `uptime check <url>`, GitHub Actions build matrix, README, one-page site in `/site`.
- Money: license key is **day 60**, not slice 1.
- Mail: “new release” list planned, not sent.

**E2E required**

- `cargo test` / `go test`.
- Built binary: `./uptime check https://example.com` exits 0 and prints `UP` or `DOWN`.
- Actions uploads artifacts for linux-amd64, darwin-arm64, windows-amd64 (or a documented subset).
- Site job: `GET /` 200 on preview host or local static server.
- Newsletter: render fixture release notes; send is dry-run.

---

## Example C — what “fully complete” means vs what it does not

**Does**

- Classify the idea into product types.
- Write a management plan covering product, host, tests, content, acquisition, money, support, cost.
- After approval: repo, feature branch, working slice, helper command, GitHub Actions, e2e for that type.
- Use GitHub now. Use Vercel/Netlify/Stripe if you connect them. Emit a DO runbook if you name DO.

**Does not**

- Spin a DigitalOcean droplet from this chat (no DO connector).
- Charge real cards or email a real list from CI.
- Build every workstream in week one.
- Merge to prod unless you ask.

---

## Implement command once you like the plan

```text
Approve the plan. Set approve_plan=true. Implement slice 1 only.
Use GitHub. Do not spend. Keep e2e in Actions.
```
