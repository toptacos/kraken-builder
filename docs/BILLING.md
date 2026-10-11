# Billing (not live)

Stripe account visible in this session: **McAchran Consulting LLC**, livemode only.

Do **not** create products or Checkout Sessions against live mode from CI.

## Plan slugs

These plans exist in the TopTacos API's `BillingSeeder`:

| Plan | Price | Features |
|------|-------|----------|
| `beta` | Free | Random `k_` key, no Stripe checkout |
| `kraken-starter` | $19/mo | One device, 0600 keys, default deny |
| `kraken-pro` | $49/mo | Five devices, org API keys, email support |
| `kraken-enterprise` | $149/mo | Unlimited devices, priority support |

The CLI validates plan slugs in `kraken.core.license.PLAN_SLUGS`. The API
enforces them in `POST /api/kraken/licenses/issue` — paid plans return 402
until Stripe checkout succeeds.

## When you add a **test-mode** Stripe context

1. Set `STRIPE_SECRET` (sk_test_…) and `KRAKEN_BILLING=1` on api.topta.co.
2. `POST /api/kraken/billing/checkout` should create a Checkout Session for SKU `featured-catalog` or `tentacle-seat`.
3. Webhook `checkout.session.completed` writes `kraken_licenses`.
4. `POST /api/kraken/licenses/issue` for plan `beta` stays free (random `k_` key). Paid plans return 402 until checkout succeeds.

Until then, `kraken license set` + `KRAKEN_LICENSE_OFFLINE=1` is the local path.

## Optional package (`kraken.billing`)

MIT core does not require this. Free tentacles never import it.

```python
from kraken.billing import BillingClient, LicenseError
client = BillingClient()          # KRAKEN_API_BASE, default api.topta.co
client.set("weather-pro", "KEY")  # ~/.kraken/keys/licenses.json 0600
```

CLI: `kraken license status|set|verify`. Seats ($19 / $49 / $149) checkout on **profile.topta.co/pricing**. The CLI never opens Stripe.

Hooks (`after_install`, `on_error`) may point at the optional `billing-log` tentacle. Set `KRAKEN_BILLING_LOG=1` for JSON lines on stderr.

Not required to run `kraken demo`. Not phone-home for geo, filesort, panel, expose.

## Canonical source

The billing implementation lives in the TopTacos API:
- Plans: `toptaco-api/database/seeders/BillingSeeder.php`
- Stripe: `toptaco-api/app/Services/StripeService.php`
- License verify: `toptaco-api/routes/kraken.php`

The Kraken CLI's `kraken/billing/client.py` is a thin wrapper that talks to
the API. It does not implement its own billing logic.
