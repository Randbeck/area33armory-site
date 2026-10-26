# Area 33 Armory Website — Product Intelligence Architecture

**Status:** Draft plan (not published). **Source:** Website branch `site-refresh-v1`.  
**Primary goal:** Build a useful, customer-facing research and discovery experience powered by shared Randbeck Intelligence, while preserving operational dealer intelligence as private and not implying unverified inventory or selling prices.

## Current state (October 2026)

- Live `main`: static GitHub Pages under-construction page; `CNAME` points to `area33armory.com`.
- Draft `site-refresh-v1`: responsive informational homepage, contact links, and Product Intelligence introduction.
- Randbeck backend: separate project with normalized product search, supplier evidence, costs and freshness being developed. Its current database contains imported distributor records with known category misclassification and unknown currency/completeness for some source offers.
- **The draft is not a functioning online store**. GitHub Pages cannot safely host the authenticated/private Randbeck backend or store its secrets.

## System boundary

```text
Imported supplier feeds, product reference records
                   |
                   v
         RANDBECK INTELLIGENCE (private services)
        - canonical product identity (UPC / MPN)
        - deduplication and normalized classifications
        - source provenance, freshness and data-quality flags
        - recorded supplier observations (private)
        - business calculations and decisions (private)
                   |
                   v
        PUBLISHING / APPROVAL BOUNDARY
        - only explicit, sanitized public fields
        - no dealer costs, credentials, raw feeds, private notes
        - no unsupported inventory or pricing claims
                   |
                   v
        PUBLIC PRODUCT INFORMATION API (secure host)
                   |
                   v
  AREA33ARMORY.COM (responsive customer-facing website)
        - product discovery and education
        - informational product detail pages
        - clear source/freshness/uncertainty disclosures
        - general contact and service inquiries
```

### Separate data shapes

**Internal source offer**: source/distributor ID; exact UPC where available; cost; promotional terms; recorded quantity; fee estimates; observed timestamp; raw source provenance; authorization scope.

**Canonical product**: durable internal product ID; UPC/MPN; brand and model; product type (complete product vs part/accessory/ammunition); relevant specifications; source-linked aliases; classification confidence; conflicts and gaps.

**Public product** (allowlist only): public ID/slug; name; manufacturer/model; normalized category; verifiable specifications; approved image/description; publication status; optional approved customer-facing values where permitted. **Never serialize private source-offer objects directly to public clients.**

## Practical phases

### Phase 1 — Customer discovery experience (no regulated checkout)

- Rework website information architecture: Home, Explore Products (informational), About, Services, Contact.
- Design discovery UI for desktop/mobile with query, brand, category, product type, and spec filters. Only offer a customer price filter where independently approved public prices are available.
- Product details should state source/freshness and distinguish verified specs from incomplete records; no false `In stock` or `all available` claims.
- Include honest empty/error/loading states. No mock data presented as actual inventory.
- Continue working on the draft GitHub branch; protect live `main`.

### Phase 2 — Shared Randbeck catalog foundation

- Correct category normalization with explicit firearm/part/accessory/ammunition distinction and uncertain classifications.
- Match records by reliable UPC/MPN; keep source provenance, duplicates, observation date and query coverage.
- Expose **paginated public-safe search endpoints**, not direct database access; apply allowlisted fields and server-side filtering.
- Validate multi-business ownership/tenant boundaries before any broader use; current installation-wide source-offer storage is not suitable for public/tenant access.
- Tests: classification false positives, duplicate grouping, filter correctness across all pages, permission isolation, no dealer pricing leaks.

### Phase 3 — Content publishing and quality gates

- A dealer/admin approves specific product pages and public fields.
- Publish only trustworthy public descriptions/images/identifiers and appropriately sourced statuses.
- Disallow contradictory data, old stock observations and generic public reference prices from being treated as confirmed offers.
- Add corrections, expiry and retraction paths; audit what was published and when.

### Phase 4 — Review regulated transaction requirements before commerce

- Do not add checkout or claim that firearms can be bought online until applicable legal requirements, licensing/transfer workflows, merchant processor policies, age/geography restrictions and business operations have been independently reviewed and implemented with suitable providers.
- Public static GitHub Pages must never hold secret credentials or receive internal dealer pricing.
- Treat these as **release gates**, not as assumptions about current compliance.

## Near-term acceptance criteria

1. Public website looks and works well on phone and desktop.
2. Navigation and accessibility tested; correct business contact and claims.
3. Catalog search is honest about source coverage and returns paginated matching public records when an approved API exists.
4. Distributor costs, raw supplier data, account IDs and authentication secrets never appear in the website's public HTML/JS/network responses.
5. No unverified stock/price or `comprehensive inventory` claim.
6. Website and Randbeck repositories remain independent; shared intelligence is consumed through a controlled API.
7. No changes merge into `main` without review.

## Scope and priority

**First useful release:** clean site + informational discovery experience + accurate service/contact details, independent of live commerce.  
**Next:** sanitized public catalog integration after classification and tenant-isolation fixes.  
**Later:** any regulated commerce only once external/compliance dependencies are cleared.

**Operating principle:** Build intelligence once in Randbeck; publish only evidence-grounded, authorized customer information to Area 33.

