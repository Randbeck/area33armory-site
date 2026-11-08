# Area 33 — Six-View Product Counter: Media and Release Contract

## Goal

Give a customer a premium, true-photograph inspection of **one exact product reference** using the six physical camera directions (left, right, top, bottom, front, rear). The viewer should never claim that images of different SKUs or individual products are multiple views of one firearm.

## Current coverage (2026-11-08)

- `ruger-precision-308-gen1`: **one original Creative Commons reference photograph**, photographer Coati077, CC BY-SA 4.0. The photographer's file caption identifies a Ruger Precision Rifle in .308 Winchester, Generation 1. Its exact camera direction is **not verified**; it appears only under “reference,” not under one of the six direction buttons.
- `ruger-precision-6mm-2019-photo`: a separate firearm photo of a **different** Ruger Precision Rifle example; never use as another angle of .308 Gen1.
- `glock-g19-gen5-mos` and other research products: accurate text identities are available, but the viewer has **no exact-item approved directional photo set**. Do not substitute the 3D concept pilot model, manufacturer hotlinks, other variants, or illustrations.
- Actual separate Meopta scope photo can be shown alongside a rifle as research, but there is **no exact confirmed fitment for this photographed rifle and scope**.

The six angle slots remain unavailable unless the exact product photo and rights have been reviewed. “6 / 6” must mean six actual, distinct camera directions—not a synthetic rotation of one photograph.

## Temporary local six-view demonstration

The preview has an optional local file selector. Choose one of the six directions and load a photograph of **the same exact selected product**. The image is shown using a browser-local object URL only:

- It is **not sent to GitHub, Area 33, Randbeck, a server, or a third party** by this page.
- It is **not stored in localStorage**, persisted, placed in a catalog, or given a media-rights approval.
- Browser refresh resets the session. The “Clear local photos” control revokes all currently loaded images for the selected item.
- Sharing a product link includes product and accessory IDs only. Uploaded local images **do not travel** with a link.

This proves the six-angle interface with owner-supplied real photos without promising public publication.

## Public image approval workflow

1. Establish manufacturer, exact SKU or uniquely reviewed individual model and variant, and record a durable identity.
2. Obtain six **unmodified or appropriately licensed** photographs taken from left, right, top, bottom, front, rear (not another SKU, a product family, different chambering, or a single photo cropped into fake views).
3. Record the author/source, written publication permission or applicable license, modifications and attribution requirements, and approval date. If a Creative Commons license has share-alike obligations, comply with the relevant license.
4. Normalize each approved file to `assets/approved/multiview/<product-id>/<angle>.<jpg|jpeg|png|webp>`. Preserve quality and keep source masters private as appropriate. Do not put raw distributor downloads in the public repository.
5. Add a record per approved direction to `assets/multiview-public.json` with exactly: `productId`, `angle`, `src`, `alt`, `rights: "approved"`, `verifiedExactItem: true`, `reviewedAt`, `sourcePage`, `credit`. The viewer's safety checks reject unknown products, unmatched paths, duplicate directions, external media or incomplete fields.
6. Verify that every mapped image points to the **same exact** item and the asserted direction, and review publication rights and visual clarity manually. Contract validation alone is **not** a legal rights determination.
7. Run site validation, inspect every camera direction in the desktop and mobile browser, and obtain owner approval prior to release.

No images have been added to the public directional manifest yet.

## Accessory intelligence

The page reuses reviewed `evaluatePairing` statuses and intended-use guidance from `accessory-context.mjs`. Category relevance is not exact fit. Unknown or family guidance may appear for research, but never become a confirmed installation or graphic composite. The source name and photo (where licensed) stay separate from the firearm photograph.

## Pricing/quoting gate

The package builder intentionally displays **Not quoted** for every line and **Quote pending** for the complete package. It cannot calculate an executable price without exact variants, sourceable stock, landed costs, promotions/fees, jurisdictional charges and current quotes from Randbeck and approved Area 33 sale policies. There is no checkout, order, inventory or deceptive fabricated price.

## Backlog after owner visual review

- Obtain rights-cleared six-view photographs for a single exact currently offered firearm SKU; replace the older research-photo flagship when appropriate.
- Establish manufacturer-approved accessory imagery, separate accessory view sets and exact SKU-specific combination evidence.
- Add verified customer pricing and quote-expiry treatment through the shared Randbeck Intelligence and supplier services.
- Preserve this interface as a fallback when real 3D assets are eventually approved, without forcing 3D onto every product.
