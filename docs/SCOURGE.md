# Scourge (premium panel)

Free: `panel` — one device, paths, resources, contact *plan*.  
Paid: `scourge` — org-scoped fleet after login + license + grants.

```
kraken account login you@example.com
kraken license set scourge KEY
kraken grant scourge
kraken grant remote_config
kraken tentacle add examples/tentacles/scourge
kraken run scourge status
kraken run scourge devices
```

`devices` fails until `grant scourge`. `share-plan` fails until `grant remote_config`. Sharing is a plan (hash + path), not raw secrets. Tunnel still uses the free `tunnel` tentacle on 127.0.0.1.

Site: https://kraken.topta.co (DNS already on DigitalOcean). Deploy `website/` with `docs/DEPLOY_TOPTA.md`.

Social: drafts only in `docs/SOCIAL.md`. Do not script account creation.
