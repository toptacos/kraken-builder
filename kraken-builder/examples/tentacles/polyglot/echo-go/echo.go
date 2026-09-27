package main

import (
	"encoding/json"
	"io"
	"os"
)

func main() {
	raw, _ := io.ReadAll(os.Stdin)
	if len(raw) == 0 {
		raw = []byte("{}")
	}
	var req map[string]any
	_ = json.Unmarshal(raw, &req)
	out := map[string]any{
		"v": 1, "id": req["id"], "ok": true,
		"result": map[string]any{"arm": "echo-go", "lang": "go", "action": req["action"], "echo": req["payload"]},
	}
	enc, _ := json.Marshal(out)
	os.Stdout.Write(enc)
}
