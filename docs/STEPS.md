# Steps (archive)

## Done in this working tree

1. Lean Python core: load in-repo arms, queue, CLI.
2. Tentacles `echo` and `pi-host`.
3. JSON stdin/stdout contract helper.
4. Hierarchical `.kraken` discovery and merge.
5. Tests, Dockerfile, Actions workflow, wiki, v5 prompt.
6. Plan for FrankenPHP + Laravel control plane + Postgres.
7. Brand and site copy.

## You run once GitHub create is allowed

```bash
cd kraken-builder
python3 -m pip install -e . -r requirements-dev.txt
make e2e
gh repo create mmcachran/kraken-builder --public --source . --remote origin --push
git checkout -b feature/kraken-core-tentacles
git push -u origin feature/kraken-core-tentacles
```

## Device install (target)

```bash
curl -fsSL https://kraken.topta.co/install.sh | sh
kraken init          # writes ~/.kraken/{config.yaml,data,logs,tentacles}
cd your-project
mkdir -p .kraken && cp ~/.kraken/config.yaml .kraken/config.yaml
# edit overrides
kraken list
kraken run echo ping
```

## Next engineering slices (order)

1. `kraken init` CLI wired to `ensure_user_layout`.
2. Exec external binaries from merged `tentacles:` list.
3. FrankenPHP+Laravel skeleton for `kraken serve` + site.
4. Postgres only when the control plane has users.
5. Cross-compile core with Docker.
6. Catalog page on kraken.topta.co.
7. Optional Stripe after a paid tentacle exists.

## Do not do yet

- Call DigitalOcean (no connector).
- Compile Laravel into each tentacle.
- Require network for local `kraken run`.

## Done this session (slice 2)

- `kraken init` writes ~/.kraken layout
- `kraken list` / `run` resolve in-process arms and config binaries
- Repo `.kraken/config.yaml` registers `echo-bin`
- Control-plane PHP health + catalog + Postgres schema (deferred)
- Site PHP front controller + CSS
- Install stub and Makefile e2e including php health
