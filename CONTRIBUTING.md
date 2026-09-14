# Contributing

1. Keep core lean: JSON in → policy → exec → JSON out.
2. Tentacles live in `examples/tentacles/<name>/` with `tentacle.yaml` + handler. Do not import `kraken.core` from a tentacle.
3. Suckers are named hook rows in `examples/suckers/`.
4. Default deny: add a grant before exposing scourge, remote_config, tunnel, llm, expose.
5. Bind `127.0.0.1` unless `docker-env` sets `public: true`.
6. Run `PYTHONPATH=. python3 -m pytest tests/test_notes_tunnel_llm.py tests/test_expose.py tests/test_scopes_ca.py tests/test_panel.py tests/test_scourge_grant.py tests/test_suckers.py -q`.
7. Never commit `~/.kraken/keys`, licenses, or `.env`.
