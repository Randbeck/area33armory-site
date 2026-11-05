# Area 33 text-first, image-rights-safe catalog path (private branch)

Development branch: work/rights-safe-text-catalog-v1, based on the previous distributor/manufacturer rights branch. All new features are isolated; the website's live deployment, main branch, and public catalog manifest remain unchanged.

## Why this exists

RSR's source-image notice says manufacturer logos, images, and IP belong to the manufacturers, and that RSR has no authority to sublicense them. A photo downloaded from FTP or displayed elsewhere on the internet does not by itself authorize Area 33 to use it. The original 60-product sample yielded 49 private image review drafts and 11 identity exceptions; **the 49 products have not been cleared for public image use**.

Rather than forcing every eventual product listing to carry licensed RSR artwork, Area 33 now supports explicitly **text-only public product records**, with no embedded image or fake image placeholder. Verified brand/model names are descriptive product facts, but original copy, accurate fit/variant, sale eligibility, and other applicable restrictions still require owner review before any record becomes public.

## Implementation

- The source bridge scripts/import_randbeck_staging.py accepts `--text-only-drafts`. It never reads/opens/downloads/copies source images, and outputs `photos: []`. It intentionally blanks the distributor-sourced description, sets `listing_mode: text_only` and `content_origin: ""` (owner must explicitly attest later), and leaves all five approval flags FALSE. Exact GTIN/manufacturer/MPN/model exceptions still quarantine questionable products.
- The private owner review page scripts/build_private_catalog_review.py supports images=[] and an explicit `Owner-written and verified` copy origin. The photo-rights approval is disabled/false for text-only items; the other four independent checks remain required. A product offered for sale is a separate real-world owner decision, not inferred from distributor presence.
- The strict server-side approved-only publisher requires text-only mode, exactly zero photos, rights_source empty, content_origin=owner_written, media_rights FALSE, and owner_publication, exact_identity, content_review, and offered_for_sale all TRUE. Image listings retain the image rights and source-photo integrity checks. There is no text-only shortcut into rights-based photographs.
- The public browser sanitizer requires explicit presentation_mode=text_only for images=[], otherwise it rejects the record. It still rejects private SKUs/costs/source filenames, unapproved images, remote assets and unexpected properties.
- Area 33's actual public catalog cards show a clean typographic product profile in place of imagery; search, filtering, comparison, details, and approved-only sharded pagination work with mixed image/text products.
- The v2 private full-replacement release builder accepts mixed, independently approved photo and text records and copies zero image bytes for text-only items.
- Product marketing descriptions copied from RSR, a manufacturer website, or other stores must NOT be included in a text-only public record unless their text reuse rights are independently established. The importer supplies a blank description to prevent automatic content copying.

## One consolidated private sample review on Windows

This does not publish products; it creates private review drafts and an offline browser review page for verified identity candidates.

```powershell
& {
    $ErrorActionPreference = "Stop"
    $worktree = "C:\Area33\area33-catalog-integration-test"
    $branch = "work/rights-safe-text-catalog-v1"
    if (-not (Test-Path $worktree)) { throw "Existing isolated website worktree not found" }
    $changes = git -C $worktree status --porcelain
    if ($LASTEXITCODE -ne 0 -or $changes) {
        throw "Worktree has local changes; refusing to overwrite"
    }
    git -C $worktree fetch origin "refs/heads/${branch}:refs/remotes/origin/${branch}"
    if ($LASTEXITCODE -ne 0) { throw "Fetch failed" }
    git -C $worktree switch --detach "refs/remotes/origin/$branch"
    if ($LASTEXITCODE -ne 0) { throw "Branch update failed" }

    Set-Location $worktree
    $python = "C:\Area33\randbeck-rsr-media-test\backend\.venv\Scripts\python.exe"
    if (-not (Test-Path $python)) { throw "Verified local Python environment missing" }
    $batch = "C:\Area33-private\rsr-verified-photo-pilot-20261104-174452"
    $inputFile = Join-Path $batch "area33-private-catalog-staging.json"
    if (-not (Test-Path $inputFile)) { throw "Original source staging missing" }
    $out = "C:\Area33-private\area33-text-only-pilot-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

    & $python .\scripts\import_randbeck_staging.py `
      --staging $inputFile `
      --batch-root $batch `
      --out $out `
      --identity-key "C:\Area33-private\area33-private-catalog-identity-key.bin" `
      --text-only-drafts
    if ($LASTEXITCODE -ne 0) { throw "Private text-only intake failed" }

    $draft = Join-Path $out "catalog-approval-template-part-001.json"
    if (-not (Test-Path $draft)) { throw "Expected private review draft missing" }
    & $python .\scripts\build_private_catalog_review.py --input $draft
    if ($LASTEXITCODE -ne 0) { throw "Offline review page failed" }
    Start-Process (Join-Path $out "catalog-owner-review.html")
    Write-Host "PRIVATE TEXT-ONLY OWNER REVIEW CREATED — NO LIVE SITE CHANGE."
}
```

Note: The importer checks original source identity, not real-time stock, MAP obligations, product legality, valid manufacturer image rights or actual customer price. With text-only samples no source images are processed and no RSR descriptions are copied. The 11 identity exceptions previously observed may remain; don't automatically fix their UPC/MPN fields by guessing.

The owner may review and export approved JSON offline for a future separate full release. Do not run --publish or deploy without direct authorization and an appropriate legal/supplier terms review. A text-only listing is not automatically permitted to advertise every product category in every jurisdiction.
