# Panel tentacle (Capacitor + local LAN)

Optimized UI for a phone/tablet on the **same machine / loopback**, not the public internet.

```
kraken tentacle add examples/tentacles/panel
kraken run panel status
kraken run panel paths
kraken run panel ui
kraken run panel contact --payload '{"email":"you@example.com","body":"help","scope":"work"}'
```

`status` returns config paths + CPU/disk/mem.  
`ui` writes `~/.kraken/data/panel/index.html`. Serve it:

```
python3 -m http.server --bind 127.0.0.1 18181 --directory ~/.kraken/data/panel
```

Capacitor WebView loads `http://127.0.0.1:18181` when the CLI is on that device. On another LAN host, use `expose` + `ca` — still not `0.0.0.0` from this tentacle.

## Contact

Plans `POST https://api.topta.co/api/kraken/contact` with `{email,body,scope,source:panel}`.  
The CLI **does not send** unless you later add a control-plane route. Live POST is off in this tree.

Control plane should store rows in Kraken’s own DB (not a third-party form). Until that route exists, treat the plan JSON as the contract.

## Native shell

`apps/native` + `docs/CAPACITOR.md`. Panel is the data source; Capacitor plugins (Device, Filesystem, Network) can overlay GPS/battery later without growing core.
