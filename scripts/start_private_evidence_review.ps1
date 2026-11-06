# Starts private evidence-assisted review using existing pilot files.
# Never deploys, approves, edits source drafts or uploads.
param(
    [string]$Pilot = 'C:\Area33-private\area33-text-only-pilot-20261105-032927',
    [string]$SourceStaging = 'C:\Area33-private\rsr-verified-photo-pilot-20261104-174452\area33-private-catalog-staging.json',
    [string]$IdentityKey = 'C:\Area33-private\area33-private-catalog-identity-key.bin',
    [string]$Python = 'C:\Area33\randbeck-rsr-media-test\backend\.venv\Scripts\python.exe',
    [string]$SavedProgress = '',
    [string]$SavedResearch = ''
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
$research = Join-Path $Pilot "catalog-private-product-research-$stamp.json"
$reviewPage = Join-Path $Pilot "catalog-source-backed-review-$stamp.html"
$readiness = Join-Path $Pilot "catalog-first-release-readiness-$stamp"
$scriptDir = $PSScriptRoot

& $Python (Join-Path $scriptDir 'prepare_private_catalog_evidence.py') `
    --staging $SourceStaging `
    --drafts $drafts `
    --exceptions $exceptions `
    --identity-key $IdentityKey `
    --out $evidence
if ($LASTEXITCODE -ne 0) { throw 'Private UPC/MPN/SKU evidence join failed. Nothing published.' }

& $Python (Join-Path $scriptDir 'prepare_private_product_research.py') `
    --drafts $drafts `
    --exceptions $exceptions `
    --evidence $evidence `
    --out $research
if ($LASTEXITCODE -ne 0) { throw 'Private source-linked research packet failed. Nothing published.' }

$researchToUse = $research
if ($SavedResearch) {
    if (-not (Test-Path -LiteralPath $SavedResearch -PathType Leaf)) {
        throw "Saved research-notes file missing: $SavedResearch"
    }
    $researchToUse = $SavedResearch
}
$reviewArgs = @(
    '--drafts', $drafts,
    '--exceptions', $exceptions,
    '--evidence', $evidence,
    '--research', $researchToUse,
    '--out', $reviewPage
)
$readinessArgs = @(
    '--drafts', $drafts,
    '--exceptions', $exceptions,
    '--evidence', $evidence,
    '--research', $researchToUse,
    '--out', $readiness,
    '--prepare-private-readiness'
)
if ($SavedProgress) {
    if (-not (Test-Path -LiteralPath $SavedProgress -PathType Leaf)) {
        throw "Saved owner-review progress missing: $SavedProgress"
    }
    $reviewArgs += @('--saved-progress', $SavedProgress)
    $readinessArgs += @('--saved-progress', $SavedProgress)
}
& $Python (Join-Path $scriptDir 'build_private_text_batch_review.py') @reviewArgs
if ($LASTEXITCODE -ne 0) { throw 'Private evidence-assisted review failed. Nothing published.' }

& $Python (Join-Path $scriptDir 'prepare_private_first_release_readiness.py') @readinessArgs
if ($LASTEXITCODE -ne 0) { throw 'Private release-readiness report failed. Nothing published.' }

Start-Process -FilePath $reviewPage
Write-Host 'PRIVATE evidence-assisted catalog review opened in your browser.'
Write-Host 'Look-alike models now show recorded part numbers, UPC and source-linked research.'
Write-Host 'No publication, image processing, rights grants, or source data changes.'
Write-Host "Review page: $reviewPage"
Write-Host "Private identity evidence: $evidence"
Write-Host "Private research packet: $researchToUse"
Write-Host "Private release-readiness report: $readiness"
Write-Host 'The CSV worklist is inside that report folder. No publication occurred.'
Write-Host 'Save product progress and research notes separately before closing the browser.'
