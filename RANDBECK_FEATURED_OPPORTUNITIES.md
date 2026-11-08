# Area 33 — Randbeck Opportunities → Featured Discoveries

## Customer-facing goal
Featured products should make Area 33 fun to explore, whether or not visitors plan to purchase. A featured item can appear on both the homepage and the product counter. Selecting it opens the **same product-aware counter and EVA research experience**.

An internal Randbeck opportunity is NOT permission to advertise. High internal margin, low wholesale price, a distributor email promotion or inferred inventory does not make an item publish-ready.

## Current implementation (draft)

- `assets/featured-public.json`: publish-approved opportunities only, currently **empty**.
- `assets/featured-opportunities.mjs`: strict allowlist, owner approval, exact public product identity, image rights review and freshness/expiry validation. Hidden internal costs or arbitrary extra fields are rejected.
- `assets/featured-opportunities-ui.js`: displays approved entries. If there are none, the homepage/counter displays **clearly labeled editorial research discoveries** instead. They are not claimed as a sale, special price, availability, or actual Randbeck opportunity.
- Cards use actual named public research records and only their separately licensed images; no private distributor photographs or price data.
- Entry navigation carries the selected public product ID into the unified product counter, where Ask EVA provides documented evidence. The current EVA preview is not live Randbeck.

## Intended publishing workflow for an approved opportunity

1. Randbeck flags an internal opportunity using its source freshness, distributor comparison, shipping, rebates, eligibility, landed costs, stock and expected margin. These details remain strictly **internal**.
2. Owner reviews it for public promotion (one-click approval UI in a later back-office integration).
3. Map it to an **approved-for-public exact product/SKU** and verify public specifications and product-media rights. The current demo can only feature its small curated research-reference set; the production normalized catalog adapter is a required next step.
4. Compose a truthful public headline/description that describes why someone might enjoy exploring it. Check manufacturer restrictions, public advertising policies, actual availability and any claimed discount.
5. If displaying a public price, use a **separate** approved quote service with a confirmed Area 33 total: merchandise, applicable taxes, shipping, handling and every Area 33 charge. **Receiving FFL transfer fees are excluded, charged separately by the chosen dealer, and must be disclosed before checkout**. Do not store external dealer fee guesses.
6. Assign a publication expiration time so stale opportunities are withdrawn. Expired or unapproved entries must never show as active promotions.
7. Owner confirms public preview, then publishes through the approved server-side to-public-manifest workflow. No browser or git repository may accept untrusted internal fields automatically.
8. On expiry, stock change, rights withdrawal or owner revocation, remove the public entry immediately and return to generic editorial discovery.

## Public featured record (schema v1)

`assets/featured-public.json` initially has no items. A future OWNER-APPROVED example record has:

```json
{
  "schema": "area33.featured.public.v1",
  "items": [
    {
      "publicId": "feature-approved-example",
      "productId": "ruger-precision-308-gen1",
      "headline": "Explore the precision rifle",
      "description": "A documented research example with one real licensed photograph and relevant educational context.",
      "label": "Featured discovery",
      "ownerApproved": true,
      "productIdentityReviewed": true,
      "publicationRightsReviewed": true,
      "reviewedAt": "2026-11-08T10:00:00Z",
      "expiresAt": "2026-11-10T10:00:00Z"
    }
  ]
}
```

**Illustration only**: this example is NOT in the live manifest and must never be pasted without actual evidence and review. The manifest has **no price field**, because public customer pricing requires a separate authorized quote contract. The initial version supports only known research-product IDs. Later support for all normalized public catalog IDs must be reviewed separately.

## Do not send to the customer site

- distributor purchase costs, supplier contract terms, actual internal gross margin, rebates not publicly eligible, private inventory access credentials, supplier email bodies or private EVA reasoning;
- unpublished or rights-unapproved images, product IDs that are merely suspected to match a UPC, and expired unverified offers;
- a made-up sale price or an estimated receiving FFL fee presented as part of Area 33's collected price;
- personal purchase history, names, location, queries, saved items or browsing details without a separate privacy review and customer authorization.

## Release status

This branch is a **development draft**. It has a working display and validation path, but **no direct authenticated connection to Randbeck opportunity records**, and no operational publisher. Connecting the Executive Suite's Opportunities approval action to an authenticated public-feature exporter is a later backend integration.

Tests: `node scripts/test_featured_opportunities.mjs` (plus the full GitHub Actions suite).
