# Archives (unzip order)

| Zip | What |
|---|---|
| kraken-handoff.zip | Full tree slice (CLI, tests, site, older media) |
| kraken-scourge-pack.zip | panel + scourge + grants |
| kraken-launch-pack.zip | LAUNCH, SEO, SOCIAL, prompt |
| kraken-media-pack.zip | Brand guidelines, SEO playbook, video index, kit-2026, instruction shorts |

On the laptop:

```
unzip kraken-handoff.zip
unzip -o kraken-scourge-pack.zip
unzip -o kraken-launch-pack.zip
unzip -o kraken-media-pack.zip
cd kraken-builder && export PYTHONPATH=$PWD
```

Then `docs/PROMPT_LAPTOP.md`.
