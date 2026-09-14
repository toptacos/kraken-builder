# kraken.topta.co

Live marketing is the Vue SPA (`toptaco-monorepo/applications/kraken`). `website/` is brand kit + archive. Canonical paths have no `.html`.

## Pages

- `/` hero, install, catalog slice
- `/cli` install + demo + Homebrew
- `/use-cases` homelab / Pi / consultant
- `/docs` contract
- `/catalog/tentacles/:name` long-form for geo, filesort, expose
- `/blog` journal (six posts)
- `/changelog` 0.1.1
- `/register` tentacle listing
- `/pricing` free core; Scourge on profile.topta.co

## SEO

Index `/`, `/docs`, `/cli`, `/catalog/*`, `/blog/*`, `/use-cases`. Noindex `/keys`, `/admin`. Prerender on `npm run build`.

## Launch post

`Kraken CLI is a local plugin runner. Not the exchange. curl … | sh then kraken demo.`
