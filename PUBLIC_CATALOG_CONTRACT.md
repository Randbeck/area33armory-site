# Area 33 public discovery handoff — stage 1
Status: **development contract only**. No production API is connected, and this is not a promise of current coverage.

## Current experience
- `explore.html` presents six clearly labeled editorial learning paths. They are **not** fictitious product records.
- Live filtering, accessible guide expansion and honest missing-data messaging work without an API.
- Approved red-33 white-on-black SVG wordmark is reused. No product images are presented without rights and exact-identity proof.
- Home navigation leads into discovery. Main/production remains out of scope.

## Proposed Randbeck public API
A secured publication process must explicitly approve every public field; never put distributor feeds or credentials into static JS.

`GET /v1/public/products?q=&category=&product_type=&brand=&cursor=&limit=`
Response shape:
```json
{
  "items": [{
    "id": "public-opaque-id",
    "slug": "stable-public-slug",
    "manufacturer": "Approved manufacturer",
    "model": "Approved exact model",
    "variant": null,
    "category": "normalized-category",
    "product_type": "complete|part|accessory|ammunition|other",
    "specifications": [],
    "evidence": [{"source_label": "Approved source", "checked_at": "ISO-8601"}],
    "images": [{"url": "approved-url", "alt": "specific alt", "rights": "approved"}],
    "publication_updated_at": "ISO-8601"
  }],
  "next_cursor": null,
  "coverage": {"description": "Scope of approved published records, not all distributor inventory"},
  "as_of": "ISO-8601"
}
```
**Example keys and strings above are schema illustrations, not real product data.** Cursor must paginate across the server-side filtered result set. A missing `next_cursor` means no more *published matching* records, not universal completeness.

## Security and release gates
1. Publish via strict field allowlist; reject internal offer, cost, margin, account, private notes, raw feed and credential fields. No direct distributor or internal API endpoints in the browser.
2. Validate tenant/business ownership and authorized publication for every record, including linked media.
3. Verified exact UPC/MPN and variant association before showing model photos. Record source, rights, last checked, display priority, and useful alt text. If missing, use an explicit image placeholder.
4. Source provenance/checked dates and classification confidence must survive sanitization. Ambiguous classifications are reviewed, not treated as confirmed.
5. Render loading, error, zero results, end-of-page, stale data and partial coverage honestly.
6. Add end-to-end tests for pagination with filters, false-positive category matches, cross-tenant leaks, private-price leaks, image rights and retracting previously approved records.
7. Validate actual customer-facing claims/contact, accessibility and mobile experience; do not publish until owner approves.
8. Payment, stock confirmation, regulated checkout, Passport and dealer tools remain separate gated stages.

## Future integration seam
A subsequent stage can add `assets/public-catalog.js` (client-only public read calls) and catalog card/detail components after the API passes the gates above. Keep editorial topics independent of real product search; never silently substitute local examples for a failed catalog request.
\n\n## Stage 2 development interface\nSee `CATALOG_STAGE_2.md` for the implemented catalog preview, its explicit disabled API configuration and the remaining publication/security gates.\n