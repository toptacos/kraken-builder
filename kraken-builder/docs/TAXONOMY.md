# Taxonomy

Content is tagged so it can be listed without a hand-maintained index. The
registry is data, not prose: `website/data/taxonomy.json` is the single place
taxonomies and terms are declared, and both the static site and the blog
publisher read it.

## The one taxonomy today: `project` — Internal Projects

Every article, page, and post belongs to exactly one project, or none (which
means company-wide). The term is the project's name:

| Term | Project | Content it covers |
|---|---|---|
| `kraken` | Kraken | Core CLI, tentacles, the v1 contract, grants, hooks, benchmarks, the marketing site |

To add a project later: append an object to `terms` in the registry. Nothing
else changes — the site verifier and the blog publisher learn it from there.

## How tagging looks

**On a site page**, in the `<head>` and on `<body>`:

```html
<meta name="taxonomy" content="project:kraken">
<body class="docs" data-taxonomy="project:kraken">
```

**In a blog post payload** (`scripts/publish-journal.sh` builds this), the
term rides along with the existing category and tags:

```json
{
  "title": "...",
  "category": "DevOps",
  "tags": ["kraken", "cli", "homelab", "project:kraken"]
}
```

`project:kraken` is a tag in the blog platform's vocabulary *and* the
authoritative key in this repo's registry — the mapping is the registry, so
the two can never drift apart silently: `scripts/verify_site.py` fails CI if
a page declares a taxonomy term the registry does not know.

## Verify

```bash
python3 scripts/verify_site.py          # links, taxonomy, sitemap
python3 -m pytest tests/test_site.py    # the same checks in the suite
```

Both run on Linux, macOS, and Windows — they are file and JSON checks with no
network and no shell dependency.
