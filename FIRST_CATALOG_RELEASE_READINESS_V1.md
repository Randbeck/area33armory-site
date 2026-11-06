# Area 33 first-release readiness — private decision worklist v1

Branch: `work/first-catalog-readiness-v1`. Built on top of the existing offline, source-linked UPC/MPN review screen.

**Nothing is deployed, source drafts and original private photos are untouched, and no product is newly approved.** Live `area33armory.com`, `main`, GoDaddy and GitHub Pages are unchanged.

## Why this batch

The first 49 product candidates are now distinguishable by UPC/MPN, but still require independent product evidence, original copy, actual sales/channel eligibility and individual owner approval. To avoid another engineering-only loop, this batch surfaces actual research leads for more identified products and provides one concrete **first-release decision worklist**, rather than suggesting everything is launch-ready.

## Added exact public evidence (all independently reviewed by the owner before use)

Existing two Single Mag Carrier references remain separate: `CMCS-2-D` / `193858308883` is listed for 9mm/.40 single-stack magazines; `CMCS-4-D` / `193858308906` is listed for 9mm/.40 double-stack magazines.

Additional dated retailer research leads are mapped **only when BOTH the original private UPC and manufacturer part number match**:

- `CT35-0057-RH-D` / `193858308937`: Cloak Tuck, right-hand IWB, Glock 19/23/19X/44/45 family (final generation/configuration compatibility still requires verification).
- `CT35-0939-RH-D` / `193858309125`: Cloak Tuck 3.5, right-hand IWB, Glock 43/43X. Retailer listings state Boltaron construction.
- `PHO-0057-L1-D` / `193858752136`: Photon light-bearing holster. Listings state ambidextrous carry and a Glock 19/44/45/19X/23 family fit, but verify the exact weapon light and generation before using any claim.

**Disputed identity, deliberately held:** Several public retailers list `CT35-1198-RH-D` as a SIG P365 X-Macro holster, but one reports UPC `193858332383` while another reports `193858373485`. The new private research packet records both sources and both UPC claims. If the original 49-draft record matches one of these, it receives an **unresolved UPC conflict** requiring authoritative identity evidence; the browser cannot confirm it for private handoff. Deleting the warning in saved research notes is blocked. Do not invent the correct UPC.

These are **retailer research leads**, not original manufacturer licenses or proof Area 33 can sell the goods. No retailer price, availability, trademarks, photographs, copyrighted marketing copy, private RSR SKU or dealer costs are copied into the customer-facing catalog. The source-linked fact checkboxes default to false.

## New release-readiness report

`scripts/prepare_private_first_release_readiness.py` cross-checks unchanged original drafts, 11 held exceptions, original exact-identity evidence, current private source-linked research, and optional personally saved review progress. It emits only a **PRIVATE** folder containing:

- `private-first-release-readiness.json`: audited source hashes, exact product IDs, status counts, individual next actions and pending identifier conflicts.
- `private-first-release-worklist.csv`: searchable local list ordered by handoff eligibility, owner-review work, independent research work, and held identity conflicts.
- `README_PRIVATE.txt`: explains the nonpublication boundary.

Status values are **private_handoff_eligible**, **owner_review_pending**, **independent_research_needed**, and **identity_conflict_hold**. Being eligible for a private handoff **does not authorize actual web publication** or prove dealer resale terms, live inventory, price, MAP compliance, shipping rules or photo rights. If no real products were individually reviewed, the eligible count will correctly remain zero. The original 11 identity exceptions stay outside the 49 candidates.

## Existing saved work is preserved

The original offline review now accepts `--saved-progress` and re-opens a prior complete 49-record owner-progress file without overwriting the original draft source. Manufacturer/model, opaque ID and no-photo rights remain immutable. The Windows launcher accepts optional `-SavedProgress` and `-SavedResearch` paths.

`scripts/migrate_private_research_notes.py` merges prior (including previous-v1) saved source research links and personally checked facts with the updated seeded evidence packet. It preserves source indices and check flags, fails rather than discard notes on limits/errors, and **never allows old progress to erase a known UPC warning**. Original saved files are not modified or deleted.

## One consolidated Windows run

Use PowerShell from the Windows computer containing the original 49-record private pilot. This does not re-run distributor media intake:

```powershell
& {
  $ErrorActionPreference = 'Stop'
  $branch = 'work/first-catalog-readiness-v1'
  $checkout = "C:\Area33\area33-release-review-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
  git clone --quiet --depth 1 --single-branch --branch $branch 'https://github.com/Randbeck/area33armory-site.git' $checkout
  if ($LASTEXITCODE -ne 0) { throw 'Release-review clone failed' }
  & (Join-Path $checkout 'scripts\start_private_evidence_review.ps1')
  if (-not $?) { throw 'Private source-backed release review failed' }
}
```

This opens the current offline product reviewer, generates a fresh immutable-identity evidence sidecar and research packet **beside the original private drafts**, and produces a new private readiness JSON/CSV folder. It prints those paths in PowerShell.

### Resume prior saved progress when applicable

If you already clicked *Save private progress* and/or *Save research notes*, add verified actual download file paths as parameters:

```powershell
& (Join-Path $checkout 'scripts\start_private_evidence_review.ps1') -SavedProgress 'C:\Users\YOU\Downloads\area33-private-text-batch-progress.json' -SavedResearch 'C:\Users\YOU\Downloads\area33-private-product-research-progress.json'
```

Replace `YOU` and the filenames with their actual locations, or omit either parameter independently. Browser-generated suffixes may differ. The saved notes are migrated into a NEW file with warnings and new source leads; the originals remain untouched. The launcher requires the original 32-byte catalog identity key, 49-draft JSON, 11-exception report, RSR private staging JSON, and previously used Python venv at the locations referenced in earlier batches. Missing paths must be located, not recreated.

## What to do next

Open the generated CSV worklist. Begin with the short group of products that already have specific independent source leads. Confirm exact manufacturer/model/variant, independently verify relevant fit, write original short product copy, check your ability to sell under each manufacturer's program and locally applicable restrictions, then confirm each product one by one. Save both progress files. Keep disputed UPC records and all 11 identity exceptions held. Once some products are genuinely approved, the existing separate private handoff can verify them before any later owner-authorized Pages deployment.

## Tests

GitHub CI performs all Python tests, website JavaScript syntax and public website contract tests, including new synthetic 49/11 readiness counts, a previously checked product's private handoff eligibility, source identity conflict blocking despite owner approval flags, conflict warning tamper rejection, existing progress preservation, and saved research note migration. None of these synthetic fixtures approves real Area 33 listings.