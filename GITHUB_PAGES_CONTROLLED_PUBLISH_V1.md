# Area 33 / GitHub Pages controlled publication — development-only v1

**Status:** Implemented and tested on `work/github-pages-controlled-publish-v1`. **Nothing has been deployed or copied into the live `main` branch.** The live `area33armory.com` under-construction page remains untouched.

## Verified hosting background

On November 5, 2026 the operator's HTTPS response included `HTTP/1.1 200 OK`, `Server: GitHub.com`, and the under-construction page's October 2 last-modified date. Earlier GitHub Pages Actions logs successfully deployed `main` with CNAME `area33armory.com`. GitHub Pages is the current static host; the GoDaddy domain is not itself a reason to use separate paid web hosting.

**Important:** GitHub Pages currently auto-builds/publishes from `main`, based on the earlier Pages branch-build records. Moving to an owner-controlled manual workflow requires deliberate repository Settings → Pages → Build and deployment → Source → **GitHub Actions** at launch. The source configuration itself was NOT changed here.

## What the branch adds

- `scripts/catalog_static_allowlist.py` contains a single exact public file allowlist, reused by prior private release preflight and the new Pages verifier. No source-code, keys, rights documents, photos in private intake folders, invoices, or cost data can be included in the publishable artifact.
- `scripts/prepare_github_pages_candidate.py`: from an owner-approved and verified private catalog release + the prior controlled deployment package + unchanged private rights-hold ledger, build a **new private Pages candidate** at `<output>/site/` with the real Area 33 site, approved-only v2 catalog, versioned shards, licensed/independently approved images, domain `CNAME`, empty `.nojekyll`, and a public hash-inventory file `pages-release-public.json`. It validates and hashes every file first. All private approvals/hold records stay outside `site/`; the candidate is **NOT committed and NOT deployed**.
- `scripts/verify_github_pages_candidate.py`: a **Python-standard-library-only verifier** meant to run from trusted `main` source code against a separate approved release checkout. It requires two **owner-confirmed SHA-256 inputs** (public manifest and approved catalog index), checks full byte integrity, strict site allowlist, `CNAME`, exact public catalog identities, hash-pinned shards, text-only vs approved-photo contracts, image URL ownership, no orphaned deleted photo paths, and empty legacy fallback catalog. Fails closed on extra or tampered files.
- `examples/area33-github-pages-manual-deploy-TEMPLATE.yml`: **INACTIVE example only**. On a future, separately approved installation to `main/.github/workflows/`, it is `workflow_dispatch`-only, runs only on `main`, checks a separately approved `release/area33-...` branch and exact frozen Git SHA, exact input manifest/index hashes, explicit publication phrase, and the trusted verifier. Only if all checks pass does it upload **only `candidate/site`** as a Pages artifact and run `actions/deploy-pages` under the `github-pages` environment. No push trigger or auto-deploy code on the development branch.
- Tests in `scripts/test_controlled_catalog_release.py` and `scripts/test_github_pages_workflow_safety.py` exercise synthetic owned/approved content, public-only packaging, tamper rejection, rights-hold changes, exact hash verification, and inactive workflow safety.

## Why a GitHub Pages artifact is different from FTP

GitHub Pages Actions deploys a **new complete static site artifact**. Deleted old files should no longer be part of the new published version, so old photos and obsolete catalog shards are not intentionally copied forward. **BUT** cached old URLs may remain temporarily accessible at CDN edges or browsers; there is no cache-purge endpoint integrated with this implementation. A rights withdrawal requires manual verification of old URLs, elapsed cache lifetime, and escalation if urgently necessary. A "rollback" is a *new*, independently authorized release; never restore a snapshot containing currently restricted photos.

The site is a static catalog/inquiry frontend. GitHub Pages does not add a private pricing backend, real-time inventory service, shopping cart, checkout, taxes, FFL shipping rules, customer payment handling or product-media licenses.

## Future production activation — ONLY after explicit owner approval

