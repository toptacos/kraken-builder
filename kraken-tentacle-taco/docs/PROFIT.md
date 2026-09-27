# Profitability plan — taco (premium)

Company: **TopTaco**. Site: https://kraken.topta.co. API: https://api.topta.co.

## What you sell

| SKU | Buyer | Price to test | What they get |
|---|---|---|---|
| Seat | org that already runs Kraken | $9 / user / month | `taco` listed + license verify |
| Instance | small team, flat | $29 / month up to 25 users | same arm, cheaper than 25 seats |
| Annual | either | 10 months prepaid | cash earlier, less churn work |

Do **not** sell tacos. Do **not** tax peer grants. Do **not** take a cut of lunch cards. Those are the owner's rewards; selling them turns this into a gift-card business with payroll and tax drag.

## Unit economics (planning, not a forecast)

Assumptions you can replace:

- Gross on a seat: ~$9
- Card + tax + verify API: ~12% → net ~$7.90
- Support + catalog review: $1.50 / seat / month if you stay inbound-only
- Contribution ~$6.40 / seat / month

25-user instance at $29 is ~$1.16 / user. Use it as a lander; expand to seats when they hit the cap.

Break-even sketch: 80 seats * $6.40 ≈ $512 / month contribution. That covers a small verify endpoint, not a chatbot farm. Keep bots inbound.

## What makes it profitable

1. **License, not ledger.** Money hits https://api.topta.co/license. The scoreboard stays on their disk.
2. **No hosting COGS on default path.** `hosting.mode=local` costs you nothing. Charge extra only if they want `toptaco` receipts stored for them (then you have storage + DPA). Price that as a separate "receipts" add-on ($5 / month), not bundled.
3. **Connectors stay push.** Every GitHub/Slack crawl you add becomes an on-call cost. Profit depends on refusing pull.
4. **Premium gate at `init`.** Unlicensed runs can `ping` and `help`. `give` / `ingest` / `redeem` return 402 from core, not from this arm inventing Stripe.

## What kills profit

- Selling redeemable store credit
- Public Slack bots you host
- Storing vendor OAuth secrets
- Per-taco transaction fees
- Building a second marketplace on the catalog

## Rollout

1. Catalog list `taco` license=premium on https://kraken.topta.co/pricing.
2. Verify on https://api.topta.co.
3. Ship instance SKU first (one invoice, one hook).
4. Add seats when an org asks to grow past 25.
5. Receipts add-on last, only with `anon: true` default.

## 12-month check

Healthy: seat gross margin > 70%, support tickets < 1 per 20 seats / month, zero payout of peer tacos from TopTaco's bank. If you are wiring rewards for customers, you are in the wrong business line.
