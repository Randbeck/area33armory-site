# Area 33 — private identity-evidence-assisted catalog review

**Branch:** `work/private-evidence-assisted-review-v1` (based on `work/private-text-batch-review-v1`).

**Scope:** PRIVATE owner-only review. No public product approvals, no change to `main`, no GitHub Pages deployment, no changes to live `area33armory.com`.

## Why this is needed

The existing 49 text-only RSR pilot drafts include duplicate-looking manufacturer/model names. They may be distinct exact products. The original importer deliberately kept UPC, manufacturer part number and distributor SKU out of the public draft, so the review page had no way to distinguish those names.

Rather than re-running intake, `scripts/prepare_private_catalog_evidence.py` joins **the original 60-row private RSR staging file**, **original 32-byte HMAC identity key**, **existing 49 draft JSON**, and **original 11-exception report**. It creates a NEW private identity-evidence sidecar in the SAME private pilot directory. Existing drafts remain unchanged.

## How the private evidence is built

- Recalculates the exact opaque catalog ID from the ORIGINAL UPC + manufacturer + manufacturer part number + model identity and original HMAC key. New keys are rejected: they would generate unrelated IDs.
- Verifies matching source model/manufacturer/category for every candidate, source SKU consistency, GTIN checksum, original counts, original 11 held identity exception coverage, and source publication/media/offer flags all FALSE.
- Records per-candidate UPC (recorded/check-digit valid, NOT independently identity verified), manufacturer part number, private source SKU(s), category and source identity label.
- Produces a conservative 200-character-or-shorter neutral *editorial suggestion* from recorded identity facts only, without distributor marketing descriptions, media, dealer costs, inventory or availability assertions.
- Fails closed if the staging data/key/draft alignment has changed. Quarantined identity groups stay excluded, and no manufacturer/model variant or missing identity facts are invented.

## Review UI enhancements

Run `scripts/build_private_text_batch_review.py --evidence <private-sidecar>` to show source UPC/MPN/SKU in the existing OFFLINE black-and-white review screen. Search finds private UPC, MPN and SKU. Duplicate-looking items show a part number and recorded UPC in the queue; each item has a private identity panel.

**Use as editable starting text** copies a suggested description into the editable draft only after any replacement warning. It resets all four owner approvals, returns the status to DRAFT and clears the owner-written declaration. It cannot set evidence-check date, confirm stock or rights, verify configuration, or approve a product. The owner must independently check source numbers, variant/fit, product copy, reseller/channel restrictions and actual ability to offer the item for sale.

The original save/resume/export-approved-only workflow and the handoff backend remain in place. The private evidence sidecar is NOT part of the exported product records or published v2 shards.

## One Windows setup and launch

Run this from PowerShell on the computer holding the previously generated 49-draft pilot. It clones code into a NEW isolated folder; the script checks existing source files and the original key and does not re-run intake:

```powershell
& {
  $ErrorActionPreference = 'Stop'
  $branch = 'work/private-evidence-assisted-review-v1'
  $repo = "C:\Area33\area33-evidence-review-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
  git clone --quiet --depth 1 --single-branch --branch $branch 'https://github.com/Randbeck/area33armory-site.git' $repo
  if ($LASTEXITCODE -ne 0) { throw 'Private reviewer code checkout failed' }
  & (Join-Path $repo 'scripts\start_private_evidence_review.ps1')
  if (-not $?) { throw 'Private evidence-assisted launch did not complete' }
}
```

Note: PowerShell multiline continuation uses a backtick, not a backslash. For a direct one-line Git invocation, use: `git clone --quiet --depth 1 --single-branch --branch $branch 'https://github.com/Randbeck/area33armory-site.git' $repo`.

The launcher uses these previously referenced default private files (and stops if any are missing):

- `C:\Area33-private\area33-text-only-pilot-20261105-032927\catalog-approval-template-part-001.json`
- `C:\Area33-private\area33-text-only-pilot-20261105-032927\catalog-private-exceptions.json`
- `C:\Area33-private\rsr-verified-photo-pilot-20261104-174452\area33-private-catalog-staging.json`
- `C:\Area33-private\area33-private-catalog-identity-key.bin`
- `C:\Area33\randbeck-rsr-media-test\backend\.venv\Scripts\python.exe`

If a path differs, call `start_private_evidence_review.ps1 -Pilot ... -SourceStaging ... -IdentityKey ... -Python ...` with actual existing paths. Do not create or replace a missing identity key.

## Validated

New synthetic tests cover 49 HMAC-joined candidates (including duplicate model labels), 11 quarantined identity groups, incorrect key rejection, altered source/model/sidecar rejection, no supplier marketing text/cost or image bytes in evidence, no automatic approvals, no private catalog handoff when records have not actually been reviewed, and Node.js syntax of the offline review page. Existing Python and browser website tests run in GitHub CI. **All fixtures are synthetic; the actual private 49 records have not been opened in CI.**

## Publication boundary

No products are published simply because an RSR UPC passes the check-digit algorithm or appears in a dealer feed. The recorded UPC/MPN must be independently confirmed for the exact variant. Owner approval and manufacturer/dealer channel policies remain separate requirements. The 11 identity exceptions stay quarantined.