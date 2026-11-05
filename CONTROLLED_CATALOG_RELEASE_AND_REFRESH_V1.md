# Area 33 controlled catalog release + repeatable approved-only refresh v1

**Development branch**: work/controlled-catalog-release-v1  
**Website status**: NO live deployment, NO GitHub Pages change, NO GoDaddy change, NO published product catalog. Main remains untouched.

## Result

This batch connects the previously built **private approved-only v2 release builder**, **real-site preflight**, **manufacturer-image provenance**, **reviewed withdrawal**, and **text-only product presentation** into a testable release process. It does **not** grant any brand/media rights. The 49 RSR trial records are still **unapproved private drafts** and must not be fed into these publisher/release commands.

### 1. Repeatable approved catalog refresh

\`scripts/refresh_approved_catalog_snapshot.py\` can start with a **previous independently owner-approved, private v2 snapshot**, and:

- Carry forward precisely the previously approved product records, evidence timestamps and original SHA-verified photo bytes. **No per-SKU reapproval of unchanged records is invented.**
- Add or update products ONLY from new, independently owner-approved JSON bundles; the unchanged prior approvals remain from the previously approved snapshot, not from a fresh supplier feed.
- Reject an unapproved draft, changed exact manufacturer/model/variant/category/type under an existing opaque product ID, or different image bytes at an existing public photo URL (cache collision).
- Require reviewed withdrawal evidence for each removed public product ID; retain all other approved records.
- Reject any product or photo hit by current private rights holds.
- Rebuild an atomic private v2 approved-only catalog index, 100-record shards, copied photo assets, private image-provenance ledger and audit. No live pricing/inventory claims, download operations or distribution feed refresh occur.

This is a **reviewed-publication refresh**; it is not yet a direct automatic Randbeck live-feed sync. Live current stock and price still must not be inferred.

### 2. Deny-only media and rights holds

\`scripts/catalog_release_safety.py\` enforces a private owner-maintained ledger of \`image_sha256\`, \`manufacturer_media\`, \`manufacturer_sales\`, and \`catalog_id\` holds. Each hold has an exact target, reviewer-facing reason and date. Media-only holds allow unrelated, independently approved text-only records to remain; manufacturer sales restrictions can block even text listings.

A **rights-hold ledger does not prove an image is licensed**. An empty list is not a manufacturer license. Current rights must be checked independently before any release.

Start from \`examples/area33-private-rights-holds-TEMPLATE.json\`, copy it OUTSIDE Git to a protected folder such as \`C:\Area33-private\area33-rights\`, replace the placeholder owner and review date with actual values, and maintain every actual rights objection there. Do not treat the example as current verified evidence.

### 3. Controlled deployment package and rollback gate

\`scripts/plan_controlled_catalog_deployment.py\` accepts a real, previously verified private Area 33 website preview (from \`scripts/stage_private_catalog_site_preview.py\`), the matching approved private release, current rights-hold ledger, and optional previous approved release.

It verifies the original private approved image-provenance/URLs/hashes, every staged public file, and exact website static files. It then creates a **PRIVATE** package with:

- \`site/\`: only the actual Area 33 public website files and independently approved public records/images.
- \`deployment-plan-private.json\`: approved catalog versions, new/withdrawn counts, full public asset SHA-256 checksums, new immutable image/shard upload steps, index activation LAST, exact obsolete hosted image/shard deletion paths and CDN cache invalidation list.
- \`owner-deployment-authorization-TEMPLATE.json\`: approval FALSE by default, host unconfirmed. A future host-specific deployment procedure must independently verify host, current site revision, owner signoff, current manufacturer rights, MAP and sale restrictions.
- \`rollback-site/\` **ONLY** if the previous approved snapshot passes the **CURRENT** rights-hold ledger. Otherwise the old catalog is not packaged for rollback; e.g. when a manufacturer revoked photo rights, rolling back could reintroduce the prohibited image.

No Git push, server upload, deletion, DNS change, CDN API, SMTP send or production mutation is performed.

\`scripts/rehearse_catalog_cutover.py\` simulates this package on a **temporary private mock host**. It checks all byte hashes, uploads immutable assets first, activates the index last, simulates removing obsolete images/shards, and rehearses rollback only when current rights holds allow it. It does not contact a real host.

### 4. Separate live hosting adapter still pending

The repository has GitHub Pages capability, but the actual deployment destination and live-site revision/hosting chain for **area33armory.com** have **not** been authenticated or verified. GitHub Pages vs GoDaddy DNS/hosting must not be assumed from the Git remote.

Building a real deployment adapter requires confirmed hosting control and explicit owner authorization. A real withdrawal would also require deleting obsolete hosted images, old versioned shard URLs where feasible, and purging caches; merely switching the index is insufficient. No tool created in this batch acts on a live host.

### Safe sequencing once actual product/media rights and publication are approved

All commands operate on private folders. They are NOT useful for the existing unapproved 49 RSR photo drafts.

\`\`\`powershell
$python = "C:\Area33\randbeck-rsr-media-test\backend\.venv\Scripts\python.exe"
$holds = "C:\Area33-private\area33-rights\current-rights-holds.json"
$previous = "C:\Area33-private\your-previous-OWNER-APPROVED-release"
$refresh = "C:\Area33-private\approved-refresh-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$preview = "C:\Area33-private\approved-preview-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$package = "C:\Area33-private\approved-cutover-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$rehearsal = "C:\Area33-private\approved-cutover-test-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

# From a clean isolated checkout of this development branch:
# 1. Preserve unchanged owner-approved records. Add --approved-bundle <file>
#    for independently approved additions/updates or --reviewed-withdrawals
#    <file> when removing previously published product IDs.
& $python .\scripts\refresh_approved_catalog_snapshot.py \`
  --previous-private-release $previous --rights-holds $holds \`
  --out $refresh --stage-private-refresh
if ($LASTEXITCODE -ne 0) { throw "Approved-only refresh rejected" }

# 2. Validate actual Area 33 site with the refreshed approved-only catalog.
& $python .\scripts\stage_private_catalog_site_preview.py \`
  --private-approved-release $refresh \`
  --previous-approved-release $previous \`
  --out $preview --prepare-private-preview
if ($LASTEXITCODE -ne 0) { throw "Private site preflight rejected" }

# 3. Prepare immutable-first activation/deletion and rights-safe rollback plan.
& $python .\scripts\plan_controlled_catalog_deployment.py \`
  --private-preview $preview --approved-release $refresh \`
  --previous-approved-release $previous \`
  --rights-holds $holds --out $package --stage-private-deployment
if ($LASTEXITCODE -ne 0) { throw "Private controlled release plan rejected" }

# 4. Test all byte-for-byte copy/delete/rollback operations LOCALLY only.
& $python .\scripts\rehearse_catalog_cutover.py \`
  --private-release-package $package \`
  --out $rehearsal --rehearse-local-only
if ($LASTEXITCODE -ne 0) { throw "Local release rehearsal failed" }

Write-Host "PRIVATE TEST COMPLETE. NOTHING PUBLISHED."
\`\`\`

### Verification

GitHub Actions runs the original privacy, image, publisher, text-only, withdrawal and website JavaScript tests, plus \`scripts/test_controlled_catalog_release.py\`. The new tests use **synthetic, independently approved** product records and simulated photo rights in temporary test folders, including: prior approval retention, reapproved content changes, newly approved products, no unapproved draft reuse, unchanged-image hashes, changed-photo URL rejection, rights holds, reviewed withdrawal, rollback blocked for revoked media, bad audit rejection, tampered preview and package detection, and no changes to real site's public catalog.

### Launch-critical limits

- A rights hold is a **denial**, not proof of permission. Each genuine public photo must already be authorized.
- No automatic reseller approval, manufacturer copyright permission, live source inventory, accurate current selling price, legal compliance screening, shopping cart, or payment processing is delivered here.
- User/operator must confirm the production hosting provider, credentials, current deployed revision, deployment safeguards and CDN/old-media removal before enabling live publication.
- The current 49 RSR product drafts are private and unapproved. Eleven identity exceptions were held in the trial. Do not bypass them by setting approval flags true.
