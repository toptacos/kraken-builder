# Device groups

`kg_<hex>` ties laptops and phones. Each box also records:

| Field | Source | Stored? |
|---|---|---|
| `nic_` hash | `uuid.getnode()` SHA-256 prefix | yes — never the raw MAC |
| `last_seen` | UTC when `account group/join/login` runs | yes |
| `signals.on` | process is running | yes |
| `signals.plugged_in` / `charge_pct` | `/sys/class/power_supply` when present | yes |
| unlocked / screen | Capacitor later | not in CLI |

Alerts (`sess["alerts"]`, `notify` event `device.alert`):

- `new_device_on_group` — second device_id on this home
- `stale_device_returned` — last_seen older than `KRAKEN_DEVICE_STALE_SECS` (default 30 days)
- `nic_changed` — same device_id, different hashed NIC (copied `session.json` onto other hardware)

```
kraken account group
kraken account join kg_… --device phone
```
