# Full plan

## Bet

People and agents need one local executable that can grow tools without rewriting the core. Tools live in other repos and speak JSON.

## Smallest slice that already exists

Python `kraken` CLI + two in-process tentacles + `.kraken` merge + contract helpers + tests.

## Target shape

- kraken-core: one binary per OS. Discovers `.kraken`, runs tentacles, notifies.
- Control plane: Laravel + FrankenPHP + Postgres at kraken.topta.co.
- Tentacles: any language to one binary + tentacle.yaml.

## 30 / 60 / 90

- 30: public GitHub repo, kraken init, external binary invoke, docs site stub.
- 60: Docker multi-arch core, first remote tentacle from a second repo.
- 90: catalog + decide if a paid plane is real.
