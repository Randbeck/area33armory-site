# Randbeck -> Area 33 approved-only catalog integration (private development)

Branch: work/randbeck-catalog-bridge-v1. **No changes to Area 33 main, no deployment, no public source images, no customer sale availability or dealer pricing**. The existing approved-only static catalog remains empty.

## Why this is the actual website integration boundary

Randbeck is the source of normalized product/source and media intelligence; Area 33 presents only separately authorized public records. The file scripts/import_randbeck_staging.py converts Randbeck's verified private staging ledger (schema randbeck.area33.private_catalog_staging.v1) to the **existing Area 33 owner review/publishing contract**, not another standalone demo.

- Uses authenticated-in-private original JPEG evidence with checked SHA-256 bytes, full Pillow decode, real dimensions, SKU paths and EXIF check; rejects changes.
- Groups by valid UPC/GTIN + manufacturer + MPN + model, with conflict quarantine for matching UPCs that disagree on identity. Identical exact products become one proposed listing even when multiple source rows exist.
- Retains the original/source-derived category, title and proposed description, and suggests a public type only for explicitly mapped RSR labels. These are **proposals**, not verified specifications or sales claims.
- Generates a stable opaque catalog ID per exact identity using a 32-byte private key stored outside Git; do not lose this key or it will change future product IDs. The key and source UPC never appear in the proposed public record.
- Produces private legacy-compatible catalog-approval-template-part-NNN.json bundles (100 maximum per bundle) so existing owner-review UI and the existing, separately owner-authorized --publish gate may be used later without rewriting them.
- Produces catalog-private-exceptions.json with specific invalid UPC, identity collision, missing verified photo, unsupported source category and other quarantine reasons.
- The bridge does **not** set any of the five required owner approvals, never infers photo rights from supplier distribution and never writes inside the website repository. All templates remain status=draft with approval flags false.
- Adds an optional **owner-reviewed description** field to the actual site publisher, strict public JSON sanitizer, search, product cards and details. It does not include supplier costs/quantities. Existing older records without a description continue to work.
- No live website or publicly exposed catalog is changed by running the bridge. The current approved-only static browser contract still has a 100-item cap; a sharded index or approved-only API will be needed before scaling beyond the initial approved catalog batches. This batch intentionally does not turn 29,935 filename matches into public listings.

The previous pilot verified 101 images across 60 source products (39 products had two technically showroom-sized views). The intake operates on those original bytes and private per-product identity/blocks. Photo technical quality is NOT owner permission, current stock, advertising rights, model/fit accuracy or public availability.

## One consolidated local intake run (Windows PowerShell)

The original Area 33 clone is C:\Area33\area33-catalog-approval-test. Because it may have local modifications, create an isolated **Git worktree** and do not touch its current branch. Replace nothing in existing folders.

```powershell
$ErrorActionPreference = "Stop"
$repo = "C:\Area33\area33-catalog-approval-test"
$clean = "C:\Area33\area33-catalog-integration-test"
$branch = "work/randbeck-catalog-bridge-v1"
if (Test-Path $clean) { throw "Integration test folder already exists; refusing overwrite" }
git -C $repo fetch origin "refs/heads/work/randbeck-catalog-bridge-v1:refs/remotes/origin/work/randbeck-catalog-bridge-v1"
if ($LASTEXITCODE -ne 0) { throw "Git fetch failed" }
git -C $repo worktree add --detach $clean "refs/remotes/origin/$branch"
if ($LASTEXITCODE -ne 0) { throw "Worktree creation failed" }

Set-Location $clean
$python = "C:\Area33\randbeck-rsr-media-test\backend\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Known Pillow-enabled Python environment not found" }

$batch = "C:\Area33-private\rsr-verified-photo-pilot-20261104-174452"
$source = Join-Path $batch "area33-private-catalog-staging.json"
if (-not (Test-Path $source)) { throw "Existing private Randbeck staging is missing" }

$out = "C:\Area33-private\area33-catalog-intake-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$key = "C:\Area33-private\area33-private-catalog-identity-key.bin"
& $python .\scripts\import_randbeck_staging.py --staging $source --batch-root $batch --out $out --identity-key $key
if ($LASTEXITCODE -ne 0) { throw "Private Area 33 catalog intake failed" }
```

The script prints source row/group counts, the number of proposed owner-review drafts and identity/media exceptions. Keep the generated key, JSON and source images private. Do not commit the JSON, move it to public HTML, or run --publish. Do not manually approve all rows because the importer populated source names or images.

## Safety/regression tests

GitHub Actions for this branch runs all existing website privacy/image/publisher Python tests, all static catalog browser/JavaScript tests, and the new test_import_randbeck_staging.py tests. These use synthetic images in temporary private folders only; no RSR credentials or live data are sent to CI. The public assets/catalog-public.json remains unchanged and empty.

## Remaining release steps

1. Decide eligible distributor/category terms and record explicit owner authorization and revocation paths in shared Randbeck Intelligence. Source image-use permissions must be grounded in real supplier agreements.
2. Add bounded recurring source refresh and a held-items queue; clean exact identity and potential fitment mistakes instead of granting unearned evidence to 30,000 SKUs.
3. Build a scalable approved-only paged API or validated static shards and a withdrawal/retraction path (the current static browser is capped at 100 records).
4. Only after authorizations and privacy/security tests pass, have the owner explicitly authorize a separate reviewed release and website deployment. There is no cart, checkout, online pricing or live inventory capability in this integration.
