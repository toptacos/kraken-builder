# Capacitor WebView ↔ Kraken panel

Capacitor’s WebView is not a browser tab. JS at the **app origin** (`https://localhost` / `capacitor://localhost`) can call plugins. Anything loaded as `server.url` is treated as live-reload and is **not** a production pattern.

## What Kraken should do

| Mode | How | Store-safe? |
|---|---|---|
| Default | Bundle `panel` HTML in `apps/native/www` (`webDir`). Offline works. | Yes |
| Dev on same phone/laptop | `kraken run panel ui` then debug `server.url = http://127.0.0.1:18181` + `cleartext: true` | Dev only |
| LAN other device | `expose` + `ca` HTTPS. Add host to `allowNavigation`. Still not `0.0.0.0` from panel. | Gray; prefer bundled UI |

Do **not** ship `server.url` pointing at kraken.topta.co as the whole app. Reviewers treat that as an empty shell. Ionic documents `server.url` as live-reload only.

## Config sketch (dev)

```ts
const config = {
  appId: "co.topta.kraken",
  appName: "Kraken",
  webDir: "www",
  server: {
    hostname: "localhost",
    androidScheme: "https",
    // DEV ONLY:
    // url: "http://127.0.0.1:18181",
    // cleartext: true,
    // allowNavigation: ["127.0.0.1", "127.0.0.1:18181"],
    errorPath: "offline.html",
  },
};
```

Android API 28+ blocks cleartext unless `cleartext: true`. iOS needs ATS exception for `127.0.0.1` if you use HTTP. Self-signed `ca` certs often fail WKWebView unless the user trusts the CA.

LAN IP in the WebView needs `allowNavigation` entries **with and without port** or plugins may not inject (`androidBridge` issue on remote HTTP origins).

## Plugins vs remote origin

Plugins work when the page origin is Capacitor’s localhost. If you `loadUrl` a LAN site, Secure Storage / Device often break unless `allowNavigation` matches. Keep the shell bundled; have it `fetch` `http://127.0.0.1:18181` only for live status JSON, or use `@capacitor/http` after the CLI is up.

## Security

The WebView origin is trusted. Do not deep-link into `/_capacitor_http_interceptor_?u=`. Do not `allowNavigation: ["*"]`. Contact POST stays a plan unless the user is logged in.

## Same-device assumption

Panel bind is `127.0.0.1:18181`. That is the **phone or laptop running `kraken`**, not a server on the WAN. Capacitor on a phone cannot see the laptop’s 127.0.0.1. For two devices use org scope + api.topta.co queue, not WebView-to-foreign-loopback.
