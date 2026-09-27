# Usage

```json
{"v":1,"action":"grant","payload":{"name":"laptop"}}
{"v":1,"action":"listen","payload":{"port":7420}}
{"v":1,"action":"listen","payload":{"tunnel":true}}
```

If cloudflared is installed, run it yourself:

`cloudflared tunnel --url http://127.0.0.1:7420`