1. First obtain genuinely approved products (including independent dealer resale, public content and photo rights where applicable). Our **49 RSR pilot text drafts remain unapproved**; 11 identity exceptions remain held. Their presence in a private folder does **not** allow them onto GitHub, even on a nondefault branch of the public repo.
2. Use the previously completed owner-approved private release → private site preflight → controlled release plan → private rehearsal sequence. Ensure the private rights-hold ledger is current and no expired/withdrawn rights survive.
3. Run `scripts/prepare_github_pages_candidate.py` against the real private release, plan and rights ledger. Record `<output>/private-pages-candidate-receipt.json` **privately**. Review `<output>/site/` before any public Git commit. Run `scripts/verify_github_pages_candidate.py` with both hashes. Verify no cost, private supplier records, secrets or unlicensed photos appear.
4. Only **after explicit owner signoff to make each product public**, commit **only public candidate `site/` files** to a separate `release/area33-...` branch of this *public* GitHub repo. This alone makes source files accessible through GitHub even if the live Pages site is still unchanged. The branch name must match the manual workflow pattern.
5. Prepare the publication workflow **separately and deliberately**, not by merging the entire development branch into `main`. At launch, have the owner switch Settings → Pages → Source to **GitHub Actions**; introduce ONLY the reviewed `catalog_static_allowlist.py`, `verify_github_pages_candidate.py` and manual workflow into the trusted `main` branch. A manual `workflow_dispatch` will not appear in Actions until the workflow is on the default branch. Do not inadvertently change `main/index.html` or ship the storefront during this setup.
6. Where available configure `github-pages` deployment environment branch restrictions and required reviewers. Trigger the manual workflow from **main**, enter the exact public release branch, frozen 40-character Git SHA, approved public manifest SHA, approved catalog index SHA, and the explicit publication phrase. **This is the actual publication step and requires owner authorization.** CI alone does not establish that rights have not expired since packaging.
7. After the deployment completes, verify `https://area33armory.com/`, `/catalog.html`, actual current v2 catalog version, image URLs, search and pagination. Check that retired photo URLs are gone and account for CDN caching. Do not treat a successful artifact upload as equivalent to a confirmed live URL.
8. If rollback is needed, build and review a newly gated release that passes **current** rights holds; re-run the exact manual process. The workflow deliberately has no one-click, rights-unsafe automated rollback.

## Private candidate-generation example (not for current unapproved drafts)

Run from an isolated checkout of this development branch using Python with Pillow installed in the existing validated environment.

```powershell
$python = "C:\Area33\randbeck-rsr-media-test\backend\.venv\Scripts\python.exe"
$package = "C:\Area33-private\owner-approved-controlled-release-package"
$approved = "C:\Area33-private\owner-approved-catalog-release"
$previous = "C:\Area33-private\previous-approved-catalog-release" # omit for first release
$holds = "C:\Area33-private\area33-rights\current-rights-holds.json"
$out = "C:\Area33-private\area33-pages-private-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

& $python .\scripts\prepare_github_pages_candidate.py `
  --private-deployment-package $package `
  --approved-release $approved `
  --previous-approved-release $previous `
  --rights-holds $holds `
  --out $out --prepare-private-pages-candidate
if ($LASTEXITCODE -ne 0) { throw "Public-only Pages candidate failed private checks" }

$receipt = Get-Content (Join-Path $out "private-pages-candidate-receipt.json") | ConvertFrom-Json
& $python .\scripts\verify_github_pages_candidate.py `
  --site (Join-Path $out "site") `
  --expected-manifest-sha256 $receipt.public_manifest_sha256 `
  --expected-index-sha256 $receipt.public_index_sha256
if ($LASTEXITCODE -ne 0) { throw "Pages candidate failed byte-for-byte verification" }

Write-Host "PRIVATE verified Pages candidate; no Git commit, website or DNS change."
```

For a *first* release omit `--previous-approved-release`; it is required when the controlled plan references a previous version. The paths above are placeholders, not verified existing folders.

## Next blockers before live Area 33 catalog

**Business**: owner authorization of a real publishable product set, exact identity, dealer resale and image rights, MAP/channel/sale restrictions.  
**Technical**: explicit owner authorization to place a trusted manual workflow in default `main`, Pages source change, review of public release branch, environment reviewer controls and live cache/removal checks.

**Nothing has changed on `main`, Pages Settings, GoDaddy, DNS, live area33armory.com, or the 49 private owner-review drafts.**
