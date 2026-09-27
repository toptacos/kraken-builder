# Launch checklist

1. Tag `v0.1.0`.
2. Point `schemas/catalog.json` `source` at the public git URL.
3. `POST /api/kraken/catalog/register` with `license: free`.
4. Site page `/catalog/tentacles/board`.
5. Commands on the page: `kraken tentacle add <url>` then `kraken run board init`.
