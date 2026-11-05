#!/usr/bin/env python3
"""Prepare a PRIVATE removal-only replacement catalog after an image-rights issue.

Uses a previously staged, independently approved v2 release plus its private
image provenance. It can only REMOVE affected listings; never grants rights,
changes product text, overwrites old releases, deploys or purges live caches.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import secrets
import shutil
import tempfile

from prepare_approved_catalog_shards import (
    MAX_PRODUCTS, PER_SHARD, RELEASE_SCHEMA, SHARD_SCHEMA,
    ShardedReleaseError, _encode, _private_destination,
)

ID = re.compile(r"^catalog_[a-f0-9]{20}$")
VERSION = re.compile(r"^r[a-f0-9]{20}$")
SHA = re.compile(r"^[a-f0-9]{64}$")
SHARD_PATH = re.compile(r"^assets/catalog-shards/(r[a-f0-9]{20})/part-([0-9]{4})\.json$")
IMAGE_PATH = re.compile(r"^assets/approved/catalog/(catalog_[a-f0-9]{20})/view-0[1-8]\.jpg$")
PUBLIC_RECORD_KEYS = {
    "id","manufacturer","model","variant","description","presentation_mode",
    "category","product_type","specifications","evidence","images","publication_updated_at",
}
PUBLIC_SUMMARY_KEYS = {
    "id","manufacturer","model","variant","description","category","product_type","shard",
}


class PrivateWithdrawalError(ValueError):
    pass


def _read_json(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 30_000_000:
        raise PrivateWithdrawalError("Release evidence file missing, linked or too large")
    return json.loads(path.read_text(encoding="utf-8"))


def _approved_previous(root: Path):
    """Check staged catalog identity/shard hashes and all private provenance."""
    root = Path(root).expanduser().resolve()
    if not root.is_dir() or any((p/".git").exists() for p in (root,*root.parents)):
        raise PrivateWithdrawalError("Expected an existing private release outside Git")
    index = _read_json(root/"assets/catalog-index.v2.json")
    provenance = _read_json(root/"catalog-private-media-provenance.json")
    if (not isinstance(index, dict) or index.get("schema") != RELEASE_SCHEMA
            or not isinstance(index.get("version"), str) or
            not VERSION.fullmatch(index["version"]) or
            not isinstance(index.get("products"), list) or
            not isinstance(index.get("shards"), list) or
            type(index.get("total")) is not int or
            index["total"] != len(index["products"]) or
            index["total"] > MAX_PRODUCTS or len(index["shards"]) > 500):
        raise PrivateWithdrawalError("Invalid previous approved index")
    if (not isinstance(provenance, dict) or
            provenance.get("schema") != "area33.catalog.private_media_provenance.v1"
            or provenance.get("release_version") != index["version"] or
            provenance.get("public_catalog_record_count") != index["total"] or
            not isinstance(provenance.get("records"), list) or
            len(provenance["records"]) != index["total"]):
        raise PrivateWithdrawalError("Missing or mismatched private source-image provenance")
    seen, full, source_images = set(), [], {}
    for shard_no, desc in enumerate(index["shards"]):
        if (not isinstance(desc, dict) or set(desc) != {"url","sha256","count"} or
                not isinstance(desc["url"], str) or
                not isinstance(desc["sha256"], str) or
                not SHA.fullmatch(desc["sha256"]) or
                type(desc["count"]) is not int or
                not 1 <= desc["count"] <= PER_SHARD):
            raise PrivateWithdrawalError("Unrecognized approved shard descriptor")
        matched = SHARD_PATH.fullmatch(desc["url"])
        if (not matched or matched.group(1) != index["version"] or
                int(matched.group(2)) != shard_no + 1):
            raise PrivateWithdrawalError("Untrusted shard URL")
        file = root.joinpath(*Path(desc["url"]).parts)
        if not file.resolve().is_relative_to(root):
            raise PrivateWithdrawalError("Shard escapes private release")
        raw = file.read_bytes()
        if hashlib.sha256(raw).hexdigest() != desc["sha256"]:
            raise PrivateWithdrawalError("Previous approved shard hash mismatch")
        doc = json.loads(raw)
        if (not isinstance(doc, dict) or set(doc) != {"schema","version","items"}
                or doc.get("schema") != SHARD_SCHEMA or
                doc.get("version") != index["version"] or
                not isinstance(doc.get("items"), list) or
                len(doc["items"]) != desc["count"]):
            raise PrivateWithdrawalError("Previous shard content malformed")
        for product in doc["items"]:
            if (not isinstance(product, dict) or set(product) != PUBLIC_RECORD_KEYS
                    or not isinstance(product.get("id"), str) or
                    not ID.fullmatch(product["id"]) or
                    product["id"] in seen or
                    product.get("presentation_mode") not in ("image", "text_only") or
                    not isinstance(product.get("manufacturer"), str) or
                    not 2 <= len(product["manufacturer"]) <= 100 or
                    not isinstance(product.get("images"), list)):
                raise PrivateWithdrawalError("Unexpected or duplicated approved product")
            if product["presentation_mode"] == "text_only" and product["images"]:
                raise PrivateWithdrawalError("Text-only product contains image URLs")
            if product["presentation_mode"] == "image" and not 1 <= len(product["images"]) <= 8:
                raise PrivateWithdrawalError("Approved photo listing missing original images")
            seen.add(product["id"])
            full.append(product)
    if len(full) != index["total"]:
        raise PrivateWithdrawalError("Index count and approved shards differ")
    expected_summaries = []
    for shard_no, offset in enumerate(range(0, len(full), PER_SHARD)):
        for p in full[offset:offset+PER_SHARD]:
            expected_summaries.append({
                "id":p["id"],"manufacturer":p["manufacturer"],"model":p["model"],
                "variant":p["variant"],"description":p["description"],
                "category":p["category"],"product_type":p["product_type"],
                "shard":shard_no,
            })
    if expected_summaries != index["products"]:
        raise PrivateWithdrawalError("Index summary disagrees with the approved shards")
    private_by_id = {}
    for entry in provenance["records"]:
        if (not isinstance(entry, dict) or set(entry) != {
                "id","manufacturer","presentation_mode","rights_source","images"
            } or entry.get("id") not in seen or entry["id"] in private_by_id or
                not isinstance(entry.get("images"), list) or
                not isinstance(entry.get("rights_source"), str)):
            raise PrivateWithdrawalError("Private image provenance missing or corrupted")
        private_by_id[entry["id"]] = entry
    if set(private_by_id) != seen:
        raise PrivateWithdrawalError("Not all approved records have provenance")
    for product in full:
        evidence=private_by_id[product["id"]]
        if (evidence["manufacturer"] != product["manufacturer"] or
                evidence["presentation_mode"] != product["presentation_mode"] or
                len(evidence["images"]) != len(product["images"])):
            raise PrivateWithdrawalError("Image ownership mapping disagrees with approved listing")
        if product["presentation_mode"] == "image" and not evidence["rights_source"].strip():
            raise PrivateWithdrawalError("No private media-rights source on image record")
        for source_img, display_img in zip(evidence["images"],product["images"]):
            if (not isinstance(source_img, dict) or
                    set(source_img) != {"public_url","original_sha256"} or
                    not isinstance(source_img["public_url"], str) or
                    source_img["public_url"] != display_img.get("url") or
                    not isinstance(source_img["original_sha256"], str) or
                    not SHA.fullmatch(source_img["original_sha256"])):
                raise PrivateWithdrawalError("Approved photo URL or source hash changed")
            name=IMAGE_PATH.fullmatch(source_img["public_url"])
            if not name or name.group(1) != product["id"]:
                raise PrivateWithdrawalError("Unsafe or mismatched approved image path")
            source_file=root.joinpath(*Path(source_img["public_url"]).parts)
            if (source_file.is_symlink() or not source_file.is_file() or
                    not source_file.resolve().is_relative_to(root) or
                    hashlib.sha256(source_file.read_bytes()).hexdigest()
                        != source_img["original_sha256"]):
                raise PrivateWithdrawalError("Previous approved image bytes have changed")
            source_images[source_img["public_url"]] = source_file
    return index, full, private_by_id, source_images


def stage_media_withdrawal(
    previous: Path, output: Path, *, manufacturer: str | None = None,
    image_sha256: str | None = None, include_text_only: bool = False,
    reviewer: str, reason: str, reviewed_on: str,
):
    """Generate an atomic, private full-replacement snapshot by removing only."""
    if bool(manufacturer) == bool(image_sha256):
        raise PrivateWithdrawalError("Specify exactly one manufacturer or original image SHA-256")
    if include_text_only and not manufacturer:
        raise PrivateWithdrawalError("Text-only removal requires explicit manufacturer selection")
    for value in (reviewer, reason):
        if (not isinstance(value, str) or not 3 <= len(value.strip()) <= 160
                or any(ord(c) < 32 for c in value)):
            raise PrivateWithdrawalError("Reviewer and reason are required for rights withdrawal")
    if manufacturer and (not 2 <= len(manufacturer.strip()) <= 100):
        raise PrivateWithdrawalError("Manufacturer must be an exact reviewed name")
    if image_sha256 and not SHA.fullmatch(image_sha256):
        raise PrivateWithdrawalError("Invalid exact source image hash")
    try:
        reviewed=date.fromisoformat(reviewed_on)
    except (TypeError, ValueError) as exc:
        raise PrivateWithdrawalError("Invalid review date") from exc
    if reviewed > date.today():
        raise PrivateWithdrawalError("Cannot record a future rights decision")
    output=_private_destination(Path(output))
    previous=Path(previous).expanduser().resolve()
    if output.is_relative_to(previous) or previous.is_relative_to(output):
        raise PrivateWithdrawalError("Previous release and output cannot contain each other")
    index, products, provenance, images = _approved_previous(previous)
    affected=[]
    for product in products:
        record=provenance[product["id"]]
        if manufacturer:
            selected=product["manufacturer"].casefold() == manufacturer.strip().casefold()
            if not include_text_only:
                selected=selected and product["presentation_mode"] == "image"
        else:
            selected=any(p["original_sha256"] == image_sha256 for p in record["images"])
        if selected:
            affected.append(product)
    if not affected:
        raise PrivateWithdrawalError("No matching image-bearing approved records to withdraw")
    removed_ids={p["id"] for p in affected}
    retained=[p for p in products if p["id"] not in removed_ids]
    version="r"+secrets.token_hex(10)
    now=datetime.now(timezone.utc).isoformat()
    new_index={
        "schema":RELEASE_SCHEMA,
        "version":version,"as_of":now,
        "coverage":index["coverage"],"total":len(retained),
        "shards":[],"products":[],
    }
    shards=[]
    for number,offset in enumerate(range(0,len(retained),PER_SHARD),1):
        items=retained[offset:offset+PER_SHARD]
        name=f"assets/catalog-shards/{version}/part-{number:04d}.json"
        blob=_encode({"schema":SHARD_SCHEMA,"version":version,"items":items})
        new_index["shards"].append({
            "url":name,"sha256":hashlib.sha256(blob).hexdigest(),
            "count":len(items),
        })
        shards.append((name,blob))
        for item in items:
            new_index["products"].append({
                "id":item["id"],"manufacturer":item["manufacturer"],
                "model":item["model"],"variant":item["variant"],
                "description":item["description"],"category":item["category"],
                "product_type":item["product_type"],"shard":number-1,
            })
    review=[{
        "id":p["id"],"reason":reason.strip(),
        "approved_by":reviewer.strip(),"reviewed_at":reviewed_on,
    } for p in affected]
    audit={
        "schema":"area33.catalog.private_rights_withdrawal.v1",
        "created_at":now,"previous_version":index["version"],
        "new_version":version,"reason":reason.strip(),
        "reviewed_by":reviewer.strip(),"reviewed_on":reviewed_on,
        "selection_type":"manufacturer" if manufacturer else "image_sha256",
        "affected_product_count":len(affected),
        "retained_product_count":len(retained),
        "removed_public_ids":sorted(removed_ids),
        "site_changed":False,"deployment_performed":False,
        "reminder":"Remove old public media and purge caches on separately authorized deployment; staging alone does not remove accessible URLs.",
    }
    keep_images = {
        p["public_url"] for product in retained
        for p in provenance[product["id"]]["images"]
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    temp=Path(tempfile.mkdtemp(prefix=".area33-takedown-",dir=output.parent))
    try:
        for name,blob in shards:
            path=temp.joinpath(*Path(name).parts)
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(blob)
        for name in sorted(keep_images):
            source=images[name]
            target=temp.joinpath(*Path(name).parts)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target)
            if hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(
                source.read_bytes()
            ).digest():
                raise PrivateWithdrawalError("Approved retained photo copied incorrectly")
        path=temp/"assets/catalog-index.v2.json"
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(_encode(new_index))
        (temp/"catalog-private-media-provenance.json").write_bytes(_encode({
            "schema":"area33.catalog.private_media_provenance.v1",
            "release_version":version,
            "public_catalog_record_count":len(retained),
            "records":[provenance[p["id"]] for p in retained],
            "notice":"PRIVATE: image provenance is not a license or public data.",
        }))
        (temp/"catalog-private-withdrawals.json").write_bytes(_encode({
            "schema":"area33.catalog.withdrawals.private.v1","items":review,
        }))
        (temp/"catalog-private-rights-withdrawal-audit.json").write_bytes(_encode(audit))
        (temp/"READ_ME_FIRST.txt").write_text(
            "PRIVATE rights-withdrawal snapshot. Public site UNCHANGED.\n"
            "Only copy separately validated public assets after owner deployment approval.\n"
            "A live takedown also requires removing old hosted image URLs, old"
            " catalogs and CDN caches; do not republish removed images.\n",
            encoding="utf-8",
        )
        temp.rename(output)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return audit,new_index


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous-private-release",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--manufacturer")
    group.add_argument("--image-sha256")
    parser.add_argument("--include-text-only",action="store_true")
    parser.add_argument("--reviewer",required=True)
    parser.add_argument("--reason",required=True)
    parser.add_argument("--reviewed-on",required=True)
    parser.add_argument("--stage-private-withdrawal",action="store_true")
    args=parser.parse_args(argv)
    if not args.stage_private_withdrawal:
        parser.error("Explicit --stage-private-withdrawal required")
    try:
        audit,index=stage_media_withdrawal(
            args.previous_private_release,args.out,
            manufacturer=args.manufacturer,
            image_sha256=args.image_sha256,
            include_text_only=args.include_text_only,
            reviewer=args.reviewer,reason=args.reason,reviewed_on=args.reviewed_on,
        )
    except (OSError,ValueError) as exc:
        parser.error(str(exc))
    print("PRIVATE rights-withdrawal release staged; NOTHING published.")
    print("  Affected owner-approved product IDs:",audit["affected_product_count"])
    print("  Retained owner-approved product IDs:",index["total"])
    print("  Private output:",args.out)
    print("  Live hosting and CDN purge: not performed")


if __name__=="__main__":
    main()
