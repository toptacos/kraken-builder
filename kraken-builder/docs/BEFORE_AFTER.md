# Before / after — Nyx’s job

The tired plates are **not** the brand default. They are the *without* shot.

## Without Kraken

A `scripts/` folder. A new wrapper per client. SSH keys in three places. A README that lies. 2 a.m. fluorescent, hoodie, mug, cables.

Visual: `website/img/nyx-real/desk.jpg`, `lab.jpg`, `lot.jpg`.

What she typed:

```
./geo.sh 1.1.1.1 | tee /tmp/out
CITY=$(jq -r .city /tmp/out)
curl "https://api.example/weather?q=$CITY" | python3 weather_fmt.py
# license? there is no license. the token is in .env.bak
```

## With Kraken

Same woman, slept. Office light. One binary.

Visual: `website/img/nyx-real/office.jpg`, `desk-ok.jpg`.

```
kraken doctor
kraken tentacle add examples/tentacles/geo
kraken tentacle add examples/tentacles/weather-pro
kraken license set weather-pro YOUR_KEY
kraken workflow run examples/workflows/geo-then-weather.yaml
```

## What changed

| Before | After |
|---|---|
| unnamed scripts | tentacle.yaml + contract |
| copy-paste compose | workflow interpolation `$geo.city` |
| token in a bak file | `kraken license set` |
| no doctor | `kraken doctor` |
| rewrite the wrapper | add an arm from another repo |

## Links on this site

- Why: `/#why` and `docs/WHY.md`
- Contract / hooks / workflows: `website/docs.html`
- Courses: `website/courses.html`
- Nyx rules: `docs/NYX.md`
- Examples: `examples/tentacles/`, `examples/workflows/`

## Public article line

Do not write “she was broken and Kraken healed her.” Write: the work was the same; the folder was the problem.
