# Area 33 owner-approved thumbnail catalog — development stage

Branch: \`work/approved-catalog-thumbnails\`, created from \`site-refresh-v1\`. **No changes to live \`main\`**, no approved RSR product images or listings in GitHub, no public stock/pricing, no checkout and no backend connection. The deployed static catalog remains empty until individual products are approved.

## Why two media tiers

Randbeck's eight-owner-review RSR items were all \`catalog_thumbnail_review_candidate\` and all had too-small images for the premium zoomable showroom. These technical media categories alone do **not** establish whether Area 33 offers each item for sale, exact fitment, or rights to advertise the images.

- Standard catalog supports one or more small *approved* images (source JPEG 300×200 or greater); genuine product name, no invented specs, and no universal stock claims.
- The existing premium showroom keeps independent requirements for multiple appropriately sized, approved angles.
- At the beginning, \`assets/catalog-public.json\` has \`items: []\`. No private records are shown.

## Implemented

1. \`scripts/prepare_catalog_candidates.py\` reads a PRIVATE Randbeck \`area33-private-candidates.json\` and private original RSR JPEG directory, verifies source file SHA-256 and exact per-SKU paths, then generates a **private** \`catalog-approval-template.json\` with *all five approvals false*, the exact source photos, random opaque IDs, and unresolved variant/category/type/rights details.
2. \`scripts/publish_approved_catalog.py\` requires actual independent true approvals for **owner publication, exact identity, photo rights, content, and currently offered for sale**; exact manufacturer/model/variant, source provenance and date, type/category, owner-confirmed descriptive photo alt text, unmodified original JPEGs, checked hashes, no EXIF or private media path inside Git, and at least one photo sized 300×200 or larger. It requires \`--publish\`, does not connect to FTP, and outputs only allowlisted fields and the approved original JPEGs.
3. The standard catalog UI now reads an **approved-only static JSON** in the site development branch and filters the complete *published set* client-side, with 12-item pages. Missing, corrupt or unapproved data fails closed; no demo products are substituted. Existing future server/API hook remains disabled.
4. The browser contract \`assets/catalog-static-contract.mjs\` validates strict public field allowlist, safe same-site \`assets/approved/catalog/<opaque-id>/view-NN.jpg\` paths, rights flags, unique product IDs, dates, types, and no source-private record keys. Images not approved are never loaded.
5. CI runs source preparation/publication unit tests and browser manifest regressions. All synthetic test photos live only in temporary unit-test directories and **do not represent real products**.

## Prepare a private approval draft from the prior eight-product run

Only after checking this entire plan, in PowerShell:

\`\`\`powershell
$siteTest = "C:\Area33\area33-catalog-approval-test"
if (Test-Path $siteTest) { throw "Review folder already exists; do not overwrite it." }
git clone --depth 1 --single-branch --branch work/approved-catalog-thumbnails https://github.com/Randbeck/area33armory-site.git $siteTest
if ($LASTEXITCODE -ne 0) { throw "Site branch clone failed" }
Set-Location $siteTest
py -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Python virtual environment failed" }
$python = ".\.venv\Scripts\python.exe"
& $python -m pip install "Pillow>=11,<13"
if ($LASTEXITCODE -ne 0) { throw "Pillow installation failed" }
& $python -m unittest discover -s scripts -p "test_*.py" -v
if ($LASTEXITCODE -ne 0) { throw "Python checks failed" }
node scripts/test_catalog_static_contract.mjs
if ($LASTEXITCODE -ne 0) { throw "Catalog browser checks failed" }

$handoff = Get-ChildItem "C:\Area33-private" -Directory -Filter "area33-media-tiers-*" |
  Where-Object { Test-Path (Join-Path $_.FullName "area33-private-candidates.json") } |
  Sort-Object LastWriteTime -Descending | Select-Object -First 1
$images = Get-ChildItem "C:\Area33-private" -Directory -Filter "rsr-catalog-review-*" |
  Where-Object { Test-Path (Join-Path $_.FullName "catalog-media-review.json") } |
  Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $handoff -or -not $images) { throw "Existing private RSR review is missing" }
$out = "C:\Area33-private\catalog-approvals-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
& $python .\scripts\prepare_catalog_candidates.py --handoff (Join-Path $handoff.FullName "area33-private-candidates.json") --media-root $images.FullName --out $out
if ($LASTEXITCODE -ne 0) { throw "Private approval draft failed" }
Write-Host "PRIVATE approval draft saved under: $out"
\`\`\`

The generated private JSON is not approved for sharing/publication. Its \`source_path\`, source hashes, SKU and inventory evidence are confidential review inputs: do **not** copy or commit it to GitHub.

## Actual publication is separate and NOT authorized yet

The publication script can run only after the owner confirms Area 33 is displaying that exact product for sale, RSR permits the specific image reuse, exact model/variant/fit, visible image content, and all five approval flags. A publication action must be explicitly requested and reviewed.

The CLI \`python scripts/publish_approved_catalog.py --input <private reviewed approvals.json> --publish\` writes approved-only catalog assets into the **site working copy**, not the public deployed website by itself. A separate code review and explicit owner authorization are required before merging/deploying to \`main\`.

## Boundaries

The preview has no payment features, customer checkout, verified stock or price data. RSR SKU-to-UPC association is source evidence rather than proof of safety or compatibility. Site/browser validation helps avoid accidental leaks, but it cannot replace human licensing, source identity, and release review. This is not a scheduled Randbeck image sync or automatically maintained all-distributor catalog.
