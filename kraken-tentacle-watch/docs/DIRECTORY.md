# Introducing watch to the Kraken web directory

See the shared plan: `../../KRAKEN_DIRECTORY_PLAN.md` (sibling of this repo in the artifacts tree) or the copy in this file.

## Catalog payload

`schemas/catalog.json` is the record `POST /api/kraken/catalog/register` expects (`docs/PUBLISHING.md` in kraken-builder).

## Website files to add in kraken-builder (do not invent a second catalog)

1. `website/catalog/tentacles/watch.html` (or the generator that reads `schemas/catalog.json`)
2. Link from `/catalog/tentacles`
3. Keep blurb ≤ 140 chars, same voice as geo/filesort
4. Install line only: `kraken tentacle add <git-url>`

Human review is required before api.topta.co promotes a row.
