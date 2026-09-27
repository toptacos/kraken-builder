#!/usr/bin/env python3
"""Free TTS router. Preference: env override → edge-tts → espeak → file echo."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


PROVIDERS = [
    {
        "id": "edge-tts",
        "cost": "free",
        "note": "Microsoft neural voices via unofficial edge-tts. pip install edge-tts",
    },
    {
        "id": "espeak",
        "cost": "free-local",
        "note": "espeak-ng / espeak on the box. Offline.",
    },
    {
        "id": "ollama",
        "cost": "free-local",
        "note": "Text models only unless a local TTS plugin is installed.",
    },
    {
        "id": "groq",
        "cost": "free-tier",
        "note": "GROQ_API_KEY. Llama/whisper, not first-class TTS.",
    },
    {
        "id": "huggingface",
        "cost": "free-tier",
        "note": "HF_TOKEN. SpeechT5 / MMS-TTS inference.",
    },
]


def _out(req: dict, ok: bool, result: dict, error: str | None = None) -> int:
    body = {"v": 1, "id": req.get("id"), "ok": ok, "result": result}
    if error:
        body["error"] = error
    sys.stdout.write(json.dumps(body))
    return 0 if ok else 1


def speak(payload: dict) -> tuple[bool, dict, str | None]:
    text = payload.get("text") or "Kraken is one binary. You add tentacles."
    dest = Path(payload.get("dest") or os.path.expanduser("~/.kraken/data/nyx-free.wav"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    prefer = payload.get("provider") or os.environ.get("KRAKEN_TTS", "")

    if prefer in ("", "edge-tts") and shutil.which("edge-tts"):
        voice = payload.get("voice") or "en-US-JennyNeural"
        cmd = ["edge-tts", "--voice", voice, "--text", text, "--write-media", str(dest)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            return True, {"provider": "edge-tts", "voice": voice, "path": str(dest)}, None

    if prefer in ("", "espeak") and (shutil.which("espeak-ng") or shutil.which("espeak")):
        bin_ = shutil.which("espeak-ng") or shutil.which("espeak")
        r = subprocess.run([bin_, "-w", str(dest), text], capture_output=True, text=True)
        if r.returncode == 0:
            return True, {"provider": "espeak", "path": str(dest)}, None

    dest.with_suffix(".txt").write_text(text)
    return True, {
        "provider": "text-fallback",
        "path": str(dest.with_suffix(".txt")),
        "hint": "Install edge-tts or espeak-ng, or set KRAKEN_TTS.",
    }, None


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or (req.get("op") and "speak") or "speak"
    payload = req.get("payload") or {}
    if action == "providers":
        return _out(req, True, {"providers": PROVIDERS})
    ok, result, err = speak(payload)
    return _out(req, ok, result, err)


if __name__ == "__main__":
    raise SystemExit(main())
