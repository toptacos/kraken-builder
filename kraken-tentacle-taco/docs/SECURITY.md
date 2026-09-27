# Security

- Ledger under `$KRAKEN_HOME/.kraken/data/taco/` mode `0600`.
- Jail on keys / licenses / catalog.
- No vendor tokens in the ledger.
- `finish` drops token/secret.
- `pulls_vendors: false`.
- Redemption is a local debit, not a card charge.
