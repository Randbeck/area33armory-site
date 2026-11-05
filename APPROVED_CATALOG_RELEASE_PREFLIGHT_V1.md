# Area 33 approved-only release preflight and actual-site preview

**Development branch:** `work/approved-catalog-release-preflight-v1`

## Purpose

Bridge the gap between a **PRIVATE owner-approved catalog release** and the **ACTUAL Area 33 site** without publishing unapproved data. This batch is not a product-source license, distributor feed, seller authorization, deployment mechanism or live stock tool.

This comes after the image-provenance/withdrawal, text-first, and sharded-catalog branches. It preserves those features. The Area 33 production website and main repository branch remain unchanged.

## What was implemented

`scripts/stage_private_catalog_site_preview.py` takes a staged approved-only v2 release produced by `scripts/prepare_approved_catalog_shards.py` (or a separately reviewed rights-withdrawal release).

It checks:
- The full previous release's approved products, private photo provenance, exact image hashes, public IDs, index/shard consistency and shard body checksums.
- An owner-approved builder audit or a reviewed rights-withdrawal audit whose version and counts match the proposed catalog; neither may claim deployment.
- Exact reviewed withdrawal evidence whenever a prior approved release loses a product ID.
- That the existing site fallback public catalog remains empty, rather than combining a new v2 index with unknown records.
- Only the exact website static HTML/JS/CSS/SVG/public JSON files explicitly allowlisted for a preview may be included.

It builds a new private folder:
- `<out>/site/catalog.html` and the existing real Area 33 HTML/pages/assets, unchanged.
- `<out>/site/assets/catalog-index.v2.json`, approved-only 100-record shards, and only verified public photo files.
- `<out>/preflight-private-report.json` (OUTSIDE the served site) with counts, versions, the approved index checksum, added/withdrawn IDs, obsolete hosted media paths, and human release checks.
- No dealer costs, RSR data, image permission documents, private media-provenance audit, local source-image paths, keys, inbox data or credentials are copied into the served site.

`scripts/serve_private_catalog_preview.py` serves that `site` folder **only on 127.0.0.1**, with directory listings disabled and caching disabled. It cannot deploy, rewrite a production directory or expose internal audits; it does not start automatically.

There are no new public products and no new public image rights. Existing 49 RSR product drafts remain unapproved; 11 identity exceptions remain held. **Do not pass those drafts to the approved-only release builder** or mark their approval flags true just to get a catalog preview.

## Consolidated use — AFTER you genuinely have approved product bundles

From a clean, isolated clone of this staging branch, with a known Pillow-enabled Python interpreter:

```powershell
$python = "C:\Area33\randbeck-rsr-media-test\backend\.venv\Scripts\python.exe"
$approved = "C:\Area33-private\reviewed-catalog-owner-approved.json" # genuine owner-approved bundle
$release = "C:\Area33-private\catalog-release-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$preview = "C:\Area33-private\catalog-site-preview-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

# Validates a fully approved owner-review bundle. Will reject the current 49 drafts.
& $python .\scripts\prepare_approved_catalog_shards.py `
    --bundle $approved --out $release --prepare-private-release
if ($LASTEXITCODE -ne 0) { throw "Approved private release failed" }

# Copies the REAL site + verified approved public records to an isolated private folder.
& $python .\scripts\stage_private_catalog_site_preview.py `
    --private-approved-release $release --out $preview --prepare-private-preview
if ($LASTEXITCODE -ne 0) { throw "Private release preflight failed" }

# Opens the actual site on 127.0.0.1:8765. Browser URL /catalog.html. Ctrl+C to stop.
& $python .\scripts\serve_private_catalog_preview.py `
    --preview-root $preview --port 8765 --serve-private-preview
```

When releasing a replacement that removes existing approved products, use `--previous-index` and a fully reviewed `--withdrawal-file` with the approved-only release builder; pass `--previous-approved-release` to the private preflight as well. Otherwise the release cannot silently remove an old product.

## Release engineering decisions still needed

1. Validate current manufacturer media rights and online sale eligibility for each actual product. Supplier access/RSR image notices, attribution statements or an absence of complaints do NOT grant image reproduction rights.
2. Decide web hosting deployment and an owner-authorized, separate upload/activation workflow. No cloud/server credentials were used or changed here.
3. Design CDN/host old-image deletion, browser caching, media rights withdrawal emergency procedures and rollback safeguards. A new index without removing obsolete image URLs is NOT an effective live takedown.
4. Prove production performance and cache behavior for the intended record count before publishing a distributor-scale catalog; the static v2 contract's 50k max is a format bound, not demonstrated capacity.
5. Confirm product sale eligibility, relevant FFL restrictions, MAP/manufacturer channel policies, and freshness of stock/price claims. This catalog intentionally makes **no current stock, price, or ecommerce/checkout claims**.

## Automated coverage

`scripts/test_private_catalog_site_preview.py` uses locally generated images and synthetic owner-approved/test inputs to test:
- Actual website + two allowed presentation modes on localhost
- No private rights/photo/price/source-file leakage to the served site
- SHA integrity of approved shards/photo copies and site isolation
- Failure for unapproved source records and tampered shards
- Reviewed prior-product withdrawal and obsolete-media removal planning
- Rejection of altered withdrawal evidence
- Prevention of rights-withdrawal release preview without its previous approved snapshot

Full existing Python and JavaScript website test suite runs on this branch. Test fixtures do not represent actual Area 33 product approval.
