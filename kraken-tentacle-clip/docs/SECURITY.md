# Security

- No HTTP client. Offline by design.
- No Facebook token. No unofficial downloader.
- Store: `$KRAKEN_HOME/.kraken/data/clip/clips.json` mode `0600`.
- Rejects `file:` and paths under `keys/` / catalog / topta.
- Copyrighted video bytes stay on Facebook. We only keep the URL you typed.
