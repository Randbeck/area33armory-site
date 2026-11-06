# Area 33: 49 text-only drafts + 11 identity exceptions — fast private owner review

Branch: `work/private-text-batch-review-v1`. All work is isolated; no live website or GitHub Pages changes. No source photos, distributor descriptions, automatic approvals or guessed identities.

## What is implemented

`scripts/build_private_text_batch_review.py` accepts the SAME private draft and exception files already generated from Randbeck's RSR pilot. It produces one offline HTML reviewer with searchable queue, per-item review, next/previous/next-unfinished, private save/resume, approved-only export, review counts, and 11 read-only quarantined exception groups. It does NOT rerun the RSR intake.

Exact manufacturer and model are read-only because changing them under an opaque product ID can invalidate product identity. Hold incorrect identities and fix upstream. Proposed variant/fit, category/type, independent evidence reference/date, original description (18–200 characters) and independently owner-written origin remain editable. Any meaningful edit returns the item to draft and clears the prior four human checkboxes. Each item needs its own explicit confirmation and a separate confirm dialog. No bulk approve.

Text-only items ALWAYS have `photos: []`, `rights_source: ""`, and `media_rights: false`. The other four existing approvals are exact_identity, content_review, offered_for_sale, owner_publication.

`scripts/prepare_private_text_batch_handoff.py` checks an exported private progress/approved-only JSON against the ORIGINAL 49-draft IDs and model/manufacturer plus the original 11-exception report. It uses the EXISTING server-side publisher validator, rejects source photos, claims of image rights, short/copied copy origin, incomplete confirmations, future/missing dates, and identity changes. It stages only individually approved records. Optionally creates a PRIVATE v2 first approved-only release. Nothing is committed, deployed or offered for sale automatically.

## Open the real private 49-record review in ONE PowerShell command

This uses the previously confirmed Windows pilot location; the developer code is cloned to a NEW folder, avoiding dirty existing Git worktrees.

```powershell
& {
  $ErrorActionPreference = 'Stop'
  $branch = 'work/private-text-batch-review-v1'
  $repo = "C:\Area33\area33-batch-review-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
  $pilot = 'C:\Area33-private\area33-text-only-pilot-20261105-032927'
  $drafts = Join-Path $pilot 'catalog-approval-template-part-001.json'
  $exceptions = Join-Path $pilot 'catalog-private-exceptions.json'
  $python = 'C:\Area33\randbeck-rsr-media-test\backend\.venv\Scripts\python.exe'
  if (-not (Test-Path $drafts)) { throw "Private 49-product draft missing: $drafts" }
  if (-not (Test-Path $exceptions)) { throw "Original 11-exception report missing: $exceptions" }
  if (-not (Test-Path $python)) { throw "Previously used Python environment missing: $python" }
  git clone --quiet --depth 1 --single-branch --branch $branch `
    'https://github.com/Randbeck/area33armory-site.git' $repo
  if ($LASTEXITCODE -ne 0) { throw 'Isolated branch clone failed' }
  $page = Join-Path $pilot ("catalog-batch-owner-review-{0}.html" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
  & $python (Join-Path $repo 'scripts\build_private_text_batch_review.py') `
    --drafts $drafts --exceptions $exceptions --out $page
  if ($LASTEXITCODE -ne 0) { throw 'Private review generation failed' }
  Start-Process $page
  Write-Host "OFFLINE PRIVATE OWNER REVIEW OPENED. Nothing published."
}
```

Use the offline page to review exact identity and author original copy, select copy origin, inspect evidence and eligibility, check all 4 owner confirmations, and confirm each product individually. Save private progress from time to time; the browser downloads JSON to its downloads folder. The 11 exceptions remain read-only.

## After one or more products are truly reviewed

Choose **Export approved-only JSON**. Then use the SAME isolated cloned repository folder in this separate private handoff (replace YOUR-CODE-CHECKOUT with the actual name).

```powershell
$repo = 'C:\Area33\YOUR-CODE-CHECKOUT'
$python = 'C:\Area33\randbeck-rsr-media-test\backend\.venv\Scripts\python.exe'
$pilot = 'C:\Area33-private\area33-text-only-pilot-20261105-032927'
$reviewed = Join-Path $env:USERPROFILE 'Downloads\area33-owner-approved-text-only-private.json'
$out = "C:\Area33-private\area33-owner-approved-first-release-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

& $python (Join-Path $repo 'scripts\prepare_private_text_batch_handoff.py') `
  --input $reviewed `
  --source-drafts (Join-Path $pilot 'catalog-approval-template-part-001.json') `
  --exceptions (Join-Path $pilot 'catalog-private-exceptions.json') `
  --out $out --stage-first-private-release
if ($LASTEXITCODE -ne 0) { throw 'Private approved-only handoff failed' }
Write-Host "FIRST PRIVATE RELEASE: $out. Nothing published."
```

The downloaded filename might include a browser-generated suffix, so verify the actual local path. Both commands only work with the existing private pilot files and stay outside the public Git repository.

## Safety and limits

- The 49 pilot records are NOT approved until the owner individually verifies them. The 11 exceptions are held, not silently repaired.
- Dates and source evidence must be real; text copy must be original and checked; actual dealer/manufacturer sales policies must be respected. An owner checkbox is not a manufacturer image license.
- Existing GitHub Pages under-construction site remains unchanged until a completely separate, explicit owner-approved release. No real inventory, customer price, checkout, shipping compliance or sale eligibility is inferred from the RSR feed.
- `scripts/test_private_text_batch_review.py` tests 49 synthetic candidates + 11 synthetic held exceptions, offline browser JS, reviewed export, strict identity revalidation and private release staging. Synthetic fixtures are not genuine Area 33 approvals.