## Product vision approved October 26, 2026 — beyond the generic storefront

The objective is a **modern, distinctive, useful Area 33 experience**, not another stock distributor template or an endless grid of duplicated products.

**Experience principles:**

- Give visitors ten-second clarity about who Area 33 is and what they can do.
- Make exploration enjoyable through premium visual hierarchy, strong type, clear photography (only licensed/approved), and thoughtful transitions that respect reduced-motion settings.
- Put prominent universal search and guided category exploration near the top, rather than forcing customers through navigation trees.
- Make product details educational: what this item is, verified relevant specifications, how models differ, what is and isn't confirmed, and a sensible next step.
- Separate editorial/educational content from confirmed catalog data. Do not invent product availability, technical facts, review counts, urgency, markdowns, discounts, or customer testimonials.
- Let customers compare supported product specifications side-by-side; unresolved details are identified as unknown rather than filled with guesses.
- Product intelligence should support questions and exploration, but not impersonate a live employee or claim access to data it lacks.
- Preserve brand personality and ease of use on phones; prioritize performance, accessibility, and fast search.

### Example customer journey

1. Visitor lands on confident Area 33 branding and an immediate search/explore entry point.
2. They choose a category or ask a product-focused question.
3. Catalog returns **normalized, properly categorized** public entries with real pagination, provenance/freshness indicators, and filters grounded in verifiable specs.
4. They open product details and an optional neutral comparison/explainer, without public exposure of dealer sources/costs.
5. If a product has an approved real customer offer and validated status, the interface may show it; otherwise provide a general inquiry/availability-check path.
6. Future transactional experience routes through a reviewed processor and lawful fulfillment/transfer workflow, never a mock checkout.

### Integrating Firearms Passport

**Passport is a separate, permissioned product-history experience sharing the product-identity service with Product Intelligence.** It can eventually surface verified manufacturer/model data, service/maintenance records, voluntary updates, and record provenance.

- A product-model identity is not the same as a physical-item identity; distinguish UPC/model catalog data from individual-item identifiers.
- Internal item IDs/QR credentials must be unguessable and authorization-scoped where they grant access.
- No public ownership registry; do not publish owner identity, private serial numbers, personal service details, or regulated records.
- A code/QR scan can open a controlled record or claim workflow, not automatically establish ownership or reveal private records.
- Record entries must identify who supplied the information, how it was validated, and who may read it.
- Passport integration is a later phase; do **not** block the basic website/catalog release on it.

### One platform / payment integration plan

**Single platform architecture**: Area 33 customer website + shared Randbeck intelligence + private dealer operations + future Passport, using modular services and one governed product identity rather than independent duplicated platforms.

**One-fee aspiration is a cost objective, not a promise**: replacing a packaged storefront subscription might reduce overlapping software charges, but compliant payment processing, hosting, transaction charges, banking, tax and possible third-party fulfillment/API costs may remain. Price vendors on complete landed operational cost, not headline percentage.

- Create a processor-neutral order/payment abstraction to avoid making the product catalog dependent on one vendor.
- Never process/store raw card details in custom app code; use a suitable provider's hosted/tokenized payment integration once approved.
- Do not turn on payment, cart, public sale statuses or automatic order promises until processor policy, regulatory/FFL requirements, relevant state restrictions, taxes, fraud handling, availability reservation, cancellation/refund, and fulfillment/transfer procedures are reviewed and implemented.
- GitHub Pages is static hosting; private APIs, credentials, checkout webhooks and order orchestration require a secured backend host.
- Keep one stable order and product ID across website, Randbeck decisioning and customer communication; retain audit logs and idempotency.

### Identity and visual system

Start with **evolution over reinvention**. Evaluate the existing Area 33 logo alongside 2 lightweight concept directions, rather than throwing away established recognition.

- Candidate A: refine existing mark; align proportions, spacing and legibility at small sizes.
- Candidate B: custom geometric `A33` monogram with an A leg integrated with the twin threes, striking in black and white.
- Candidate C: typography-first wordmark `AREA 33 ARMORY` with simplified standalone `33` device.
- Favor timeless black/white/high-contrast typography, disciplined small accent use, strong mobile favicon, and dark/light variants; avoid visually generic shield/target/rifle clip art.
- Test at favicon, mobile header, receipt, engraving and monochrome dimensions.
- Final mark requires user's review of the actual existing logo artwork before choosing a direction; do not treat an illustrative site mark as the approved logo.

### Parallel workstreams and priority

**A. Website UI:** build browsable modern search/catalog experience and information architecture on the draft branch now, separate from public `main`.

**B. Randbeck core:** normalize records and identifiers, introduce public-safe catalog publishing and proper access isolation. Ship backend and website behind an explicit interface contract, with independent tests.

**C. Passport:** document identity/history API and consent/record provenance; prototype later after reliable product identification.

**D. Commerce:** evaluate processor and workflow requirements later, with no provider commitment or checkout work that blocks the discovery release.

**E. Branding:** gather existing logo file and prepare/refine concepts early so subsequent web UI is not repeatedly reskinned.

**Success means:** one coherent brand and shared data foundation, a distinctive usable website before e-commerce, and clean interfaces to add Passport and approved commerce without rebuilding the catalog.

