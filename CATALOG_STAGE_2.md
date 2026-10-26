# Stage 2 — Customer Catalog UI (development only)

## Delivered
- Separate `catalog.html` with premium black/white/red identity, product search form, category/type/manufacturer filters, large image-ready cards, detail dialog, accessible source labels, comparison of up to three products, and cursor-based pagination.
- `assets/catalog.js` never manufactures product records. With its endpoint set to `null`, it renders an explicit not-connected notice, rather than fabricated inventory or an endless spinner.
- Client projects only the public product fields it needs, escapes all untrusted content via `textContent`, and accepts only `https:` image URLs individually marked `rights: "approved"`. Unapproved or broken images display a placeholder.
- No checkout/cart, stock claim, price, supplier cost, supplier URL, private login, Passport data or backend key is included.
- Built for an eventual audited Randbeck publication endpoint; do not enable the endpoint until reviewed.

## API work required before enabling
1. Release sanitized, tenant-isolated and explicitly approved `/v1/public/products` response with stable cursor pagination and filter parameters (`q`, `brand`, `category`, `product_type`, `limit`, `cursor`). Return source coverage and `next_cursor`.
2. Return `specifications: [{label,value}]`, `evidence:[{source_label,checked_at}]`, and `images:[{url,alt,rights:"approved"}]`; maintain exact UPC/MPN/variant linkage server-side.
3. Add a real categories/facets endpoint, filtered by publication policy. The current category select intentionally has only the All option; this must not be populated with guessed categories.
4. Enforce media-domain allowlisting, CORS policy, CDN safety controls and cache expiry on the server. Client `rights` markers are presentation checks, *not* authorization.
5. Add server-side contract and privacy tests; browser accessibility and visual regression tests; empty/timeout/pagination/stale-data tests; explicit owner approval to publish.

## Manual review steps
Open `catalog.html` on a local static server or a private preview deployed from `site-refresh-v1`. The unavailable-catalog message should show and no catalog API request should occur. Check desktop/mobile navigation, search/filter focus, contrast, text scaling and image placeholders before connecting live data.
