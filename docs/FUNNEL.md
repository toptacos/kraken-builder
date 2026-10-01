# Funnel (opt-in)

Default: `KRAKEN_OFFLINE=1` — no events.

If unset and https://api.topta.co/v1/telemetry/kraken exists, POST only:

`install_ok | demo_ok | second_cmd | arm_add | d7_return`

Fields: `version`, `platform`, `error.code`. No argv, no paths, no project names.

Hub: path + logged_in + product_click only.
