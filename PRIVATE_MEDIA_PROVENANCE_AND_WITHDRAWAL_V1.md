# Area 33 private image provenance and rights-withdrawal workflow

**Branch:** work/private-media-withdrawal-v1. Development branch only. Main, live site, uploaded website assets and the 49 RSR pilot image drafts remain untouched and unapproved.

## Why

RSR's manufacturer image disclaimer puts image-rights responsibility on dealers and says RSR cannot sublicense manufacturer photos. An attribution notice and responsive takedown procedure do not substitute for rights. This batch creates a practical way to REMOVE or isolate affected imagery once an issue is identified, not a license to publish uncertain images first.

## Implemented

- When preparing a private v2 release from genuinely approved owner-review bundles, `scripts/prepare_approved_catalog_shards.py` writes `catalog-private-media-provenance.json` **outside public assets**, alongside the private staged release. It maps exact public catalog ID, manufacturer, presentation mode, owner-recorded rights source, public image URL and original verified photo SHA-256. An image used by multiple products is linked to every relevant opaque product ID. Text-only records have empty image arrays; no source image is fabricated.
- `scripts/stage_private_media_withdrawal.py` reads that private provenance and every previous approved shard. It verifies signed-by-hash shard body integrity, product-to-index consistency, old approved photo bytes, and source SHA-256 mapping before creating a new **private** full replacement release.
- A reviewer can target **exact original-image SHA-256** (every listing using those bytes, even across brands), or an **exact manufacturer** (by default only the brand's photo listings). With explicit `--include-text-only`, a broader manufacturer sales restriction can remove its approved text-only listings too.
- The resulting private output contains a new complete approved-only v2 index and shards, only retained approved photos, a new private provenance ledger, a reviewed-withdrawal file compatible with the existing catalog removal audit schema, and a private audit with removed public product IDs.
- The tool does not grant new rights, change descriptions, auto-convert photos to text-only, alter the prior release, overwrite an existing directory, deploy a website or purge a CDN. It refuses unknown image hashes/manufacturers, tampered image bytes, stale/mismatched staged release files, missing provenance, invalid reviewer and missing review dates.
- On the public site *development branch only*, an image or attribution concern link in exact product details opens the contact page's `Image or trademark rights` topic with the validated opaque public product ID. The site still opens a draft in the visitor's own mail client; it does not silently send or store personal data.

## Tests

`scripts/test_private_media_withdrawal.py` covers multiple brands using the same photo hash, manufacturer-scoped removal, separate text-only eligibility, opt-in removal of text-only records, tampered shards/bytes, missing provenance, no-match refusal, repeated withdrawals, and unchanged old release/live-site files. The complete pre-existing image/text-only catalog regression tests also run on this branch.

## IMPORTANT: production takedown is a separate owner-controlled deployment

This tool only stages a PRIVATE replacement snapshot. An actual live rights withdrawal requires someone with deployment authorization to switch the public site to the replacement index, **remove any previously hosted disputed image files and old versioned shards**, and **invalidate relevant CDN/browser cache paths** wherever supported. Copying the new index without removing old hosted images is NOT a complete takedown. Rollback must never inadvertently re-enable revoked rights. Build an approved deployment + purge adapter before relying on this for an actual live notice.

## Example private command, after an existing approved v2 release exists

These are illustrative names only, NOT a request to publish the existing 49 unapproved drafts.

    python scripts/stage_private_media_withdrawal.py \
      --previous-private-release <previous-private-approved-v2-release> \
      --out <brand-new-private-withdrawal-folder> \
      --image-sha256 <SHA256-of-the-affected-source-photo> \
      --reviewer "Area 33 owner" \
      --reason "Rights holder requested image withdrawal" \
      --reviewed-on YYYY-MM-DD \
      --stage-private-withdrawal

For an entire manufacturer photo collection, substitute `--manufacturer "<exact manufacturer name>"` for the hash. Do not add `--include-text-only` unless the restriction also affects selling/listing the manufacturer's products without images.

**No live catalog has been populated, no real RSR photos approved, and no supplier/manufacturer image rights are implied by this system.**
