# First real-product photo intake — Stage 12 (development only)

**Scope:** \`site-refresh-v1\`. No changes to public \`main\`, no real product assets published, and no approval inferred from photographs merely being supplied.

## First real set
Start with **2–6 original photos of the same EXACT item** (left, right, front, rear, detail). Photograph a safely handled product against a simple neutral background in steady lighting. Do not substitute retailer stock photos or AI-generated approximations. Photos must be at least 800 pixels on the long side and 400 on the short side.

Verify the exact manufacturer, model and variant independently. If a scoped rifle is the first specimen, photograph it **as actually configured**; do not simulate removing or attaching accessories. Separate with/without accessory visuals require real matching-angle photos and independent pairing approval later.

Remove or obscure visible serial numbers, names, addresses, plates, customer faces and other identifying surroundings before approving the public release. The preparation script strips EXIF camera and GPS metadata but cannot detect visible details in the photo.

## One-command private preparation
From a local checkout of this branch, install the image-processing dependency:

\`\`\`powershell
py -m pip install "Pillow>=11,<13"
\`\`\`

Take original photos, then run (adjust paths and exact product fields):

\`\`\`powershell
py scripts/prepare_showroom_photos.py --manufacturer "Exact manufacturer" --model "Exact model" --variant "Exact variant" --photo "left=C:\Area33\photos\left.jpg" --photo "right=C:\Area33\photos\right.jpg" --out "C:\Area33-private\showroom-reviews"
\`\`\`

It produces a **private review folder outside the GitHub working copy**, containing optimized WebP photos, \`review.html\` for an offline visual check, \`private-review.json\` with all release approvals **false**, and \`NEXT_STEPS.txt\`.

## Approval / promotion path
1. Check every original and converted photograph against exact model identity, ownership/license rights, privacy, quality, accurate angle labels, and permitted use on a public commercial website.
2. For the approved record only, complete the private JSON with actual \`rights_source\`, \`identity_evidence_label\`, \`checked_at\`, \`status: published\` and each relevant independent human approval. Never commit this private JSON to GitHub.
3. Copy **only** its converted \`assets/approved/showroom/<public-id>/\` media folder into the development website checkout.
4. Run the existing rights-gated publisher:
   \`python scripts/publish_showroom.py --input "C:\path\to\private-review.json" --publish\`.
5. Review public output, inspect the real viewer, and run all tests. Commit **only** the reviewed sanitized media and public manifest to the **development branch**, not live \`main\`. Obtain separate owner launch approval before merge/deploy.

Uploading a product photograph into a chat, a filesystem, or a private review package does **not** by itself grant permission for public website publication.

## Verification
\`python -m unittest discover -s scripts -p "test_*.py" -v\` and \`node scripts/test_showroom_contract.mjs\`. The photo intake tests create synthetic **test-only** pixels in a temporary directory and confirm EXIF removal, draft-only status, image validation and no overwrites. They do not constitute a genuine licensed product photo set.
