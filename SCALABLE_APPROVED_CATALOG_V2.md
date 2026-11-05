# Area 33 scalable approved-only catalog v2 — **development only**

**Branch:** work/scalable-approved-catalog-v2 (based on the working Randbeck to Area 33 private media intake). Never deploy/merge this branch to production without separate owner approval. Main and the live public site remain unchanged.

## Verified project status

The owner's private pilot processed 60 RSR products and produced 49 owner-review drafts after preparing 96 private lossless EXIF-cleared image copies. Eleven identity groups remain in the exception queue. Source rights, sale eligibility, stock freshness and public publication approvals remain **false**. These 49 drafts are *not* input to a public release.

The initial site browser allowed only 100 owner-approved static product records in one v1 manifest. That format is too small for a distributor-scale catalog. Randbeck retains internal source/product intelligence and costs; Area 33 must serve only independently authorized public records.

## Implemented in this branch

1. **Safe private release builder:** scripts/prepare_approved_catalog_shards.py validates each 1–100-item *already fully owner-approved* private bundle via the site's existing strict publisher, never guesses rights or changes an approval, and prepares a private staged release in a fresh folder. Explicit \`--prepare-private-release\` is required. It does not write to the site checkout, GitHub public assets or the live site.
2. **Scalable static index:** release output \`assets/catalog-index.v2.json\` lists minimal approved-only searchable summaries; \`assets/catalog-shards/<release-id>/part-0001.json\` etc contains up to 100 approved records per shard. Index can describe up to 50,000 approved records in 500 shards; this is a data-contract cap, not a claim that the website can host that many media files efficiently. Shards have SHA-256 checksums and strict same-origin paths.
3. **Actual website reader:** assets/catalog.js attempts the v2 approved-only index. If it is absent (HTTP 404), the existing empty/approved-only v1 catalog continues unchanged. If v2 is malformed or shards fail checksum or schema, the catalog **fails closed** instead of showing unapproved data. When valid, it searches **all** approved public summaries locally and loads only the detailed shards needed for 12-result pages. Filters preserve the complete searchable approved set; no three-result shortlist limitation.
4. **Existing privacy gates retained:** the browser validates every loaded item through the existing allowlisted approved catalog sanitizer; same-origin image URLs, source evidence date, rights markers, unique opaque product IDs, and prohibited private fields are checked. Public cards show only approved descriptions. Source dealer costs, SKU, private file paths, quantities and credentials never appear.
5. **Withdrawals:** a new approved release is a FULL replacement snapshot. If a previous v2 index is supplied, removed IDs must be explicitly listed in a private withdrawal file with reviewer, reason and review date. Previous release files are not edited; keep them for rollback until a separate deployment process is approved. This is not an automatic retraction or live recall system.
6. **No implicit site updates:** the Git branch contains code and tests, not an active \`assets/catalog-index.v2.json\` full of supplier inventory, and not distributor images. The real 49 drafts remain private/unapproved.

## Synthetic, automated verification

- Python test \`scripts/test_prepare_approved_catalog_shards.py\` stages 205 SYNTHETIC fully approved products across three 100-item shards, checks SHA-256/image integrity and privacy, blocks unapproved records, tests cross-bundle duplicate IDs and explicit withdrawal audits. All images are generated locally for testing, not RSR.
- JavaScript \`scripts/test_catalog_shards_contract.mjs\` validates 205 SYNTHETIC approved summaries, page 98–109 across shard boundaries, a late product search without losing results, category filters, SHA tampering, off-origin paths, unapproved images and leaked private keys.
- The full existing Area 33 public-site Python and Node regression suites run unchanged in CI on this development branch.

## Safe, meaningful next work

The website-side approved-only catalog reader is infrastructure, not live inventory access. It cannot and must not turn the 29,935 RSR filename matches or the 49 drafts into public listings by assumption. Next build/source-verify a **shared Randbeck source/category policy authorization service** that records real distributor terms, image use constraints (including transformation restrictions), categories, owner authorization, evidence provenance, freshness and explicit withdrawals/revocations, and exports only demonstrably eligible product-for-sale records. Cross-distributor exact UPC/MPN identification and landed-cost intelligence stay PRIVATE in Randbeck. Then validate a controlled production release separately, with supplier-specific stock policies and serving/caching capacity.

## Example: synthetic-only tests, not a publication command

    py -m unittest discover -s scripts -p "test_*.py" -v
    node scripts/test_catalog_static_contract.mjs
    node scripts/test_catalog_shards_contract.mjs

The private builder's options are:
\`--bundle <private, genuinely owner-approved JSON>\` (repeatable),
\`--out <new private folder>\`, and \`--prepare-private-release\`. For a
full-snapshot replacement, add \`--previous-index <existing public v2 index>\` and
\`--withdrawal-file <reviewed private removals>\` whenever prior IDs disappear.

**Do not run the builder on the current 49 draft templates or set their approval booleans to true merely to pass tests.** Those records must await evidence of actual source rights, exact identity, sale listing authorization, and owner approvals.
