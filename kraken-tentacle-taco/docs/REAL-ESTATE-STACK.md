# Real estate tech stack (2026) and where taco sits

Not a CRM. Not an MLS client. Inbound events only.

## Layers offices actually buy

| Layer | Job | Names you will hear |
|---|---|---|
| MLS / listing feed | Copyrighted listing compilation | Local board MLS; transport is **RESO Web API** (RETS is deprecated) |
| IDX / site | Public search + lead capture | AgentFire, Placester, Lofty sites, BoldTrail sites |
| Lead vendors | Paid inquiries | Zillow, Realtor.com Connections |
| CRM | Follow-up and pipeline | **Follow Up Boss**, **Lofty** (ex-Chime), **BoldTrail** (ex-kvCORE), Sierra, Wise Agent |
| Transaction / compliance | Contract to close, audit | **Dotloop**, **SkySlope**, Brokermint, Open to Close |
| E-sign / forms | Association forms | Often bundled in Dotloop / SkySlope DigiSign |
| Back office | Splits, trust, books | Lone Wolf, Brokermint + QuickBooks |
| Dialer / ISA | Speed-to-lead | CallAction and similar |
| Glue | Zapier, RealSynch, API Nation | FUB ↔ Dotloop is a common paid sync |

Solo / small team default in US writeups: Follow Up Boss + an IDX site + Dotloop or SkySlope + mileage/books. Brokerages add BoldTrail or Lofty when they want site + CRM + PPC in one invoice. Salesforce shows up only when they already have an ops person. 

Sources: industry stack roundups for 2026 (CRM/TM names), RESO on Web API vs RETS.

## How data is allowed to move

- Listing content is an MLS license, not a public API you scrape.
- RESO Web API is the transport; gateways (Trestle, Spark, MLS Grid, Bridge) sit in front of many boards.
- CRM APIs (Follow Up Boss is the usual example) accept **leads in**. They are not a thank-you ledger.

Taco must not pull MLS, IDX, or CRM. A Zap on “deal stage = closed” can POST `{"action":"event","payload":{"user":"sam","kind":"custom","note":"closed"}}`. That is the whole integration.

## Where taco fits

After the close and beside peer cover shifts — not in the lead waterfall.

```
Zillow/Realtor → CRM → showing → Dotloop/SkySlope → close
                                              ↓ Zap (optional)
                                         taco event (local)
```

Custom kinds a broker-tech lead can set: `listing_live`, `offer_in`, `closed`, `cover_shift`. Caps stay in policy. Chat remains `/kraken taco @sam`.

## Who to sell

Broker or team lead who already opens a terminal or already pays Zapier. Not the agent living only in Lofty’s phone app.

## Do not build

- RESO client
- Follow Up Boss competitor
- SkySlope checklist clone
- Commission calculator
- IDX site
