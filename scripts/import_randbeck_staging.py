#!/usr/bin/env python3
"""Bridge verified private Randbeck RSR staging into Area 33's REAL catalog workflow.

Generates the existing site's owner-review draft format and exception report.
No sale, rights, content or owner approvals are ever inferred or set true.
No source photos are copied to public assets, no site/manifest writes or deploy.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import hmac
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets

from PIL import Image, UnidentifiedImageError

SITE = Path(__file__).resolve().parents[1]
SOURCE_SCHEMA = "randbeck.area33.private_catalog_staging.v1"
ID = re.compile(r"^catalog_[a-f0-9]{20}$")
SHA = re.compile(r"^[a-f0-9]{64}$")
SKU = re.compile(r"^[A-Za-z0-9#][A-Za-z0-9._-]{0,63}$")
JPEG = re.compile(r"^[A-Za-z0-9#][A-Za-z0-9._-]{0,110}\.jpe?g$", re.I)
MAX_ITEMS = 200
MAX_SOURCE_BYTES = 16_000_000
Image.MAX_IMAGE_PIXELS = 40_000_000

# Source-category -> proposed *editorial* type only. Must be verified before release.
TYPE_SUGGESTIONS = {
    "Long Guns": "complete",
    "Handguns": "complete",
    "Ammunition": "ammunition",
    "Grips, Pads, Stocks, Bipods": "part",
    "Parts": "part",
    "Magazines": "accessory",
    "Optical Accessories": "accessory",
    "Holsters & Pouches": "accessory",
    "Barrels, Choke Tubes, & Muzzle Devices": "part",
    "Optics": "accessory",
}
IDENTITY_FLAGS = {
    "missing_or_invalid_upc",
    "conflicting_product_identity_on_upc",
    "missing_exact_manufacturer_model_or_part_number",
}


class BridgeError(ValueError):
    pass


def _outside_site(path: Path, *, should_exist: bool = True) -> Path:
    value = path.expanduser().resolve()
    if value == SITE or value.is_relative_to(SITE):
        raise BridgeError("Private source/output may not be inside website repository")
    if any((p / ".git").exists() for p in (value, *value.parents)):
        raise BridgeError("Private source/output may not be inside any Git checkout")
    if any(p.lower() in {"public", "assets", "dist", "wwwroot"} for p in value.parts):
        raise BridgeError("Private data must not be saved in public asset folders")
    if should_exist and not value.exists():
        raise BridgeError("Required private input is unavailable")
    return value


def _clean(text: object, limit=160) -> str:
    if not isinstance(text, str):
        return ""
    val = " ".join(text.split())
    if len(val) > limit or any(ord(c) < 32 for c in val):
        return ""
    return val


def _identity(rec: dict) -> tuple[str, str, str, str]:
    return (
        _clean(rec.get("upc"), 14),
        _clean(rec.get("manufacturer"), 100).casefold(),
        _clean(rec.get("manufacturer_part_number"), 120).casefold(),
        _clean(rec.get("model"), 120).casefold(),
    )


def _gtin_valid(value: str) -> bool:
    if not re.fullmatch(r"\d{12,14}", value):
        return False
    total = sum(
        int(c) * (3 if i % 2 == 0 else 1)
        for i, c in enumerate(reversed(value[:-1]))
    )
    return (10 - total % 10) % 10 == int(value[-1])


def _key_file(path: Path) -> bytes:
    path = _outside_site(path, should_exist=False)
    if path.exists():
        if path.is_symlink() or not path.is_file():
            raise BridgeError("Private catalog identity key must be a regular file")
        if path.stat().st_size != 32:
            raise BridgeError("Private catalog identity key must be 32 bytes")
        return path.read_bytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = secrets.token_bytes(32)
    try:
        with path.open("xb") as output:
            output.write(data)
    except FileExistsError:
        return _key_file(path)
    return data


def _source_file(root: Path, sku: str, rec: dict) -> Path:
    raw = rec.get("private_relative_file")
    if not isinstance(raw, str) or "\\" in raw:
        raise BridgeError("Source image path missing or invalid")
    expected = PurePosixPath("media", sku, PurePosixPath(raw).name)
    if (PurePosixPath(raw) != expected or not JPEG.fullmatch(expected.name)
            or not SKU.fullmatch(sku)):
        raise BridgeError("Source image path does not match exact RSR SKU")
    path = root.joinpath(*expected.parts)
    if (path.is_symlink() or path.parent.is_symlink() or
            not path.is_file() or not path.resolve().is_relative_to(root)):
        raise BridgeError("Source photo missing, symlinked, or outside private batch")
    if not 12 <= path.stat().st_size <= MAX_SOURCE_BYTES:
        raise BridgeError("Private JPEG size out of bounds")
    sha = rec.get("sha256")
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise BridgeError("Missing verified image hash")
    if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
        raise BridgeError("Source image SHA-256 mismatch")
    try:
        with Image.open(path) as img:
            if img.format != "JPEG":
                raise BridgeError("Source format is not JPEG")
            size = img.size
            exif = bool(img.getexif())
            img.verify()
        with Image.open(path) as img:
            img.load()
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as err:
        raise BridgeError("Original JPEG cannot be decoded") from err
    if (size != (rec.get("width"), rec.get("height"))
            or size[0] < 300 or size[1] < 200):
        raise BridgeError("Original thumbnail dimensions do not match verified evidence")
    if exif or rec.get("exif_present") is not False:
        raise BridgeError("EXIF-bearing media requires separate review")
    return path.resolve()


def build(
    staging_file: Path, batch_root: Path, identity_key: bytes
) -> tuple[list[dict], dict]:
    if not isinstance(identity_key, bytes) or len(identity_key) != 32:
        raise BridgeError("32-byte private identity key required")
    staging_file = _outside_site(staging_file)
    batch_root = _outside_site(batch_root)
    payload = json.loads(staging_file.read_text(encoding="utf-8"))
    if (payload.get("schema") != SOURCE_SCHEMA or payload.get("source") != "RSR"
            or payload.get("publication_enabled") is not False
            or payload.get("media_rights_approved") is not False
            or payload.get("source_offer_verified") is not False):
        raise BridgeError("Not an unpublished, private Randbeck staging report")
    rows = payload.get("items")
    if (not isinstance(rows, list) or not 1 <= len(rows) <= MAX_ITEMS
            or payload.get("products_staged") != len(rows)):
        raise BridgeError("Unexpected private product staging records")
    groups: dict[tuple, list[dict]] = defaultdict(list)
    by_upc: dict[str, set[tuple]] = defaultdict(set)
    for rec in rows:
        if not isinstance(rec, dict) or rec.get("publication_approved") is not False:
            raise BridgeError("Invalid, previously approved or malformed product record")
        identity = _identity(rec)
        groups[identity].append(rec)
        if _gtin_valid(identity[0]):
            by_upc[identity[0]].add(identity)

    drafts, exceptions, seen_id = [], [], set()
    for identity, source_items in sorted(groups.items(), key=lambda r: r[0]):
        first = source_items[0]
        reasons = set()
        if not _gtin_valid(identity[0]):
            reasons.add("invalid_gtin")
        if len(by_upc.get(identity[0], ())) > 1:
            reasons.add("same_gtin_conflicting_exact_variant")
        if not all(identity):
            reasons.add("missing_manufacturer_mpn_or_model")
        if len({rec.get("source_category") for rec in source_items}) != 1:
            reasons.add("cross_record_category_conflict")
        images = []
        hashes = set()
        for rec in source_items:
            sku = rec.get("source_sku")
            if not isinstance(sku, str) or not SKU.fullmatch(sku):
                reasons.add("unsafe_source_sku")
                continue
            if rec.get("media_rights_approved") is not False:
                raise BridgeError("Unexpected source-media approval state")
            for flag in rec.get("blockers", []):
                if flag in IDENTITY_FLAGS or flag == "source_exif_requires_review_before_any_public_export":
                    reasons.add("randbeck_" + flag)
            for photo in rec.get("source_media") or []:
                if not photo.get("thumbnail_resolution_candidate"):
                    continue
                try:
                    original = _source_file(batch_root, sku, photo)
                except BridgeError:
                    # A real source tampering exception is serious, never silently skip.
                    raise
                digest = photo["sha256"]
                if digest in hashes:
                    continue
                hashes.add(digest)
                images.append({
                    "angle": "view-" + str(len(images) + 1).zfill(2),
                    "source_path": str(original),
                    "source_sha256": digest,
                    # Owner will check visible variant and override wording if needed.
                    "alt": "Source photograph of " + _clean(first.get("manufacturer"), 90) +
                           " " + _clean(first.get("model"), 90),
                })
                if len(images) == 8:
                    break
        if not images:
            reasons.add("no_usable_verified_source_photo")
        category = _clean(first.get("source_category"), 100)
        kind = TYPE_SUGGESTIONS.get(category, "")
        if not kind:
            reasons.add("unknown_public_category_mapping")
        if reasons:
            exceptions.append({
                "upc": identity[0],
                "manufacturer": _clean(first.get("manufacturer"), 100),
                "model": _clean(first.get("model"), 120),
                "source_skus": sorted({str(x.get("source_sku") or "") for x in source_items}),
                "reasons": sorted(reasons),
                "owner_review_required": True,
                "publication_approved": False,
            })
            continue
        opaque = "catalog_" + hmac.new(
            identity_key, "\x1f".join(identity).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()[:20]
        if not ID.fullmatch(opaque) or opaque in seen_id:
            raise BridgeError("Catalog public identity collision")
        seen_id.add(opaque)
        drafts.append({
            "id": opaque,
            "status": "draft",
            "manufacturer": _clean(first.get("manufacturer"), 100),
            "model": _clean(first.get("model"), 120),
            # Source-derived proposed description; requires explicit content approval.
            "description": _clean(first.get("description"), 200),
            "variant": "",
            "category": category,
            "product_type": kind,
            "rights_source": "",
            "identity_evidence_label": "",
            "source_checked_at": "",
            "photos": images,
            "approvals": {
                "owner_publication": False,
                "exact_identity": False,
                "media_rights": False,
                "content_review": False,
                "offered_for_sale": False,
            },
        })
    diag = {
        "schema": "randbeck.area33.private_catalog_bridge_report.v1",
        "source": "RSR",
        "publication_enabled": False,
        "source_products": len(rows),
        "exact_identity_groups": len(groups),
        "review_drafts_generated": len(drafts),
        "quarantined_identity_or_media_groups": len(exceptions),
        "exception_reason_counts": dict(sorted(Counter(
            reason for entry in exceptions for reason in entry["reasons"]
        ).items())),
        "exceptions": exceptions,
        "note": (
            "PRIVATE DRAFTS only. Proposed categories and source labels require "
            "owner review. No actual source/category photo license, sale "
            "availability, identity or publication approval has been granted."
        ),
    }
    return drafts, diag


def write_private_bridge(
    staging: Path, root: Path, output: Path, key_path: Path
):
    output = _outside_site(output, should_exist=False)
    if output.exists():
        raise BridgeError("Private bridge output exists; refusing overwrite")
    # Resolve and validate all input and media before any destination directory.
    key = _key_file(key_path)
    drafts, report = build(staging, root, key)
    output.mkdir(parents=True, exist_ok=False)
    (output / "catalog-private-exceptions.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    for index in range(0, len(drafts), 100):
        part = index // 100 + 1
        (output / f"catalog-approval-template-part-{part:03d}.json").write_text(
            json.dumps(drafts[index:index + 100], indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    (output / "READ_ME_FIRST.txt").write_text(
        "PRIVATE Randbeck-to-Area33 source integration. No approved items.\n"
        "Owner must independently confirm exact variant, source image rights,\n"
        "photo content and offered-for-sale status before any publication.\n"
        "Keep files and private ID key outside Git and public website assets.\n"
        "Public site remains approved-only and unchanged.\n",
        encoding="utf-8",
    )
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--batch-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--identity-key", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = write_private_bridge(
            args.staging, args.batch_root, args.out, args.identity_key
        )
    except (BridgeError, OSError, ValueError) as exc:
        parser.error(str(exc))
    print("Real Area 33 catalog intake from Randbeck:")
    print(f"  Source products: {report['source_products']}")
    print(f"  Exact identity groups: {report['exact_identity_groups']}")
    print(f"  Existing owner-review workflow drafts: {report['review_drafts_generated']}")
    print(f"  Identity/media exception groups: {report['quarantined_identity_or_media_groups']}")
    print("  Exception reasons:", report["exception_reason_counts"])
    print("No owner approvals set, no public images copied, no site files changed.")


if __name__ == "__main__":
    main()
