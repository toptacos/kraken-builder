# Free stack. Paid only when we choose it.

Core rule: if a vendor meter exists, we do not import it into `kraken.core`.

| Need | Free path | Paid we refuse in core |
|---|---|---|
| CLI + tentacles | This repo, MIT | none |
| Account / catalog / licenses | Your Laravel + Postgres on api.topta.co | Auth0, Clerk |
| Notify laptop | stdout, webhook, **ntfy.sh** or self-hosted ntfy | OneSignal, Pusher Beams |
| Web / Chrome push | **Web Push + VAPID** (openssl keys) | FCM web SDK |
| iOS / Android UI | **Capacitor** wrapping `apps/native/www` | Ionic Appflow unless you want it |
| iOS delivery | APNs .p8 (Apple fee is the dev account, not per push) | FCM-as-required |
| Android delivery | Capacitor local notifications + Web Push; FCM only if Play forces it later | Firebase Analytics |
| Object storage | local store tentacle; optional MinIO | paid S3 as a hard dep |
| Billing | skip until a Cloud SKU exists; then Stripe test | Chargebee |
| CI | GitHub Actions free tier | extra hosted device farms |

```
KRAKEN_NTFY_TOPIC=kraken-matt
KRAKEN_NTFY_URL=https://ntfy.sh          # or http://ntfy on kraken_dev
kraken account push --on
```

Phone app is `apps/native` (Capacitor). It does not run tentacles. It shows pinboard + queued jobs + ntfy/Web Push.

Generate VAPID (free, offline):

```
bash scripts/vapid.sh
```
