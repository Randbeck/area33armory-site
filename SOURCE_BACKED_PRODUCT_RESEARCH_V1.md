# Area 33 — source-backed private product research v1

Development branch: `work/referenced-product-research-v1`.

## Result

Existing **49 text-only product candidates** and **11 held exceptions** remain intact. The original per-product approval process now has an additional **private, source-linked research section** for the EXACT UPC + MPN pair. No website publication, no supplier media rights, no price/inventory/sale eligibility claims are inferred.

### Key additions

- `scripts/prepare_private_product_research.py` accepts the **unchanged** original private draft + exception report + HMAC-matched identity evidence. It builds a NEW private research packet containing exactly 49 UPC/MPN-linked research entries, each with a safe exact-match search query.
- It seeds **two** external research leads for public UPC/MPN pairs `193858308883`/`CMCS-2-D` and `193858308906`/`CMCS-4-D`. Links are independent retail reference pages (KYGunCo, WBT Guns, OpticsPlanet), checked November 6, 2026, **not manufacturer approvals**. Proposed facts distinguish 9mm/.40 single-stack vs double-stack magazine configurations and carry options. Every fact starts `owner_checked: false`.
- There are **no invented specifications or sourced text for the remaining 47 products**. They have exact lookup queries, with no facts or sources until researched.
- The existing `scripts/build_private_text_batch_review.py` now accepts optional `--research` and shows the exact reference URL/title/date, UPC/MPN query and related claims alongside the existing private source identity block. External search or source pages open **only on an explicit click**; there is no background scraping or network request.
- Reviewers can add a source link and a brief, source-indexed factual specification; explicitly check each factual claim; save/restore research notes **in a separate private JSON download**; and use only personally checked facts as an editable description starting point. Draft insertion clears existing item approvals and the `owner_written` declaration. The existing publisher STILL requires all item-specific owner checks. No research field is exported by the public catalog handoff.
- Product list MPN and Recorded UPC now have distinct display lines and improved wrapping.

## One PowerShell command to open updated reviewer

Run this in PowerShell on the Windows computer holding the **same original** private pilot files. It clones into a fresh isolated code directory, generates matching private evidence plus research files alongside the original 49 drafts, and opens the new review HTML. It does **not** modify the old drafts or published site.

```powershell
& {
  $ErrorActionPreference = 'Stop'
  $branch = 'work/referenced-product-research-v1'
  $checkout = "C:\Area33\area33-source-research-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
  git clone --quiet --depth 1 --single-branch --branch $branch 'https://github.com/Randbeck/area33armory-site.git' $checkout
  if ($LASTEXITCODE -ne 0) { throw 'Isolated review code clone failed' }
  & (Join-Path $checkout 'scripts\start_private_evidence_review.ps1')
  if (-not $?) { throw 'Private source-backed review launcher failed' }
}
```

The launcher expects existing paths (override through its PowerShell parameters if they differ):

- `C:\Area33-private\area33-text-only-pilot-20261105-032927\catalog-approval-template-part-001.json`
- `C:\Area33-private\area33-text-only-pilot-20261105-032927\catalog-private-exceptions.json`
- `C:\Area33-private\rsr-verified-photo-pilot-20261104-174452\area33-private-catalog-staging.json`
- `C:\Area33-private\area33-private-catalog-identity-key.bin`
- `C:\Area33\randbeck-rsr-media-test\backend\.venv\Scripts\python.exe`

Do not generate a new identity key to satisfy this command. The tool rejects wrong keys, changed source records, missing exceptions and unexpected prior approval flags.

## Progress handling

**Product approvals and research notes are intentionally separate**: click *Save private progress* and *Save research notes* before closing. The next time, use *Resume saved progress* and *Load research notes* for the matching original 49-draft group. This avoids the risk of research URLs, raw supplier SKUs, or notes entering public catalog JSON. Source links are not a substitute for exact independent variant verification.

## Test coverage

GitHub CI runs all Python tests and JS public website checks. New tests cover the 49/11 identity linkage, two exact UPC+MPN seeded source leads, lack of any automatic fact review, packet hash/identity tamper rejection, user-clicked URL behavior, browser JavaScript syntax, and the existing approved-only publisher boundary. The actual local RSR private files were not uploaded or accessed remotely. Synthetic test products do not count as approved listings.

**Live site remains untouched.** No changes to `main`, GoDaddy, DNS, Pages settings, current under-construction site, 49 private draft approvals, or 11 quarantined exceptions.