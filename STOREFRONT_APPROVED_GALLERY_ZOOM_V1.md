# Area 33 — Approved-only storefront image zoom v1

Branch: `work/storefront-approved-image-zoom-v1`, based on the first-catalog-readiness branch.

## What was built
The existing `catalog.html` product-detail modal now mounts `assets/catalog-gallery.mjs` **only for products with valid, approved, same-origin images** supplied by the strict public catalog contract. For image-based published products, visitors get:
- Desktop image hover zoom that tracks cursor location inside the image area (WBT-style magnifier interaction).
- A full-screen viewer opened by clicking the approved image, with zoom in/out/reset and keyboard arrow / Escape controls.
- Swipe and pinch-to-zoom support using pointer events on touch screens; drag to pan at greater than 100% zoom.
- Thumbnails for multiple approved views, with current-view and accessible button labels.
- Neutral image-load error states rather than substituting an unlicensed or private distributor image.

The feature intentionally never runs for text-only records. It never reads private image files, never uses remote distributor sources, and never asserts rights or sourceability. The original photo publication validator remains unchanged. Current `assets/catalog-public.json` contains **zero items**, so there is no new live product content, only a gallery feature for future legitimate image listings.

## Privacy / rights
The browser component rechecks that the public image URL:
1. Is HTTP(S), with no credentials, query or fragment;
2. Uses the same origin as the current site;
3. Belongs to the exact catalog ID in `/assets/approved/catalog/<id>/view-01.jpg` through `view-08.jpg`;
4. Comes from an image-based record, not a text-only one.

Independent public gallery sanitizers already enforce `rights: approved` in source data and exact identity. The zoom feature cannot elevate unapproved photos.

## Testing
`scripts/test_catalog_gallery_contract.mjs` tests approved-image eligibility, exact path matching, same-origin restrictions, text-only omissions, hover math, zoom limits and CSS/JS integration. Full CI also runs the existing Python validation and JavaScript site contracts.

## Deployment status
No merge into `main`, no GitHub Pages deployment, no DNS changes, no live catalog images, and no release approval. This branch is ready to be considered **after authorized product media is available**.

## Review path
Browse `catalog.html`, select a product with a properly approved `images` record, click **View details**, then hover its image on desktop or tap it on mobile. The approved photo is displayed with magnification and optional thumbnails. If no images are authorized, the preexisting text-first display stays in place.
