> **RSR manufacturer image-rights correction (2026-11-05):** The RSR FTP image disclaimer explicitly says RSR does not own manufacturer photographs/logos/trademarks or have authority to pass image rights to a dealer. Supplier-only approval is insufficient. This integration now requires signed grants bound to the exact manufacturer and category, backed by written rights-holder permission or manufacturer dealer-media terms. The old supplier-wide rights concept below is superseded for RSR images. No current product/image has been authorized for release.

# Area 33 importer: signed supplier-category scopes (development only)

The public Area 33 catalog remains approved-only and unchanged. No release, no public product images and no automatic listing permission have been added by this branch.

## Existing owner evidence

- 60 private source products from RSR after the first verified image pilot.
- 49 owner-review drafts (all still false for owner approval) after 96 private metadata-cleared photo copies.
- 11 identity exceptions (invalid UPC and incomplete exact manufacturer/MPN/model may overlap).
- The original 29,935 RSR matches were filename-only and are NOT independently approved site imagery.

## Integrated trust boundary

Randbeck's work/catalog-policy-authorization-v1 branch builds an owner-signed, evidence-backed private supplier/category policy ledger and a signed per-source evaluation receipt. This site branch adds scripts/verify_randbeck_scope_receipt.py, and extends scripts/import_randbeck_staging.py with optional --scope-receipt, --scope-ledger and --scope-key (all three are required together).

Receiver validates:

- HMAC signatures for the exact current owner ledger and private receipt (32-byte key held OUTSIDE Git);
- SHA-256 of the EXACT Randbeck private staging file and policy supplier-evidence files;
- exact supplier/category, a currently active unrevoked grant, source rights for listing, source photo, description, and metadata-cleared JPEGs where needed;
- owner grant expiry, max source data age, and receipt age within 30 minutes; and
- item counts, per-SKU category and status, false-publication flags, distinct records and the proposed public category.

Source rows without signed policy eligibility are held in the private exception report. Eligible rows still undergo the existing actual JPEG/SHA-256, UPC, manufacturer, MPN, model, and EXIF checks. The importer writes a PRIVATE map from scope grant IDs to opaque catalog IDs for later auditable withdrawals. **The importer NEVER marks content, identity, media rights, offered-for-sale, or owner publication approval true.**

Missing, expired, modified or revoked supplier permissions fail closed for applicable products. A developer cannot turn on retailer photo display by setting a false boolean to true in product JSON.

## Deliberate restrictions

RSR's product feed and password-protected image FTP do not themselves establish rights to use and transform images for an independent store. The owner must supply real written source/category rights evidence. Supplier requirements for MAP, online sale restrictions, image modifications, and brand exclusions must be reviewed separately. A listing being in a feed does NOT mean an item is in stock or ready to ship.

The current API can generate verified private cohort candidates under one owner-approved category scope, avoiding repeated SKU-level rights screening. However, actual public cohort publication and retailer signoff remain a separate, explicit release workflow. No supplier license is issued by software, and no auto deploy or live site update is available in this branch.

## Integrating after supplier rights are documented

Run the Randbeck private scope evaluator against a fresh verified staging source to create a signed receipt. In the existing Area 33 private bridge invocation add:

    --scope-receipt <new-private-signed-eligibility.json>
    --scope-ledger <latest-active-owner-policy-ledger.json>
    --scope-key <private-owner-policy-key.bin>

And, only if verified distributor rights allow the technical metadata-only transformation, add:

    --prepare-private-exif-copies

All files and owner keys must remain under C:\Area33-private, never inside a Git repository. If the 30-minute receipt has expired, recalculate Randbeck eligibility; if the distributor snapshot itself has expired, refresh source inventory and verification first.

The private source/category grants never permit unreviewed data to be inserted directly into the public v2 sharded index. Previously approved public items require a separately reviewed withdrawal if permissions are later revoked. A centralized authorization source and audited release workflow should be established before live deployment.
