# Area 33 private EXIF metadata gate — optional lossless review copies

## Evidence from owner's 60-product pilot

- 60 product records, 60 exact-identity groups.
- 3 private owner-review drafts; 57 held groups had an original JPEG containing EXIF.
- 55 "no usable verified photo" warnings were mostly downstream effects of withholding those EXIF-bearing originals, not proof their images are absent or corrupt.
- Independently: two invalid GTIN observations and eleven missing manufacturer/MPN/model observations; reasons overlap and MUST NOT be added as disjoint group counts.
- No source rights, stock or publication was authorized.

## Engineering fix (still private)

The bridge scripts/import_randbeck_staging.py supports **optional** --prepare-private-exif-copies. It leaves original RSR JPEGs and hashes unchanged. Only when explicitly selected, it:

1. Rechecks each original photo's SHA-256, real byte count, JPEG decode, actual size and source SKU association.
2. Inspects EXIF *tag IDs only*, not sensitive values, and refuses automatic processing of nontrivial orientation tags because the displayed item could rotate or change appearance.
3. Creates a new PRIVATE copy, removing JPEG APP1 EXIF/XMP, APP13 IPTC and JPEG comments without decompressing/recompressing the source scan data. APP2 ICC profiles and Adobe color markers remain intact to preserve appearance. The tool rejects a copy unless full decode yields exactly the same pixels, dimensions and color mode as the original.
4. Writes per-source/derivative hashes and segment removal counts to the **private** exception/audit report, and substitutes the private lossless copy in otherwise eligible draft product records.
5. Keeps every owner-approval flag false, rights/evidence source empty, and product status draft. It never copies to approved public catalog assets; no --publish code is called. Unclear metadata (e.g. rotated orientation) remains quarantined instead of blocking unrelated SKUs.

**Crucial:** Private image processing does not establish authorization to modify or publish supplier photographs. For a public listing, owner-verified source-specific licensing and the exact product-for-sale use and content checks remain required. Do not treat an EXIF-free copy as legal or editorial approval.

## One consolidated re-run in the existing isolated Area 33 worktree

The existing worktree is C:\Area33\area33-catalog-integration-test. The 60-product originals are under C:\Area33-private\rsr-verified-photo-pilot-20261104-174452.

```powershell
& {
    $ErrorActionPreference = "Stop"
    $worktree = "C:\Area33\area33-catalog-integration-test"
    $branch = "work/randbeck-catalog-bridge-v1"
    if (-not (Test-Path $worktree)) { throw "Existing isolated integration folder missing" }

    $changes = git -C $worktree status --porcelain
    if ($LASTEXITCODE -ne 0 -or $changes) {
        throw "Local modifications found; refusing to overwrite"
    }
    git -C $worktree fetch origin "refs/heads/${branch}:refs/remotes/origin/${branch}"
    if ($LASTEXITCODE -ne 0) { throw "Fetch failed" }
    git -C $worktree switch --detach "refs/remotes/origin/$branch"
    if ($LASTEXITCODE -ne 0) { throw "Code update failed" }

    Set-Location $worktree
    $python = "C:\Area33\randbeck-rsr-media-test\backend\.venv\Scripts\python.exe"
    $batch = "C:\Area33-private\rsr-verified-photo-pilot-20261104-174452"
    $source = Join-Path $batch "area33-private-catalog-staging.json"
    if (-not (Test-Path $source)) { throw "Private source staging unavailable" }
    $out = "C:\Area33-private\area33-catalog-intake-exif-review-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

    & $python .\scripts\import_randbeck_staging.py `
       --staging $source `
       --batch-root $batch `
       --out $out `
       --identity-key "C:\Area33-private\area33-private-catalog-identity-key.bin" `
       --prepare-private-exif-copies
    if ($LASTEXITCODE -ne 0) { throw "Private metadata review conversion failed" }
    Write-Host "PRIVATE COPY RUN COMPLETE — NO PUBLICATION."
}
```

The program reports source products, groups, new private drafts, held groups, EXIF/manual-review holds and the number of private lossless EXIF-cleared image copies. Keep the complete output JSON, original JPEGs and identity key out of Git/public asset folders. Only share **console totals** in conversation.

## Remaining requirements

- Distinguish true model/MPN and UPC errors from missing source metadata; never merge different exact products using UPC alone.
- Source-specific image permission (including permission for technical metadata-cleared copies), categorization, sale-listing authorization, image-content/compatibility and freshness policy must be grounded and owner-reviewed.
- Public catalog currently has a 100-record strict static contract, not a live 30k-item server feed. No automatic public listing is enabled by this stage.
