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


## Offline owner approval page — Nov 4 update

The next step uses the already generated private approval file. No FTP connection, site deployment, media download or changes to the V16 Randbeck installation.

In PowerShell:
\`\`\`powershell
Set-Location "C:\Area33\area33-catalog-approval-test"
git pull --ff-only origin work/approved-catalog-thumbnails
if ($LASTEXITCODE -ne 0) { throw "Unable to update private review tool" }

$draft = "C:\Area33-private\catalog-approvals-20261104-160150\catalog-approval-template.json"
if (-not (Test-Path $draft)) { throw "Private approval draft not found" }

py .\scripts\build_private_catalog_review.py --input $draft
if ($LASTEXITCODE -ne 0) { throw "Review page creation failed" }
Start-Process (Join-Path (Split-Path $draft) "catalog-owner-review.html")
\`\`\`

The local HTML displays the original private source photos, source-proposed manufacturer/model, and fields for exact variant, category, type, date/evidence, permitted image rights, and per-photo alt descriptions. **All 5 approvals start false** for a newly prepared draft. Each product requires an explicit five-part checklist, a conscious human confirmation, and an explicit export. Edit a field after confirmation and the product returns to draft.

"Save private progress" downloads a copy of the edited draft JSON. "Export approved items only" downloads only independently reviewed selections and **does not publish them**. Browsers normally place downloaded files in the user's Downloads folder; move any such files to private storage outside the website/GitHub checkout. The page does not automatically persist edits; export before closing it.

Do **not** approve every RSR record by default: only mark the exact products Area 33 actually offers for sale. RSR's rights documentation pertains to displaying products for sale, not arbitrary promotion or general catalog research. The photo/identity, rights, compatibility and sale listing facts require independent owner checks. An "approved" owner-review JSON file is still only a *private input* to the separate, fail-closed publisher and must never be committed.

The private HTML itself embeds absolute local paths for offline image previews. Keep it private and do not upload the HTML, exported JSON, FTP credentials or distributor originals to GitHub or an external site. No online account integration or public release is performed by the page.

**Validation:** \`python -m unittest discover -s scripts -p "test_*.py" -v\` and GitHub branch CI cover generator escaping, hash checks, no auto approvals, and offline script syntax.
