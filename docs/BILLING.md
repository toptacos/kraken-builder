# Billing (not live)

Stripe account visible in this session: **McAchran Consulting LLC**, livemode only.

Do **not** create products or Checkout Sessions against live mode from CI.

When you add a **test-mode** Stripe context:

1. Set `STRIPE_SECRET` (sk_test_…) and `KRAKEN_BILLING=1` on api.topta.co.
2. `POST /api/kraken/billing/checkout` should create a Checkout Session for SKU `featured-catalog` or `tentacle-seat`.
3. Webhook `checkout.session.completed` writes `kraken_licenses`.
4. `POST /api/kraken/licenses/issue` for plan `beta` stays free (random `k_` key). Paid plans return 402 until checkout succeeds.

Until then, `kraken license set` + `KRAKEN_LICENSE_OFFLINE=1` is the local path.
