# Free models and APIs

Kraken core stays offline. Premium tentacles may call a network; free tentacles default to local or no-key public APIs.

## Voice (Nyx)

Do **not** require ElevenLabs.

| Provider | Cost | How |
|---|---|---|
| Grok Voice connector | included with Grok | scratch Eve track already in `website/media/nyx-scratch.mp3` |
| edge-tts | free | `pip install edge-tts` — Jenny/Aria neural |
| espeak-ng | free local | `apt install espeak-ng` |
| Piper / Coqui | free local | ship a model file with the tentacle |
| Hugging Face TTS | free tier | `HF_TOKEN` + SpeechT5 / MMS |
| Fish Audio / Cartesia | free trial | later, optional |

```bash
kraken tentacle add examples/tentacles/voice-free
echo '{"v":1,"action":"speak","payload":{"text":"The machine stays yours."}}' \
  | kraken run voice-free speak
```

Env: `KRAKEN_TTS=edge-tts|espeak`. Output: `~/.kraken/data/nyx-free.wav`.

## Text / planning

| Provider | Cost | Use |
|---|---|---|
| Ollama | free local | user already runs this; `ollama run llama3.2` |
| Groq | free tier | `GROQ_API_KEY` — Llama/Mixtral |
| OpenRouter free | free models | `:free` suffix |
| Hugging Face Inference | free tier | `HF_TOKEN` |
| GitHub Models | free preview | `GITHUB_TOKEN` |

Never bake keys into tentacle.yaml. Read `~/.kraken/keys/env` or the process environment.

## Images / video

Site stills are already generated. Further frames: Grok Imagine (this session) or local SD/Comfy. No paid Runway/Kling required to ship the landing page.

## Rule

A tentacle that needs a paid key is `license: premium`. A tentacle that works with Ollama / edge-tts / espeak is `license: free`.
