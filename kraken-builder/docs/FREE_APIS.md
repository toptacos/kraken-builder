# Free HTTP APIs used by tentacles

No keys in core. Respect rate limits. `KRAKEN_OFFLINE=1` skips the net.

| Tentacle | URL | Limit |
|---|---|---|
| openmeteo | `https://api.open-meteo.com/v1/forecast` | no key; cache |
| ipwhere | `http://ip-api.com/json/{ip}` | ~45/min, HTTP on free |
| geo | local fixture (zip → Kernersville-ish) | none |
| zip (optional) | `https://api.zippopotam.us/us/27284` | no key |

Nominatim (OSM) is 1 req/s — do not put it in a tight loop.

Commercial weather stays in `weather-pro` + a license, not in vanilla.

| zippopotam | api.zippopotam.us |
| quakes | USGS geojson |
| countries | restcountries.com |
