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


class MediaMetadataReviewRequired(BridgeError):
    """Authentic, unchanged source photo is held for manual metadata inspection."""


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


def _source_file(root: Path, sku: str, rec: dict, *, allow_exif: bool = False) -> Path:
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
    if type(rec.get("exif_present")) is not bool or rec["exif_present"] != exif:
        raise BridgeError("Original source image EXIF evidence disagrees with verification")
    if exif and not allow_exif:
        raise MediaMetadataReviewRequired(
            "EXIF-bearing media requires separate review"
        )
    return path.resolve()


def build(
    staging_file: Path, batch_root: Path, identity_key: bytes,
    *, private_derivatives_root: Path | None = None,
    authorized_scope: dict | None = None,
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
    derivative_audits = []
    scope_eligible_drafts = 0
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
        if authorized_scope is not None:
            for rec in source_items:
                receipt=authorized_scope["eligible_by_sku"].get(rec.get("source_sku"))
                if receipt is None or receipt["status"]!="policy_eligible_private_candidate":
                    reasons.add("not_eligible_under_signed_distributor_scope")
                elif receipt["source_category"]!=rec["source_category"]:
                    reasons.add("scope_category_mismatch")
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
                if flag in IDENTITY_FLAGS:
                    reasons.add("randbeck_" + flag)
                if (flag == "source_exif_requires_review_before_any_public_export"
                        and private_derivatives_root is None):
                    reasons.add("randbeck_" + flag)
            for photo in rec.get("source_media") or []:
                if not photo.get("thumbnail_resolution_candidate"):
                    continue
                try:
                    original = _source_file(batch_root, sku, photo)
                    digest = photo["sha256"]
                except MediaMetadataReviewRequired:
                    if private_derivatives_root is None:
                        reasons.add("photo_exif_metadata_requires_review")
                        continue
                    from private_exif_derivatives import (
                        PrivateDerivativeError, create_private_derivative,
                    )
                    # A private metadata-only copy is an engineering input,
                    # NOT permission to alter supplier images for advertising.
                    source = _source_file(
                        batch_root, sku, photo, allow_exif=True
                    )
                    try:
                        original, digest, evidence = create_private_derivative(
                            source, private_derivatives_root, sku, source.name,
                            photo["sha256"],
                        )
                    except PrivateDerivativeError as exc:
                        # Unsupported orientation/metadata remains held.
                        reasons.add("source_metadata_requires_manual_review")
                        continue
                    derivative_audits.append({
                        "source_sku": sku,
                        "source_name": source.name,
                        **evidence,
                    })
                except BridgeError:
                    # Hash mismatches, path traversal, invalid image bytes
                    # and other evidence tampering remain batch-fatal.
                    raise
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
        if authorized_scope is not None and not reasons:
            grant=authorized_scope["eligible_by_sku"][first["source_sku"]]
            if (grant["proposed_public_type"]!=kind or
                    not grant["proposed_public_category"]):
                reasons.add("scope_public_product_type_conflict")
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
        if authorized_scope is not None:
            scope_eligible_drafts += 1
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
        "groups_held_for_photo_metadata_review": sum(
            any(reason in entry["reasons"] for reason in (
                "photo_exif_metadata_requires_review",
                "randbeck_source_exif_requires_review_before_any_public_export",
                "source_metadata_requires_manual_review",
            ))
            for entry in exceptions
        ),
        "private_metadata_only_derivative_files": len(derivative_audits),
        "private_metadata_derivative_audit": derivative_audits,
        "scope_gate_enabled": authorized_scope is not None,
        "scope_signed_eligible_drafts": scope_eligible_drafts,
        "scope_receipt_eligible_source_products": (
            authorized_scope["eligible_product_count"]
            if authorized_scope is not None else None
        ),
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
    staging: Path, root: Path, output: Path, key_path: Path,
    *, prepare_private_derivatives: bool = False,
    scope_receipt: Path | None = None, scope_ledger: Path | None = None,
    scope_key: Path | None = None,
):
    output = _outside_site(output, should_exist=False)
    if output.exists():
        raise BridgeError("Private bridge output exists; refusing overwrite")
    # Only explicit owner-selected --prepare-private-exif-copies triggers
    # any image processing. Originals remain unchanged, and images remain
    # outside Git/public directories. Without flag, legacy behavior is identical.
    key = _key_file(key_path)
    options=(scope_receipt,scope_ledger,scope_key)
    if 0<sum(v is not None for v in options)<3:
        raise BridgeError("All three signed scope receipt, current ledger and key are required")
    scope=None
    if all(v is not None for v in options):
        from verify_randbeck_scope_receipt import (
            ScopeReceiptError,validate_scoped_receipt,
        )
        scope=validate_scoped_receipt(staging,scope_receipt,scope_ledger,scope_key)
    if prepare_private_derivatives:
        output.mkdir(parents=True, exist_ok=False)
        drafts, report = build(
            staging, root, key,
            private_derivatives_root=output / "private-exif-copies",
            authorized_scope=scope,
        )
    else:
        drafts, report = build(staging, root, key,authorized_scope=scope)
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
    parser.add_argument("--scope-receipt", type=Path,
                        help="Private signed Randbeck cohort eligibility receipt")
    parser.add_argument("--scope-ledger", type=Path,
                        help="Current private owner-signed distributor scope ledger")
    parser.add_argument("--scope-key", type=Path,
                        help="Private shared signature verification key")
    parser.add_argument(
        "--prepare-private-exif-copies", action="store_true",
        help="Explicitly prepare lossless, private APP1/EXIF-cleared copies; never publish",
    )
    args = parser.parse_args(argv)
    try:
        report = write_private_bridge(
            args.staging, args.batch_root, args.out, args.identity_key,
            prepare_private_derivatives=args.prepare_private_exif_copies,
            scope_receipt=args.scope_receipt,
            scope_ledger=args.scope_ledger,
            scope_key=args.scope_key,
        )
    except (BridgeError, OSError, ValueError) as exc:
        parser.error(str(exc))
    print("Real Area 33 catalog intake from Randbeck:")
    print(f"  Source products: {report['source_products']}")
    print(f"  Exact identity groups: {report['exact_identity_groups']}")
    print(f"  Existing owner-review workflow drafts: {report['review_drafts_generated']}")
    print(f"  Identity/media exception groups: {report['quarantined_identity_or_media_groups']}")
    if report["scope_gate_enabled"]:
        print(f"  Signed-scope authorized PRIVATE drafts: {report['scope_signed_eligible_drafts']}")
        print(f"  Eligible source records on signed receipt: {report['scope_receipt_eligible_source_products']}")
    print(f"  Held for photo metadata review: {report['groups_held_for_photo_metadata_review']}")
    print(f"  Private lossless EXIF-cleared photo copies: {report['private_metadata_only_derivative_files']}")
    print("  Exception reasons:", report["exception_reason_counts"])
    print("No owner approvals set, no public images copied, no site files changed.")


if __name__ == "__main__":
    main()
