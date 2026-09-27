# OAuth installer (plan only)

Taco does not complete Slack/Google/Teams OAuth against those vendors from inside Kraken.

`oauth` writes the *app ids you already created* and prints the vendor install URL.

```json
{"v":1,"action":"oauth","payload":{"vendor":"slack","client_id":"W123"}}
```

Then create the Slack/Google/Teams app in *their* console and point the slash command at a loopback receiver:

`python3 bots/loopback.py slack 7421`

Do not paste client secrets into the ledger. Put them in keeps.
