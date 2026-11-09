# LZ 33 — Landing Zone 33 / Promotional Experience V1

**Brand direction (working):** LZ 33 — *Where the best deals land.*  
**Homepage:** Today's Landing (one approved featured offer); Just Landed (other approved offers, without duplication).  
**Production status:** Draft only. No public deal, inventory, price or outbound email is connected or published. No final trademark clearance has been completed.

## No redundant homepage calls to action

The former large hero reference photo is removed and its above-the-fold space is assigned to LZ 33. The hero CTA to the immediately adjacent deal section is removed. The additional landing section collapses to a short honest status line when there are no approved offers; no giant repeated placeholder box.

The existing catalog, category cards, EVA side counter, and full product research experience remain in place. An approved landing opens the right-hand product counter in place when available.

## One guarded public source for the entire promotion

1. `assets/deals-public.json` remains the **only** public promotion manifest, currently `{"schema":"area33.deals.public.v1","items":[]}`.
2. `assets/deals-public-contract.mjs` retains the existing explicit approval gate: exact public product ID, owner approval, rights review, product review, current verified stock and public offer, terms approval and finite date window. No private dealer costs/wholesale margins.
3. `assets/lz33-campaign.mjs` selects the **first** eligible public record as Today's Landing and filters same-product duplication out of Just Landed. Other records stay in original approved publisher order. No model-generated savings or ranking is inferred.
4. `assets/featured-opportunities-ui.js` populates hero, Just Landed and a **non-sendable** owner email preview from the same already-validated in-memory selection. The public endpoint is fetched only once. Receiving FFL fees remain separate from Area 33 seller charges.
5. Owner-only draft email preview is hidden by default and exposed on this draft using `?area33_lz33_owner_preview=1`. This URL switch is **not authorization**; there are no private prices or mailing functions in the browser. A future real campaign creator must have server-side authenticated owner access, subscriber permission, suppression/unsubscribe controls, terms and inventory rechecks, and human send approval. Never build it as an open public page.

## Evidence and limits

- No approval record: headline says a landing is pending; Just Landed is a single line. No product imagery, made-up pricing or purchase link.
- Approved record: the exact reviewed product is shown with offer terms; a destination-specific delivered quote is still required. Receiving FFL's separately assessed transfer fee is excluded and prominently disclosed.
- No source snapshot or rights review: the record cannot pass the public manifest validator.
- Email previews are never mailed; `lz33CampaignDraft(...).publishable` is always false.

## Validation

`node scripts/test_lz33_campaign.mjs` and `node scripts/test_deals_departments_eva.mjs` cover public-only feed selection, no duplicate product, safe empty state, owner approval and expiry requirements, unsent preview and no extra redundant sections. Entire site validation: see GitHub Actions for draft PR #9.

## Before owner publication

- Complete USPTO and marketplace name-clearance for LZ 33 / Landing Zone 33; current name is provisional.
- Implement an authenticated *server-side* owner campaign workflow; never use an insecure URL flag for live administration.
- Supply and verify an actual distributor-backed, sourceable, owner-reviewed product and exact destination quote, rights-cleared image, restriction review and offer terms.
- Rerun stock, terms, catalog identity and destination compliance validation immediately before offer publication and any fulfillment.
- Avoid duplicate homepage sales blocks or an unreviewed countdown timer; do not label marketing copy “unbeatable” without substantiation.

No changes are being made to the live `main` branch or area33armory.com in this draft.
