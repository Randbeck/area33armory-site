#!/usr/bin/env python3
"""Publish only independently reviewed, owner-approved catalog thumbnails.

Reads an approval bundle kept OUTSIDE this site repository. Writes an
allowlisted public catalog manifest and exact-product local JPEG copies only
with --publish; live deployment remains a separate Git branch/owner decision.
No product price, availability, checkout, dealer data or private IDs export.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent.parent
ASSET_ROOT = ROOT / "assets" / "approved" / "catalog"
MANIFEST = ROOT / "assets" / "catalog-public.json"
ID = re.compile(r"^catalog_[a-f0-9]{20}$")
TEXT = re.compile(r"^[^\x00-\x1f]{1,200}$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SHA = re.compile(r"^[a-f0-9]{64}$")
ANGLE = re.compile(r"^[a-z0-9_-]{2,30}$")
MAX_JPEG_BYTES = 12_000_000
MIN_WIDTH = 300
MIN_HEIGHT = 200
TYPES = {"complete", "part", "accessory", "ammunition", "other"}
REQUIRED_APPROVALS = (
    "owner_publication", "exact_identity", "media_rights",
    "content_review", "offered_for_sale",
)
# Text-only needs separate evidence: owner-generated wording, no supplier
# photo, and no invented image copyright approval.
BASE_APPROVALS = (
    "owner_publication", "exact_identity", "content_review", "offered_for_sale",
)
Image.MAX_IMAGE_PIXELS = 40_000_000


class CatalogPublicationError(ValueError):
    pass


def clean_text(record: dict, key: str, limit: int = 120) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise CatalogPublicationError(f"Missing text: {key}")
    result = " ".join(value.split())
    if not result or len(result) > limit or not TEXT.fullmatch(result):
        raise CatalogPublicationError(f"Invalid public text: {key}")
    return result


def optional_text(record: dict, key: str, limit: int = 120) -> str:
    value = record.get(key, "")
    if value is None or value == "":
        return ""
    return clean_text(record, key, limit)


def check_date(record: dict, key: str) -> str:
    value = clean_text(record, key, 10)
    if not ISO_DATE.fullmatch(value):
        raise CatalogPublicationError("Invalid date format")
    parsed = date.fromisoformat(value)
    if parsed > date.today():
        raise CatalogPublicationError("Future evidence date")
    return value


def approved_record(record: dict, index: int, source_root: Path):
    if not isinstance(record, dict) or record.get("status") != "published":
        raise CatalogPublicationError("All records must be marked published after human review")
    listing_mode = record.get("listing_mode", "image")
    if listing_mode not in ("image", "text_only"):
        raise CatalogPublicationError("Unsupported explicit catalog listing mode")
    approvals = record.get("approvals")
    if (not isinstance(approvals, dict) or set(approvals) != set(REQUIRED_APPROVALS)
            or any(type(value) is not bool for value in approvals.values())
            or any(approvals[key] is not True for key in BASE_APPROVALS)):
        raise CatalogPublicationError("Missing independent owner/identity/content/sale approval")
    if listing_mode == "image" and approvals["media_rights"] is not True:
        raise CatalogPublicationError("Product photographs require separately confirmed image rights")
    if listing_mode == "text_only" and approvals["media_rights"] is not False:
        raise CatalogPublicationError("Text-only listing cannot assert photograph rights")
    product_id = clean_text(record, "id", 64)
    if not ID.fullmatch(product_id):
        raise CatalogPublicationError("Invalid opaque public ID")
    manufacturer = clean_text(record, "manufacturer", 100)
    model = clean_text(record, "model", 120)
    variant = optional_text(record, "variant", 100)
    description = optional_text(record, "description", 200)
    category = clean_text(record, "category", 100)
    product_type = clean_text(record, "product_type", 20)
    if product_type not in TYPES:
        raise CatalogPublicationError("Unsupported public product type")
    identity = clean_text(record, "identity_evidence_label", 160)
    checked = check_date(record, "source_checked_at")
    photos = record.get("photos")
    if listing_mode == "text_only":
        if photos != []:
            raise CatalogPublicationError("Text-only listing must contain zero images")
        if record.get("rights_source", "") != "":
            raise CatalogPublicationError("Text-only listing must not claim image rights")
        if record.get("content_origin") != "owner_written":
            raise CatalogPublicationError("Text-only copy must be independently owner-written and verified")
    else:
        rights = clean_text(record, "rights_source", 160)
        if not isinstance(photos, list) or not 1 <= len(photos) <= 8:
            raise CatalogPublicationError("Approved image listing needs 1-8 exact photos")
    frames = []
    seen_angles = set()
    for n, photo in enumerate(photos, 1):
        if not isinstance(photo, dict):
            raise CatalogPublicationError("Invalid photo record")
        angle = clean_text(photo, "angle", 30)
        if not ANGLE.fullmatch(angle) or angle in seen_angles:
            raise CatalogPublicationError("Invalid/duplicate image angle")
        seen_angles.add(angle)
        original = clean_text(photo, "source_path", 1000)
        source = Path(original).expanduser().resolve()
        if source == ROOT or source.is_relative_to(ROOT):
            raise CatalogPublicationError("Private source images must remain outside the public repository")
        if any((parent / ".git").exists() for parent in (source, *source.parents)):
            raise CatalogPublicationError("Private source image must not originate inside a Git checkout")
        if Path(original).is_symlink() or source.is_symlink() or not source.is_file():
            raise CatalogPublicationError("Missing or linked private source image")
        if source.suffix.lower() not in (".jpg", ".jpeg"):
            raise CatalogPublicationError("Only original source JPEGs are accepted")
        size = source.stat().st_size
        if not 12 <= size <= MAX_JPEG_BYTES:
            raise CatalogPublicationError("Original photo size invalid")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        expected = clean_text(photo, "source_sha256", 64)
        if not SHA.fullmatch(expected) or digest != expected:
            raise CatalogPublicationError("Source photo differs from reviewed SHA-256")
        try:
            with Image.open(source) as image:
                if image.format != "JPEG":
                    raise CatalogPublicationError("Original photo is not a JPEG")
                width, height = image.size
                if width < MIN_WIDTH or height < MIN_HEIGHT:
                    raise CatalogPublicationError("Photo too small even for thumbnail review")
                # Do not repurpose source EXIF/GPS or modify supplier images.
                if image.getexif():
                    raise CatalogPublicationError("Source EXIF present: separate rights/metadata review required")
                image.verify()
        except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
            raise CatalogPublicationError("Cannot verify original JPEG") from exc
        alt = clean_text(photo, "alt", 160)
        name = f"view-{n:02d}.jpg"
        public_path = f"assets/approved/catalog/{product_id}/{name}"
        frames.append({
            "source": source,
            "dest": ASSET_ROOT / product_id / name,
            "public": {"url": public_path, "alt": alt, "rights": "approved"},
        })
    public_record = {
        "id": product_id,
        "manufacturer": manufacturer,
        "model": model,
        "variant": variant,
        "description": description,
        "presentation_mode": listing_mode,
        "category": category,
        "product_type": product_type,
        "specifications": [],
        "evidence": [{"source_label": identity, "checked_at": checked}],
        "images": [frame["public"] for frame in frames],
        "publication_updated_at": datetime.now(timezone.utc).isoformat(),
    }
    return public_record, frames


def build(approval_file: Path):
    input_file = approval_file.expanduser().resolve()
    if input_file == ROOT or input_file.is_relative_to(ROOT):
        raise CatalogPublicationError("Private approvals must live outside the public repository")
    if any((parent / ".git").exists() for parent in (input_file, *input_file.parents)):
        raise CatalogPublicationError("Private approval file may not live inside a Git repository")
    rows = json.loads(input_file.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        raise CatalogPublicationError("Expected 1-100 owner-reviewed product records")
    public, frames, seen = [], [], set()
    for i, raw in enumerate(rows, 1):
        record, source_images = approved_record(raw, i, input_file.parent)
        if record["id"] in seen:
            raise CatalogPublicationError("Duplicate public product ID")
        seen.add(record["id"])
        public.append(record)
        frames.extend(source_images)
    manifest = {
        "schema": "area33.catalog.public.v1",
        "as_of": datetime.now(timezone.utc).isoformat(),
        "coverage": {
            "description": "Only individually approved Area 33 product listings; not all distributor inventory."
        },
        "items": public,
    }
    return manifest, frames


def publish(input_file: Path, do_publish: bool = False):
    payload, frames = build(input_file)  # Full integrity/approval verification before any file copy.
    if not do_publish:
        return payload
    if MANIFEST.exists():
        existing = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if existing.get("schema") != "area33.catalog.public.v1":
            raise CatalogPublicationError("Unexpected existing public manifest")
        if existing.get("items"):
            raise CatalogPublicationError("Existing public products: refuse to replace or retract without review")
    for frame in frames:
        if frame["dest"].exists():
            raise CatalogPublicationError("Product media destination already exists; refusing overwrite")
    staged = []
    try:
        for frame in frames:
            target = frame["dest"]
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(".jpg." + uuid4().hex + ".tmp")
            shutil.copyfile(frame["source"], tmp)  # Preserve unchanged licensed source pixels.
            if hashlib.sha256(tmp.read_bytes()).hexdigest() != hashlib.sha256(frame["source"].read_bytes()).hexdigest():
                raise CatalogPublicationError("Staged photo changed")
            tmp.replace(target)
            staged.append(target)
        MANIFEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception:
        for path in staged:
            path.unlink(missing_ok=True)
        raise
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path,
                        help="Human-approved JSON kept outside the site repository")
    parser.add_argument("--publish", action="store_true",
                        help="Explicit owner-authorized creation of approved site assets")
    args = parser.parse_args()
    if not args.publish:
        parser.error("Explicit --publish is required; no automatic publication")
    try:
        payload = publish(args.input, do_publish=True)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Prepared {len(payload['items'])} approved catalog records in local site working copy.")
    print("Review files, tests and Git diff; live deployment requires separate owner approval.")


if __name__ == "__main__":
    main()
