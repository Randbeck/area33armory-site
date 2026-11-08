# Area 33 Intelligent Storefront — Initial Connected Experience (Development Draft)

## Goal

Area 33 must be **a place people love browsing**, not a conventional product-grid website with an AI chatbot bolted on. Public shopping basics must remain clear and quick. Customer experiences live in a single connected journey: **Discover → Inspect → Compare → Ask → Explore accessories → Understand one all-in price**.

This draft builds directly on the existing six-direction photo counter, accessory evidence and brand/model research. It deliberately **does not** merge or deploy to the main site.

## What is working in this draft

| Capability | Implemented scope |
| --- | --- |
| Discovery-first homepage | Prominent one-click entrances to the integrated product counter, embedded Thinking Room and price-readiness explanation. Existing informational routes retained. |
| Discovery Engine | Search across all curated manufacturer research references, filter by firearm category, surprise-me exploration, deep links to the *same* counter. No three-item shortlist restriction. |
| Product counter | The original real-photo viewer, available-angle selection, zoom/pan, locally temporary photo previews, product sources and manufacturer-aware accessory wall remain in place. |
| Known variant exploration | Explicitly grouped related research references (including G19 Gen5 versus factory MOS; distinct Ruger Precision examples), with careful warnings about caliber, generation, SKU and optics interfaces. Color availability not invented; exact current variants not asserted. |
| Comparison | Up to three real research reference products, with actual documented facts, caveats, source data and explicit unknown inventory/price. |
| Save for this visit | Save/remove research models *in memory for the current open page*, no account, cookies, network or persistent browser storage. |
| Embedded Thinking Room preview | Open-ended question entry and suggested questions tied to current product, selected accessories and comparison context. **Deterministic evidence-based responses only**, with manufacturer source links; NOT connected to Randbeck live LLM or business data yet. |
| All-in price foundation | Local-only ZIP and receiving-dealer name/transfer-fee acknowledgement, with explanatory blockers for sourceable exact SKUs, dealer fee, applicable tax, shipping, handling and all other charges. **Never displays a guessed total.** |
| Data separation | Public manufacturer references only. No internal dealer costs, distributor tokens, live checkout or inventory/price claims; no user data stored or submitted. |

### User experience design principles

- **Enjoy looking:** visitors can spend time discovering products without a forced cart, account or purchase.
- **One workspace:** model selection in the Discovery Engine updates the same Counter, Thinking Room and all-in readiness area. Comparison and saved research models remain accessible.
- **Real product identity:** every published image must identify its exact approved product and view. Never turn a photo of one SKU into another SKU's color or angle.
- **A Thinking Room that knows what is on the counter:** current product and selected accessories are shared as public ID-only context; sources and unknowns are visible.
- **Actual all-in prices:** a guaranteed customer quote must represent the final amount (product + confirmed accessories + applicable taxes + shipping/handling + agreed receiving FFL fees + any other required charges) for a defined ZIP, dealer, price validity and fulfillment path. Until then show `ALL-IN PRICE PENDING`.
- **Optional imagination:** the separate existing concept-studio route can later be integrated as a distinct concept mode with explicit illustrative labeling and independent physical-fit validation; no AI-generated imagery masquerades as actual variant photography.

## Engineering boundary: what is NOT working yet

The existing `REFERENCE_PRODUCTS` array is a *small research sample*, **not** the integrated distributor catalog or verified current inventory. The site cannot truthfully claim to display every product/finish/color without a public approved normalized catalog feed.

The customer Thinking Room is a non-networked, deterministic research preview. To connect real Randbeck Intelligence, build a **server-side public-query adapter**, not a direct browser connection to internal business data or OpenAI keys. It should:

1. Validate public product identity with normalized records and explicit variant grouping from exact maker identifiers and source UPCs.
2. Read only publish-approved product names/descriptions/images/specifications and rights grants.
3. Look up compatible accessories by exact product/variant, source documentation, date, confidence and any required physical verification.
4. Return constrained public answers with citations, uncertainty and expiry/freshness; keep all dealer costs, credentials and private supplier notes server-side.
5. Rate-limit anonymous guests and implement safety, abuse, legal, security, age, and privacy controls appropriate to the storefront. No chat transcript should reach distributor systems.
6. Support a complete authorized catalog search with honest pagination and `show all matching products` without silent truncation.

A future **public all-in quote service** also requires an authenticated source-aware server bridge that computes and verifies:
- exact product SKU and condition/variant; actual sourceable stock and freshness;
- selected real accessory SKUs, quantities, compatibility evidence and missing mounting components;
- customer destination, shipping restrictions, fulfillment method and serviceability;
- taxes and any location-specific charges;
- shipping, handling, any payment fees and confirmed receiving FFL transfer charges or Area 33 coverage;
- product and accessory rights/pricing/MAP presentation constraints;
- total customer-facing price, quote expiration and price-guarantee policy;
- private distributor comparison, fees and gross margin **never exposed to visitors**.

Receiving FFL charges imposed independently by another dealer cannot be guaranteed unless covered or contractually confirmed. Never print “everything included” as a binding offer when a fee is unknown. The browser helper's `allInQuoteStatus` is **readiness logic**, not a payment processor or security boundary.

## Media work needed

The Ruger Precision Rifle .308 Generation 1 remains a *one-photo* licensed research reference, with no directions certified left/right/top/bottom/front/rear. The six-view manifest currently has no publish-approved directional records. See `SIX_VIEW_COUNTER_MEDIA_AND_RELEASE.md` for exact product and rights steps.

## Validation and preview

- CI: `scripts/test_customer_experience.mjs`, `scripts/test_six_view_counter.mjs`, existing privacy/rights/catalog and site regressions.
- Before preview, extract the latest `work/area33-intelligent-storefront-v1` branch into a **separate** folder; don't mix it with `C:\Area33\randbeck-platform` or a previously extracted build.
- From PowerShell, locate the page and run the server from its directory (see PR instructions).
- Preview `six-view-counter.html`, beginning from the new homepage's **Enter the Area 33 experience** button.
- Test desktop and mobile browser manually before approval. Automated contract tests do not prove layout quality, working third-party images or current publication permissions.
- **DRAFT ONLY. No production merge or publication without owner review.**

## Next cohesive development batch after visual approval

1. Ingest real *approved-for-public* distributor product records, normalize product family/variant/finish and exact UPC while keeping rights and dealer costs separated. Add complete paginated customer discovery.
2. Connect a secure Randbeck public-response adapter to the embedded Thinking Room for genuinely flexible product-aware conversations, source-backed recommendations and current evidence.
3. Connect and verify the final all-in quote service with receiving-FFL fees, applicable taxes, inventory and fulfillment eligibility.
4. Only then extend the optional AI concept studio, mapped back to sourceable real product SKUs and labeled as non-physical illustrative visualization.
