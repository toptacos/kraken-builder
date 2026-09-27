# taco — game plan

Premium TopTaco arm. Currency is the **taco**. Instance owner writes the policy.

## Loop

1. A check happens off-box (GitHub action, GitLab job, chat bot, human).
2. That system posts an **inbound event** to Kraken: `{"action":"event","payload":{"user":"ada","kind":"pr"}}`.
3. Policy converts the kind into tacos.
4. Ada redeems from the instance catalog.

Kraken does not crawl GitHub, GitLab, AWS, or Google. Those tools push. If they cannot push, they do not score.

## Default checks

| kind | default tacos | intended source |
|---|---|---|
| `pr` | 3 | merged PR webhook |
| `loc` | 1 / 100 lines | CI annotation you send |
| `security` | 8 | closed vuln / dependabot you attest |
| `taco` | 1 | peer grant, cap 5/day |
| `custom` | policy | anything the owner adds |

## Rewards

Owner lists `{id, cost, title}` in policy. Redemption subtracts balance. Fulfillment is off-box (sticker in a drawer, lunch card). This arm is not a storefront and does not talk to Amazon checkout.

## Integrations (push only)

GitHub / GitLab / Google Chat / Slack-like / AWS Code* — each is a **channel name** in policy. A workflow on that side formats the Kraken envelope. Tokens for those vendors stay in *their* CI, not in taco's ledger.

https://api.topta.co may list the premium tentacle. It is not the scoreboard. Product: TopTaco at https://kraken.topta.co.

## Limits and rules

```json
"limits": {"taco": {"per_hour": 3, "per_day": 5}, "pr": {"per_day": 20}}
"rules": [
  {"id": "deny_self", "type": "deny_self"},
  {"id": "kinds", "type": "allow_kinds", "kinds": ["pr","taco","security"]},
  {"id": "hours", "type": "hour_window", "start": 8, "end": 20}
]
```

`peer_cap_per_day` still sets the taco daily cap. `hour_window` is UTC.

## Abuse

- Peer cap per hour and per day.
- No self-give.
- Events are append-only locally; owner can `clear`.
- Do not score on lines deleted-only without a policy override.
- Security tacos require a human or signed bot event, not a raw scanner dump.
