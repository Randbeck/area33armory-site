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
