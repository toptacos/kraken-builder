# Brand strategy — Kraken under Topta

## Verdict

Do **not** invent a second company identity. Treat Kraken as a **product sub-brand** of Topta.

- Parent: Topta (platform, API, billing, trust).
- Child: Kraken (local binary, tentacles, Nyx, abyss).
- Engineering can share Vue + `api.topta.co`. Visual language should **not** be a clone of other topta.co product pages.

A full rebrand of Topta around tentacles would dilute every other product. A full split (“Kraken Inc.”) is premature: licenses, domain, and API already sit on Topta.

## Why the look can diverge

Other Topta surfaces are tools. Kraken is a creature-system. The abyss photo, glow-K, and Nyx are the product’s memory. That is a legitimate sub-brand palette, not a strategy change.

| Layer | Topta parent | Kraken sub-brand |
|---|---|---|
| Domain | topta.co / api.topta.co | kraken.topta.co |
| Color | whatever the house uses | ink `#0B1220`, teal `#2FD0C6`, foam |
| Human | corporate / product leads | **Nyx Hale only** |
| Motion | UI-functional | scroll wakes the arm |
| Voice | platform English | short, technical, no myth dump |

## Spokesperson reuse

Nyx is a **character lockup**, not a staff photo.

Use her on: Kraken site, explainer, X/YouTube, premium tentacle pages, beta emails.

Do not use her on: generic Topta invoices, DPI work, other product homepages. Mixing her into the parent brand makes Kraken look like the whole company.

Reusable kit lives in `website/brand-kit/nyx/` — stills, avatar, scratch VO. Replace the scratch track with a cloned voice before paid ads; do not ship Eve-as-Nyx as the final voice.

## Site motion (this pass)

- Photo tentacles start nearly gray and colorize with scroll (`--awake`).
- SVG arm still draws; suckers latch.
- Logo breathes on the hero, tightens in the sticky nav.
- Active nav item follows the section in view.

Vue stays a thin shell so it can later sit next to other Topta SPAs on the same API without forcing those SPAs onto abyss backgrounds.

## Do not

- Do not use the crypto-exchange Kraken mark or orange.
- Do not put Nyx in a different haircut per channel.
- Do not grayscale-to-color the docs pages; keep docs quieter.
- Do not rebuild Topta’s global nav in tentacle chrome.
