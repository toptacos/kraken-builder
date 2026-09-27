#!/usr/bin/env bash
exec python3 -c '
import json, sys
req = json.loads(sys.stdin.read() or "{}")
print(json.dumps({"v":1,"id":req.get("id"),"ok":True,"result":{"arm":"echo-sh","lang":"bash","action":req.get("action"),"echo":req.get("payload")}}))
'
