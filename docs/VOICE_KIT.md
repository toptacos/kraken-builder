# Nyx voice kit (reuse)

All tracks are Eve, English, informational. Source files live in
`website/media/voice/` and are copied to `brand/voice/` for handoff.

Do not pitch-shift these. If you need a new line, generate Eve again.

| File | Use | Rough length |
|---|---|---|
| `intro.mp3` | Project introduction (hero) | ~36s |
| `pitch.mp3` | Short why-buy pitch (Nyx strip) | ~32s |
| `why.mp3` | Full why section | ~40s |
| `why-local.mp3` | Reason: local first | ~28s |
| `why-any-language.mp3` | Reason: any language | ~26s |
| `why-not-saas.mp3` | Reason: not another SaaS | ~25s |
| `why-compose.mp3` | Reason: compose, don't rewrite | ~27s |
| `why-privacy.mp3` | Reason: payloads stay on the box | ~27s |
| `why-indie.mp3` | Reason: solo / product | ~27s |
| `why-ops.mp3` | Reason: ops / jump host | ~27s |
| `install.mp3` | Install + doctor | ~48s |
| `examples.mp3` | Walks every example command | ~69s |
| `product.mp3` | Product / typed term | ~39s |
| `licenses.mp3` | Premium keys | ~38s |
| `courses.mp3` | Course overview | ~42s |
| `before-after.mp3` | Before page story | ~27s |
| `beta.mp3` | Beta form | ~19s |
| `../nyx-scratch.mp3` | Original 20s briefing | ~20s |

Catalog JSON: `website/media/voice/catalog.json`

Reuse: drop `src` on any `<audio class="voice-inline">`. Same files for social, courses, ads.
- Tutorial tracks: tutorial-dev.mp3, tutorial-secure.mp3 [2026-09-10]
