# inlet

TopTaco Kraken tentacle. **One binary. Many tentacles.**

Loopback control-plane UI for the reef. Optional `cloudflared` tunnel after a device is granted.

This arm does **not** run host commands, open a shell, or treat `api.topta.co` as a remote-admin channel. The device roster is local (`0600`). Tokens are shown once on `grant` and omitted from `devices`.
