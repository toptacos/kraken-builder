# Capacitor plugins ↔ Kraken tentacles

Official plugins (Capacitor 6 tag `latest-6`). MIT/Apache. No OneSignal.

| Plugin | Native job | Kraken side |
|---|---|---|
| `@capacitor/local-notifications` | Banner on device | `notify` + ntfy. Do not use `@capacitor/push-notifications` until APNs .p8 exists. |
| `@capacitor/filesystem` | Read/write app docs | `filesort`, `store`, `vault` stay on the CLI machine |
| `@capacitor/geolocation` | GPS | Feed lat/lon into `openmeteo` / `geo` |
| `@capacitor/device` | Model, OS | `pi-net status` analogue for the phone |
| `@capacitor/network` | Online/offline | Skip remote sync when offline |
| `@capacitor/preferences` | KV | Pinboard cache (`kraken account pin`) |
| `@capacitor/app` | Pause/resume | Poll `/api/kraken/queue` on resume |
| `@capacitor/camera` | Photo | Optional later; not in vanilla |
| `@capacitor/clipboard` | Copy install command | Website + native shell |
| `@capacitor/share` | Share a run id | Result JSON link, not secrets |

Install in `apps/native`:

```
npm i @capacitor/local-notifications@latest-6 @capacitor/filesystem@latest-6 \
      @capacitor/geolocation@latest-6 @capacitor/device@latest-6 \
      @capacitor/network@latest-6 @capacitor/preferences@latest-6
npx cap sync
```

The shell does not exec tentacles. It posts `{lat,lon}` or `{path}` to the API queue; the logged-in CLI runs `openmeteo` / `filesort`.
