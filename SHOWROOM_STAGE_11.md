# Showroom stage 11: real-media engine, publication and tests

## Built on Area 33 website development branch
- \`showroom.html\`, \`assets/showroom.css\`, \`assets/showroom.js\`: premium site-native viewer with approved photo angles, touch swipe, arrow-key navigation, zoom, exact accessory configuration selector and before/after image comparison.
- \`assets/showroom-contract.mjs\`: independently testable client-side allowlist; rejects unapproved or incorrect photo/configuration metadata and unsafe image paths.
- \`scripts/publish_showroom.py\`: **offline/manual**, rights-gated publisher for curated exact-product media, verified matching configuration pairs, and image path/format checks. Never consumes private Randbeck data or automatically deploys.
- \`scripts/test_publish_showroom.py\` and \`scripts/test_showroom_contract.mjs\`: acceptance/security tests.
- \`assets/showroom-public.json\` starts with **zero** published products. The viewer shows an honest invitation to try the interactive concept Studio until genuine licensed photo sets are supplied.

## Exact-media contract
Approved source records require \`status=published\`, opaque public ID, exact manufacturer/model/variant identity, public evidence labels, public rights source and valid checked date, 2-48 approved media angles. An accessory configuration requires independently approved accessory identity, verified pairing, image rights and alignment review; its photo frames match each base angle by name and order.

Only publicly allowlisted fields are exported. Never expose dealer costs, internal UPC/source offers, customer details, private Passport records or source approval notes. Photos/composites must reside in \`assets/approved/showroom/<public-item-id>/\`, and have actual PNG, JPEG or WebP signatures. No third-party runtime images are loaded.

This is **not** a true 3D engine, a verified all-product fitment database, a claim of a first-ever invention, or a firearm sales workflow. A photo can show appearances but does not guarantee safety; each pairing requires qualified evidence.

## Publishing workflow (after actual media and rights exist)
1. Acquire exact-model images with permitted use; secure rights and record exact identity, per-image alt text and angles. Never use random retailer photos.
2. Approve each composite pairing with exact accessory identity and source evidence; verify image alignment by a human.
3. Keep approval input **outside GitHub**. Run from repository root:
   \`python scripts/test_publish_showroom.py\`
   \`node scripts/test_showroom_contract.mjs\`
4. After explicit human release, use:
   \`python scripts/publish_showroom.py --input <private-json-path> --publish\`
5. Review sanitized \`assets/showroom-public.json\`, assets and privacy compliance. Commit only approved PUBLIC photos and sanitized manifest to a development branch. Run GitHub checks and obtain owner approval for a later live merge.

## Not yet
Real media assets are not available in this development context; no actual product views or accessory composites have been published. Public hosting and the live branch remain unchanged.
