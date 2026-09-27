# Token / cost estimate for “implement the whole plan” prompts

A single message that restates architecture, premium tentacle, blog, archive, marketing, and SOC2 is roughly:

| Band | Input tokens | Output tokens | Notes |
|---|---|---|---|
| This session’s typical turn | 25k–80k in | 2k–8k out | Long chat + tool traces |
| “Do everything” mega-prompt | 40k–120k in | 6k–20k out | Wiki + tests + zip |
| Re-run on a fresh laptop with HANDOFF.md | 8k–20k in | 3k–10k out | Tree already unzipped |

SuperGrok / Grok 4.6: treat one mega-turn as on the order of **one heavy research request**, not a cheap chat. Budget **3–8 such turns** to finish DO deploy, real Laravel contact table, and social posts — not one shot.

This file is an order-of-magnitude guide, not an invoice.
