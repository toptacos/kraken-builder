# Monetization and hosting

## Who pays whom

| Money | Who | What |
|---|---|---|
| Premium tentacle license | instance owner → TopTaco | right to run `taco` |
| Reward fulfillment | instance owner → recipient | stickers, lunch, swag |
| Peer tacos | nobody | not currency outside the instance |

TopTaco does not take a cut of peer grants. Tacos are not sold to employees. If you want paid rewards, the owner buys the reward off-box and marks `redeem`.

Billing stays on https://api.topta.co license/verify (402 if unpaid). Taco does not implement Stripe.

## Data hosting

Policy field `hosting.mode`:

- `local` — `$KRAKEN_HOME/.kraken/data/taco/ledger.json` (default)
- `toptaco` — optional **aggregate** receipt to https://api.topta.co (counts, not names if `anon: true`)
- `third` — owner-supplied HTTPS endpoint; taco POSTs the same envelope it already stores locally. No AWS SDK. No silent S3.

Always write local first. Remote is a copy. If remote fails, local still stands.

## TopTaco API fit

Use existing catalog + license on https://api.topta.co. Product site: https://kraken.topta.co. Company: TopTaco. Do not call the site “Topta”.

1. Catalog lists `taco` as premium.
2. License verify gates `init` in core (not reimplemented here).
3. Optional `POST https://api.topta.co/api/kraken/taco/receipt` later: `{org, tacos_awarded, redemptions}` only.
4. Org ids from the TopTaco API are *names*, not a remote-admin channel (see inlet).

## Chat

Commands are **`/kraken taco @user`** or **`/tt taco @user`**. Bare `/taco` is ignored so other Slack apps keep their slash command.
