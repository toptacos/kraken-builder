# Implementation pack

Drop-in order for api.topta.co + this tree. Core stays MIT and offline-first.

## 1. CLI (already in tree)

```
kraken init
kraken vanilla
kraken account login you@example.com
kraken account pin default_pi 192.168.1.42
kraken account sync          # no-op unless KRAKEN_SYNC_REMOTE=1
kraken account push --on --token '<web-push-or-fcm>'
```

Session file: `~/.kraken/keys/session.json` mode 0600.

## 2. API (copy into Laravel)

- `control-plane/laravel-api/routes/kraken.php`
- migrations `000001` licenses, `000002` catalog, `000003` users/devices/sessions/queue

```
POST /api/kraken/session/login
POST /api/kraken/session/sync
POST /api/kraken/devices/push     # stores token only
POST /api/kraken/queue            # phone → named CLI device
POST /api/kraken/licenses/* + catalog
```

Push **vendor is a stub**. Wire FCM v1 / APNs / VAPID in a Laravel job later. Do not put Firebase in core.

## 3. Clients (not built here)

| Client | Talks to | Runs tentacles? |
|---|---|---|
| CLI | local + optional API | yes |
| Web SPA | API | no |
| Chrome extension | Web Push + API | no |
| iOS / Android | APNs/FCM + API | no — enqueue only |

## 4. Money

Free: CLI + vanilla. Cloud: extra devices + pack relay. Premium tentacles: existing license keys. Stripe: test mode only (`docs/BILLING.md`).

## 5. Docker

Only `runtime`, `docker-env up`, `sites up`. Internal `kraken_*`, 127.0.0.1 publishes.

## 5. Free vendors only
docs/FREE_STACK.md — ntfy + VAPID + Capacitor. No Firebase in core.

