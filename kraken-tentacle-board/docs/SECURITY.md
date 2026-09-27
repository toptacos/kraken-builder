# Security

- `apply` needs `.kraken/grants/apply` or `KRAKEN_BOARD_APPLY=1`.
- `apply` writes only inside the project (`file`) or `.kraken/data/board/workspace.json`.
- AI URLs must be `http(s)://127.0.0.1|localhost|::1`. Cloud hosts fail closed.
- `KRAKEN_OFFLINE=1` never opens a socket.
- No keys in `board.yaml`. Do not point at `~/.kraken/keys`.
- Terminal panel does not attach a PTY.
