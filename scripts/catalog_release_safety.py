"""Private revocation safeguards shared by refresh, preflight and rollback.

An empty hold file does NOT attest that any media/license is authorized.
This file can only DENY further use; individual listing approvals and current
rights/legal restrictions remain separately required.
"""
from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import re

HEX = re.compile(r"^[0-9a-f]{64}$")
ID = re.compile(r"^catalog_[0-9a-f]{20}$")
SCHEMA = "area33.catalog.private_rights_holds.v1"
KINDS = {"image_sha256", "manufacturer_media", "manufacturer_sales", "catalog_id"}


class CatalogRightsHoldError(ValueError):
    pass


def private_regular_file(path: Path) -> Path:
    actual = Path(path).expanduser().resolve()
    if not actual.is_file() or Path(path).is_symlink() or actual.stat().st_size > 4_000_000:
        raise CatalogRightsHoldError("Private rights hold file missing, linked or too large")
    if any((p / ".git").exists() for p in (actual, *actual.parents)):
        raise CatalogRightsHoldError("Rights holds must remain outside Git")
    if any(part.lower() in ("public","assets","dist","wwwroot") for part in actual.parts):
        raise CatalogRightsHoldError("Rights holds must not be stored in website assets")
    return actual


def read_rights_holds(path: Path) -> dict:
    source = private_regular_file(path)
    raw = source.read_bytes()
    data = json.loads(raw)
    if (not isinstance(data, dict) or set(data) != {
        "schema", "reviewer", "reviewed_on", "holds"
    } or data["schema"] != SCHEMA or
            not isinstance(data["reviewer"], str) or
            not 3 <= len(data["reviewer"].strip()) <= 120 or
            not isinstance(data["holds"], list) or len(data["holds"]) > 100000):
        raise CatalogRightsHoldError("Invalid private rights hold ledger")
    try:
        checked = date.fromisoformat(data["reviewed_on"])
    except (TypeError, ValueError) as exc:
        raise CatalogRightsHoldError("Invalid private rights review date") from exc
    if checked > date.today():
        raise CatalogRightsHoldError("Rights review date is in the future")
    seen = set()
    for item in data["holds"]:
        if not isinstance(item, dict) or set(item) != {"kind", "value", "reason", "recorded_on"}:
            raise CatalogRightsHoldError("Invalid rightsholder hold record")
        kind, value = item["kind"], item["value"]
        if kind not in KINDS or not isinstance(value, str):
            raise CatalogRightsHoldError("Unrecognized rights hold category/value")
        if kind == "image_sha256" and not HEX.fullmatch(value):
            raise CatalogRightsHoldError("Invalid held source-image SHA-256")
        if kind == "catalog_id" and not ID.fullmatch(value):
            raise CatalogRightsHoldError("Invalid held catalog ID")
        if kind in ("manufacturer_media", "manufacturer_sales") and not (
            2 <= len(value.strip()) <= 100 and value == value.strip()
        ):
            raise CatalogRightsHoldError("Exact manufacturer name required")
        if ((kind, value.casefold()) in seen or
                not isinstance(item["reason"], str) or
                not 3 <= len(item["reason"].strip()) <= 200):
            raise CatalogRightsHoldError("Missing explanation or repeated held right")
        try:
            logged = date.fromisoformat(item["recorded_on"])
        except (TypeError, ValueError) as exc:
            raise CatalogRightsHoldError("Invalid held-right date") from exc
        if logged > checked:
            raise CatalogRightsHoldError("A right cannot be held after review date")
        seen.add((kind, value.casefold()))
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "path": str(source),
        "reviewed_on": data["reviewed_on"],
        "hold_count": len(data["holds"]),
        "holds": data["holds"],
    }


def blocked_records(products: list[dict], provenance: dict, holds: dict) -> dict[str, list[str]]:
    image_hashes = {x["value"] for x in holds["holds"] if x["kind"] == "image_sha256"}
    media_brands = {x["value"].casefold() for x in holds["holds"]
                    if x["kind"] == "manufacturer_media"}
    sales_brands = {x["value"].casefold() for x in holds["holds"]
                    if x["kind"] == "manufacturer_sales"}
    ids = {x["value"] for x in holds["holds"] if x["kind"] == "catalog_id"}
    problems = {}
    for product in products:
        ident = product["id"]
        brand = product["manufacturer"].casefold()
        mode = product["presentation_mode"]
        reasons = []
        if ident in ids:
            reasons.append("blocked_catalog_id")
        if brand in sales_brands:
            reasons.append("manufacturer_sales_restricted")
        if mode == "image":
            if brand in media_brands:
                reasons.append("manufacturer_media_restricted")
            entry = provenance[ident]
            if any(image["original_sha256"] in image_hashes for image in entry["images"]):
                reasons.append("source_photo_rights_held")
        if reasons:
            problems[ident] = sorted(reasons)
    return problems


def reject_held_products(products: list[dict], provenance: dict, holds: dict) -> None:
    blocked = blocked_records(products, provenance, holds)
    if blocked:
        counts = sorted({reason for reasons in blocked.values() for reason in reasons})
        raise CatalogRightsHoldError(
            f"Rights hold blocks {len(blocked)} approved record(s): {', '.join(counts)}"
        )
