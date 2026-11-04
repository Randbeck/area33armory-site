#!/usr/bin/env python3
"""Prepare PRIVATE Area 33 catalog approval drafts from a Randbeck media handoff.

This never publishes or writes media into the public site. It does not approve
any product, sale eligibility, photo rights or fit/variant claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import secrets

ID_RE = re.compile(r"^catalog_[a-f0-9]{20}$")
FILE_RE = re.compile(r"^[A-Za-z0-9#][A-Za-z0-9._-]{0,110}\.jpe?g$", re.I)
HERE = Path(__file__).resolve().parents[1]


class DraftError(ValueError):
    pass


def prepare(handoff: Path, media_root: Path, output_dir: Path) -> Path:
    handoff = handoff.expanduser().resolve()
    media_root = media_root.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    if output_dir.exists():
        raise DraftError("Approval draft output folder already exists")
    if output_dir == HERE or output_dir.is_relative_to(HERE):
        raise DraftError("Private approvals may not be written in the website repository")
    if media_root == HERE or media_root.is_relative_to(HERE):
        raise DraftError("Media root must be outside the public website repository")
    if any((p / ".git").exists() for p in (output_dir, *output_dir.parents)):
        raise DraftError("Private approval draft must not be saved inside a Git repository")
    payload = json.loads(handoff.read_text(encoding="utf-8"))
    if payload.get("schema") != "randbeck.area33_private_handoff.v1" or payload.get("publication_enabled") is not False:
        raise DraftError("Source is not a private, unpublished Randbeck handoff")
    items = payload.get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= 100:
        raise DraftError("Expected 1-100 private handoff products")
    draft = []
    for item in items:
        if item.get("publication_approved", False) or item.get("public_export_allowed") is not False:
            raise DraftError("Source handoff is not unapproved")
        sku = str(item.get("source_sku") or "")
        if not re.fullmatch(r"[A-Za-z0-9#][A-Za-z0-9._-]{0,63}", sku):
            raise DraftError("Invalid RSR source SKU")
        photos = []
        for index, photo in enumerate(item.get("frames") or [], 1):
            filename = str(photo.get("source_filename") or "")
            rel = str(photo.get("source_private_relative_path") or "")
            if not FILE_RE.fullmatch(filename) or PurePosixPath(rel).parts != (sku, filename):
                raise DraftError("Source photo path does not match exact RSR SKU")
            source = (media_root / rel).resolve()
            if not source.is_relative_to(media_root) or not source.is_file() or source.is_symlink():
                raise DraftError("Source photo missing or escapes private folder")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if digest != photo.get("sha256"):
                raise DraftError("Private source image changed after review")
            photos.append({
                "angle": f"view-{index:02d}",
                "source_path": str(source),
                "source_sha256": digest,
                "alt": "",
            })
        draft.append({
            "id": "catalog_" + secrets.token_hex(10),
            "status": "draft",
            "manufacturer": str(item.get("manufacturer") or ""),
            "model": str(item.get("model") or ""),
            "variant": "",
            "category": "",
            "product_type": "",
            "rights_source": "",
            "identity_evidence_label": "",
            "source_checked_at": "",
            "photos": photos,
            "approvals": {
                "owner_publication": False,
                "exact_identity": False,
                "media_rights": False,
                "content_review": False,
                "offered_for_sale": False,
            },
        })
    output_dir.mkdir(parents=True, exist_ok=False)
    destination = output_dir / "catalog-approval-template.json"
    destination.write_text(json.dumps(draft, indent=2) + "\n", encoding="utf-8")
    (output_dir / "READ_ME_FIRST.txt").write_text(
        "PRIVATE DRAFT. No images or listings are approved.\n"
        "Check exact model/variant and any compatibility claims, RSR image reuse rights,\n"
        "the proposed live sale listing, visible photo details and each source image.\n"
        "Complete all required fields/approvals ONLY after actual owner review.\n"
        "Source paths and SHA-256 values MUST remain private and off GitHub.\n"
        "The publisher requires manual --publish and has additional validation.\n",
        encoding="utf-8",
    )
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handoff", required=True, type=Path)
    parser.add_argument("--media-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = prepare(args.handoff, args.media_root, args.out)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print("PRIVATE approval template: " + str(result))
    print("All approvals false. No public assets or listings created.")


if __name__ == "__main__":
    main()
