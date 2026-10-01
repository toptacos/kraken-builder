package main

import (
	"encoding/json"
	"os"
)

func main() {
	var req struct {
		ID      any            `json:"id"`
		Payload map[string]any `json:"payload"`
	}
	_ = json.NewDecoder(os.Stdin).Decode(&req)
	name := "world"
	if req.Payload != nil {
		if n, ok := req.Payload["name"].(string); ok && n != "" {
			name = n
		}
	}
	out := map[string]any{
		"v": 1, "id": req.ID, "ok": true,
		"result": map[string]any{"arm": "hello-go", "lang": "go", "hello": "hello, " + name},
	}
	_ = json.NewEncoder(os.Stdout).Encode(out)
}
