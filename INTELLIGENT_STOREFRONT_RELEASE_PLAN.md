# Area 33 Intelligent Storefront — Initial Connected Experience (Development Draft)

## Goal

Area 33 must be **a place people love browsing**, not a conventional product-grid website with an AI chatbot bolted on. Public shopping basics must remain clear and quick. Customer experiences live in a single connected journey: **Discover → Inspect → Compare → Ask EVA → Explore accessories → Understand one Area 33 delivered price**.

This draft builds directly on the existing six-direction photo counter, accessory evidence and brand/model research. It deliberately **does not** merge or deploy to the main site.

## What is working in this draft

| Capability | Implemented scope |
| --- | --- |
| Discovery-first homepage | Prominent one-click entrances to the integrated product counter, embedded EVA, Your Firearms Expert and price-readiness explanation. Existing informational routes retained. |
| Discovery Engine | Search across all curated manufacturer research references, filter by firearm category, surprise-me exploration, deep links to the *same* counter. No three-item shortlist restriction. |
| Product counter | The original real-photo viewer, available-angle selection, zoom/pan, locally temporary photo previews, product sources and manufacturer-aware accessory wall remain in place. |
| Known variant exploration | Explicitly grouped related research references (including G19 Gen5 versus factory MOS; distinct Ruger Precision examples), with careful warnings about caliber, generation, SKU and optics interfaces. Color availability not invented; exact current variants not asserted. |
| Comparison | Up to three real research reference products, with actual documented facts, caveats, source data and explicit unknown inventory/price. |
| Save for this visit | Save/remove research models *in memory for the current open page*, no account, cookies, network or persistent browser storage. |
| Embedded EVA expert preview | Open-ended question entry and suggested questions tied to current product, selected accessories and comparison context. **Deterministic evidence-based responses only**, with manufacturer source links; NOT connected to Randbeck live LLM or business data yet. |
| Area 33 delivered-price foundation | Local-only destination ZIP with blockers for sourceable exact SKUs, applicable tax, shipping, handling and all other Area 33 charges. Receiving FFL transfer fees are explicitly excluded. No transfer-fee directory, collection or guessing. **Never displays a guessed total.** |
| Data separation | Public manufacturer references only. No internal dealer costs, distributor tokens, live checkout or inventory/price claims; no user data stored or submitted. |

### User experience design principles

- **Enjoy looking:** visitors can spend time discovering products without a forced cart, account or purchase.
- **One workspace:** model selection in the Discovery Engine updates the same Counter, EVA and Area 33 delivered-price readiness area. Comparison and saved research models remain accessible.
- **Real product identity:** every published image must identify its exact approved product and view. Never turn a photo of one SKU into another SKU's color or angle.
- **An EVA expert that knows what is on the counter:** current product and selected accessories are shared as public ID-only context; sources and unknowns are visible.
- **Area 33 delivered prices:** a guaranteed customer quote must represent the exact amount Area 33 will collect (product + confirmed accessories + applicable taxes + shipping/handling + all other Area 33 charges) for a verified delivery destination, quote validity and fulfillment path. The independently collected receiving FFL transfer fee is **excluded and disclosed before checkout**. Until then show `AREA 33 PRICE PENDING`.
- **Optional imagination:** the separate existing concept-studio route can later be integrated as a distinct concept mode with explicit illustrative labeling and independent physical-fit validation; no AI-generated imagery masquerades as actual variant photography.

## Engineering boundary: what is NOT working yet

The existing `REFERENCE_PRODUCTS` array is a *small research sample*, **not** the integrated distributor catalog or verified current inventory. The site cannot truthfully claim to display every product/finish/color without a public approved normalized catalog feed.

The customer EVA preview is a non-networked, deterministic research preview. To connect real Randbeck Intelligence, build a **server-side public-query adapter**, not a direct browser connection to internal business data or OpenAI keys. It should:

1. Validate public product identity with normalized records and explicit variant grouping from exact maker identifiers and source UPCs.
2. Read only publish-approved product names/descriptions/images/specifications and rights grants.
3. Look up compatible accessories by exact product/variant, source documentation, date, confidence and any required physical verification.
4. Return constrained public answers with citations, uncertainty and expiry/freshness; keep all dealer costs, credentials and private supplier notes server-side.
5. Rate-limit anonymous guests and implement safety, abuse, legal, security, age, and privacy controls appropriate to the storefront. No chat transcript should reach distributor systems.
6. Support a complete authorized catalog search with honest pagination and `show all matching products` without silent truncation.

A future **public Area 33 delivered-price quote service** also requires an authenticated source-aware server bridge that computes and verifies:
- exact product SKU and condition/variant; actual sourceable stock and freshness;
- selected real accessory SKUs, quantities, compatibility evidence and missing mounting components;
- customer destination, shipping restrictions, fulfillment method and serviceability;
- taxes and any location-specific charges;
- shipping, handling, any applicable Area 33 payment charges, and an explicit notice that receiving-FFL transfer charges are excluded;
- product and accessory rights/pricing/MAP presentation constraints;
- total customer-facing price, quote expiration and price-guarantee policy;
- private distributor comparison, fees and gross margin **never exposed to visitors**.

The receiving FFL sets and collects its own transfer fee; Area 33 **does not track, collect, guess, include, or promise** that fee. Any 'one-price' claim must say explicitly that this independent charge is excluded. The browser helper's `allInQuoteStatus` is **readiness logic**, not a payment processor or security boundary.

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
2. Connect a secure Randbeck public-response adapter to the embedded EVA expert for genuinely flexible product-aware conversations, source-backed recommendations and current evidence.
3. Connect and verify the Area 33 delivered-price quote service with explicit receiving-FFL fee exclusion, applicable taxes, inventory and fulfillment eligibility.
4. Only then extend the optional AI concept studio, mapped back to sourceable real product SKUs and labeled as non-physical illustrative visualization.

