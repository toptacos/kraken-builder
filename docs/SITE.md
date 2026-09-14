# kraken.topta.co

Public marketing + catalog. Admin stays noindex.

## Pages

- `/` hero, install one-liner, two tentacles demo
- `/docs` this tree
- `/tentacles` catalog (starts as static markdown)
- `/pricing` free core, paid plane TBD
- `/brand` logos

## Stack for the site (later)

Laravel + FrankenPHP on Vercel or a small VPS. Postgres when accounts exist. Until then, static pages in `site/` are enough.

## SEO

Index `/`, `/docs`, `/tentacles`. Noindex `/app`, `/billing`, `/admin`.

## Launch post

Silence until a public binary exists. Then one post: “Kraken is a single binary that runs tools from any repo.”
