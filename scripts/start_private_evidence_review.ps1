# Starts private evidence-assisted review using existing pilot files.
# Never deploys, approves, edits source drafts or uploads.
param(
    [string]$Pilot = 'C:\Area33-private\area33-text-only-pilot-20261105-032927',
    [string]$SourceStaging = 'C:\Area33-private\rsr-verified-photo-pilot-20261104-174452\area33-private-catalog-staging.json',
    [string]$IdentityKey = 'C:\Area33-private\area33-private-catalog-identity-key.bin',
    [string]$Python = 'C:\Area33\randbeck-rsr-media-test\backend\.venv\Scripts\python.exe'
)

$ErrorActionPreference = 'Stop'
$drafts = Join-Path $Pilot 'catalog-approval-template-part-001.json'
$exceptions = Join-Path $Pilot 'catalog-private-exceptions.json'
foreach ($file in @($drafts, $exceptions, $SourceStaging, $IdentityKey, $Python)) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
        throw "Original private prerequisite missing: $file. Do not regenerate the identity key or pilot; locate the matching existing file."
    }
}
if ((Get-Item -LiteralPath $IdentityKey).Length -ne 32) {
    throw 'Private identity key must be the original 32-byte binary key, not a replacement.'
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$evidence = Join-Path $Pilot "catalog-private-identity-evidence-$stamp.json"
$reviewPage = Join-Path $Pilot "catalog-evidence-assisted-review-$stamp.html"
$scriptDir = $PSScriptRoot

& $Python (Join-Path $scriptDir 'prepare_private_catalog_evidence.py') `
    --staging $SourceStaging `
    --drafts $drafts `
    --exceptions $exceptions `
    --identity-key $IdentityKey `
    --out $evidence
if ($LASTEXITCODE -ne 0) { throw 'Private UPC/MPN/SKU evidence join failed. Nothing published.' }

& $Python (Join-Path $scriptDir 'build_private_text_batch_review.py') `
    --drafts $drafts `
    --exceptions $exceptions `
    --evidence $evidence `
    --out $reviewPage
if ($LASTEXITCODE -ne 0) { throw 'Private evidence-assisted review failed. Nothing published.' }

Start-Process -FilePath $reviewPage
Write-Host 'PRIVATE evidence-assisted catalog review opened in your browser.'
Write-Host 'Look-alike models now show recorded part numbers and UPC.'
Write-Host 'No publication, image processing, rights grants, or source data changes.'
Write-Host "Review page: $reviewPage"
Write-Host "Private identity evidence: $evidence"
