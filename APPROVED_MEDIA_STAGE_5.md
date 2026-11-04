# Stage 5 — Approval-gated interactive media viewer

**Built:** A real multi-frame media viewer integrated into the Experience Lab. Includes rotation via slider, buttons, keyboard arrows and swipe gesture; optional source-linked feature hotspots; photo load failure fallback; responsive and keyboard-accessible controls.

**No media published:** `assets/approved-media-manifest.json` intentionally contains `products: []`. Therefore the user sees a truthful empty state, not a fabricated firearm or a fake working product visualization. A rotating set becomes usable only after assets are approved.

## Manifest entry requirements
```json
{
  "id": "opaque-public-id",
  "manufacturer": "Approved manufacturer",
  "model": "Exact model",
  "variant": "Exact variant",
  "status": "published",
  "rights": "approved",
  "rights_source": "Actual licensing or ownership evidence reference",
  "exact_identity_verified": true,
  "identity_evidence": "Record of exact identity verification",
  "publication_approved": true,
  "checked_at": "2026-10-26",
  "frames": [
    {"path": "assets/approved/unique-id/frame-01.webp", "alt": "Rights-cleared exact item, front-left"},
    {"path": "assets/approved/unique-id/frame-02.webp", "alt": "Rights-cleared exact item, front-right"}
  ],
  "hotspots": [
    {"x": 50, "y": 45, "label": "Documented feature", "note": "Approved factual explanation", "evidence_label": "Source reference"}
  ]
}
```

This is an illustrative contract, NOT an approved item or product claim. Frame paths must remain within local `assets/approved/`, in PNG/JPEG/WebP format, with no query or path traversal. The client rejects entries without all approval markers, exact identity and frame metadata. Hotspots are editorial notes, not validated fitment.

**Important:** Client validation provides display defense only. Actual approval, media rights, cross-tenant separation, correctness, and legal claims MUST be established in Randbeck's backend and publishing workflow, with a signed-off export manifest. Never rely on client-side flags as authorization.

## Next gating work
- Populate a first rights-cleared multi-angle set with verified exact model, vendor usage terms and linked evidence.
- Add tests with an isolated mocked manifest: empty state, malformed inputs, navigation, image failure, reduced motion and keyboard support.
- Consider stronger media framing and controls after real assets exist. No suppressor/optic visual overlays until exact combination assets and verification are approved.
- All work remains on `site-refresh-v1`; do not merge or publish without owner approval.
