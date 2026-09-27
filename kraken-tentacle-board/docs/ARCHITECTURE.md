# How board was built

Same contract as watch/marks: protocol v1, stdin JSON, no `kraken.core`.

The dashboard is assembled from panel collectors and painted with box-drawing characters. Interactive TUIs (Textual, Bubble Tea) would own stdin; Kraken already owns stdin for the envelope, so `open` returns a frame string.

## Jev

Official `examples/tentacles/jev-ai` is JSON path edit + Ollama/llama.cpp. board embeds the same path algebra (`get/set/delete/merge`) so `apply` works without that tentacle installed, and will call `kraken run jev-ai infer` when `ai.backend: jev-ai`.

Kev is treated as the same family (typed local inference). No closed API.
