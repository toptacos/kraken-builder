# berth

Setup tentacle for **TopTaco Kraken**.  
https://kraken.topta.co · hub https://topta.co  
**One binary. Many tentacles.**

Parses `examples/project.yaml` into a shared Docker network plan. Core command: **`kraken up`**. berth does not start containers.

```bash
echo '{"v":1,"action":"plan","payload":{"file":"examples/project.yaml"}}' | python3 handler.py
echo '{"v":1,"action":"up","payload":{"file":"examples/project.yaml"}}' | python3 handler.py
```