## November 8 refinement — EVA, price exception, featured opportunities

- Customer-facing assistant is **“Ask EVA — Your Firearms Expert”**, powered by shared Randbeck Intelligence. This branch retains offline evidence-based research replies; the secure live EVA service is not connected yet.
- The planned headline price is **Area 33 Delivered Price**: real merchandise and selected accessories plus applicable tax, shipping, handling and every other Area 33 charge, quoted for a verified delivery destination. The buyer's receiving FFL may charge a separate transfer fee. **That fee is not included**, and no fee list is requested or stored here. Never present the Area 33 delivered price as the customer's entire out-of-pocket firearm acquisition cost.
- `assets/featured-public.json` is the **approved public feature manifest**. It starts empty. An actual Randbeck Opportunity does not become public advertising until a separate owner approval step checks identity, rights, product availability, editorial claims, and any pricing/MAP rules. `assets/featured-opportunities.mjs` enforces a small allowlisted, expiring, approval-gated schema. Both homepage and counter show clearly marked **research discovery** cards if no public opportunities have been approved.
- No supplier costs, internal opportunity signals, private business intelligence or unapproved media are exposed in the public feed. Real-time selection and publication from Randbeck require a server-side and editorial workflow (details in `RANDBECK_FEATURED_OPPORTUNITIES.md`).

## Homepage information architecture refinement — November 8

Owner feedback: "Firearms worth exploring" and "Something worth a closer look" were redundant. Make the first merchandising section **Featured Deals & Specials**, make the next **Shop by Department**, and **explain who EVA is before the question input**.

**Implemented**
- Homepage hierarchy: compact firearm hero → **Featured Deals & Specials** → **Shop by Department** (Pistols, Rifles, Shotguns, Suppressors, Optics, Accessories) → category-selected results and the existing lower-page service information. The duplicate editorial research highlight card grid is no longer displayed as a second homepage section. The full-size counter still has its separate clearly labeled research highlights.
- Department cards reveal an initially hidden browser-filtered research gallery, preserving the right-side inspection counter for firearm models. Optics/accessories display manufacturer research records and source links rather than silently passing accessories off as firearms. Suppressors have no approved public product records and show a clear non-availability/coming-catalog state rather than invented SKUs.
- **Deals must be real.** `assets/deals-public.json` begins empty and the homepage displays a clearly labeled empty state until a reviewed public offer exists. `assets/deals-public-contract.mjs` allows only owner-approved, public-product-verified, rights-reviewed, inventory-verified, terms-verified, expiring promotional entries. It does not accept raw Randbeck Opportunities or internal supplier economics. Final destination-based Area 33 delivered pricing remains a separate verified quote; receiving FFL transfer fees are excluded.
- EVA's side counter now explains: "EVA is Area 33's virtual firearms expert..." including what she can explain, that she knows the current selection, and that live Randbeck AI is **not connected** to this preview. The full-page counter also introduces EVA above the question area.
- Tests: `scripts/test_deals_departments_eva.mjs` plus existing site, side counter, publishing, photo and customer experience regressions.
- Current state: **development draft only**. No real verified deals, public distributor feed, live EVA backend or payment/fulfillment system connected; no live site publication.

## Customer feedback — retail design and Catalog route repair (November 8)

Owner observed: the browsing flow was improving, but still looked "a little amateur"; clicking **Catalog** appeared to lead mainly to Experience Lab rather than a firearms catalog.

**Findings and changes**
- The published catalog feed `assets/catalog-public.json` is genuinely empty. The previous `catalog.html` showed search controls and a 'catalog not connected' placeholder as its main content, plus prominent alternate experiment links, with **no actual browsable manufacturer research collection on that page**. This was confusing.
- `catalog.html` now puts an actual searchable **manufacturer-reference gallery** FIRST, backed by the separately labeled `REFERENCE_PRODUCTS` research data and the exact-identity Creative Commons photo manifest. Search by brand, model, or description; filter pistols/rifles/shotguns; inspect a product via a right-side native dialog, and open exact research IDs with EVA on the home side counter.
- This gallery is **not** the approved distributor catalog and shows no sourceable stock, fabricated prices, invented photographs, or questionable exact SKU claims. The original authorized `assets/catalog.js` approved-listings mechanism remains beneath it and will take precedence for real sellable catalog items once the publisher is connected.
- Experimental 'Experience Lab' is no longer in the primary Catalog navigation. Customers can explore a real reference collection without being pushed into experiments.
- Introduced `assets/retail-finish.css` and `assets/catalog-research.css`: clean black/white/neutral design with restrained red accents, less visual noise, smaller navigational emphasis, a clearer editorial product hero, consistent spacing and buttons, more legible department tiles and a right-hand inspector that shares the retail design.
- Product cards with separately licensed photographs sort first in unfiltered browsing. Missing images remain text-only with intentionally styled manufacturer labels—never a picture of a similar firearm or an unverified distributor image. This improves the draft but does **not** replace the need for authentic, authorized product photography across the eventual catalog.
- Tests include `scripts/test_retail_catalog.mjs`, existing catalog rights checks, all website route tests and the new side-counter deep-link support.
- This is still **draft only**: no real complete distributor feed, live customer pricing, checkout or secure live EVA integration. Manual visual and accessibility checks on desktop and phone remain required before publication.
