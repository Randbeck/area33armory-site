#!/usr/bin/env python3
"""Prepare an offline, private, owner-approved Area 33 catalog release snapshot.

Accept only bundles already validated by the existing manual approval publisher.
Never infer supplier permissions, modify any approved record, deploy, or change
Area 33's public website. A release is a FULL replacement snapshot; when an
earlier v2 index is supplied, each removed item requires a reviewed withdrawal.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import secrets
import shutil
import tempfile

from publish_approved_catalog import build as validate_approved_bundle

RELEASE_SCHEMA="area33.catalog.index.v2"
SHARD_SCHEMA="area33.catalog.shard.v2"
ID=re.compile(r"^catalog_[a-f0-9]{20}$")
VERSION=re.compile(r"^r[a-f0-9]{20}$")
MAX_PRODUCTS=50000
PER_SHARD=100
SITE=Path(__file__).resolve().parents[1]


class ShardedReleaseError(ValueError):
    pass


def _private_destination(path: Path) -> Path:
    path=path.expanduser().resolve()
    if path==SITE or path.is_relative_to(SITE):
        raise ShardedReleaseError("Private release must not be created in website checkout")
    if any((p/".git").exists() for p in (path,*path.parents)):
        raise ShardedReleaseError("Private release must be outside all Git repositories")
    if any(x.lower() in {"assets","public","dist","wwwroot"} for x in path.parts):
        raise ShardedReleaseError("Output must not be a live/public assets directory")
    if path.exists():
        raise ShardedReleaseError("Private release folder already exists")
    return path


def _encode(value):
    return (json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode("utf-8")


def _previous_ids(previous):
    if previous is None:
        return set()
    path=Path(previous).expanduser().resolve()
    data=json.loads(path.read_text(encoding="utf-8"))
    if (data.get("schema")!=RELEASE_SCHEMA or not isinstance(data.get("products"),list)
            or data.get("total")!=len(data["products"])):
        raise ShardedReleaseError("Expected a validated previous approved v2 index")
    keys=[rec.get("id") for rec in data["products"]]
    if len(keys)!=len(set(keys)) or any(
        not isinstance(v,str) or not ID.fullmatch(v) for v in keys
    ):
        raise ShardedReleaseError("Invalid prior public product IDs")
    return set(keys)


def _withdrawals(path):
    if path is None:
        return {}
    data=json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))
    if data.get("schema")!="area33.catalog.withdrawals.private.v1" or not isinstance(
        data.get("items"),list
    ):
        raise ShardedReleaseError("Invalid private withdrawal approval bundle")
    entries={}
    for raw in data["items"]:
        if not isinstance(raw,dict) or set(raw)!={"id","reason","approved_by","reviewed_at"}:
            raise ShardedReleaseError("Withdrawal must have reason, reviewer and date")
        ident=raw["id"]
        if not isinstance(ident,str) or not ID.fullmatch(ident) or ident in entries:
            raise ShardedReleaseError("Invalid or repeated withdrawal ID")
        for field in ("reason","approved_by"):
            value=raw[field]
            if (not isinstance(value,str) or not 3<=len(value.strip())<=160
                    or any(ord(ch)<32 for ch in value)):
                raise ShardedReleaseError("Invalid withdrawal explanation or reviewer")
        try:
            reviewed=date.fromisoformat(raw["reviewed_at"])
        except (TypeError,ValueError) as exc:
            raise ShardedReleaseError("Invalid withdrawal review date") from exc
        if reviewed>date.today():
            raise ShardedReleaseError("Withdrawal review date cannot be in future")
        entries[ident]=raw
    return entries


def gather_approved(bundles):
    records, frames, seen=[],[],set()
    for bundle in bundles:
        public, media=validate_approved_bundle(Path(bundle))
        for product in public["items"]:
            ident=product["id"]
            if ident in seen:
                raise ShardedReleaseError("Same approved catalog identity appears twice")
            seen.add(ident)
            records.append(product)
        frames.extend(media)
        if len(records)>MAX_PRODUCTS:
            raise ShardedReleaseError("Approved release record limit exceeded")
    records.sort(key=lambda p:(p["manufacturer"].casefold(),
                               p["model"].casefold(),p["id"]))
    return records,frames


def prepare_private_release(
    bundles:list[Path],output:Path,*,previous_index:Path|None=None,
    withdrawal_file:Path|None=None
):
    """Stage media, hashed public index/shards, and audit in a new PRIVATE folder."""
    output=_private_destination(output)
    public,frames=gather_approved(bundles)
    previous=_previous_ids(previous_index)
    current={item["id"] for item in public}
    if not public and not previous:
        raise ShardedReleaseError("Empty first release; no approved records")
    withdrawn=_withdrawals(withdrawal_file)
    removed=previous-current
    if (removed!=set(withdrawn) or (withdrawn and previous_index is None)
            or any(v in current for v in withdrawn)):
        raise ShardedReleaseError(
            "Every removed prior catalog ID needs exactly one explicit private withdrawal"
        )
    by_image_dest={}
    for frame in frames:
        source=frame["source"]
        dest=frame["dest"]
        if dest in by_image_dest:
            raise ShardedReleaseError("Duplicate source image destination")
        by_image_dest[dest]=source
    now=datetime.now(timezone.utc).isoformat()
    version="r"+secrets.token_hex(10)
    index={
        "schema":RELEASE_SCHEMA,"version":version,"as_of":now,
        "coverage":{
            "description":"Only explicitly owner-approved Area 33 listings; not distributor inventory or live stock."
        },
        "total":len(public),"shards":[],"products":[],
    }
    written_shards=[]
    for part_no,offset in enumerate(range(0,len(public),PER_SHARD),1):
        items=public[offset:offset+PER_SHARD]
        shard={
            "schema":SHARD_SCHEMA,"version":version,"items":items,
        }
        body=_encode(shard)
        name=f"assets/catalog-shards/{version}/part-{part_no:04d}.json"
        index["shards"].append({
            "url":name,"sha256":hashlib.sha256(body).hexdigest(),"count":len(items)
        })
        written_shards.append((name,body))
        for item in items:
            index["products"].append({
                "id":item["id"],
                "manufacturer":item["manufacturer"],
                "model":item["model"],
                "variant":item["variant"],
                "description":item.get("description",""),
                "category":item["category"],
                "product_type":item["product_type"],
                "shard":part_no-1,
            })
    audit={
        "schema":"area33.catalog.private_release_audit.v1",
        "created_at":now,"version":version,
        "owner_approved_public_record_count":len(public),
        "source_approved_bundle_count":len(bundles),
        "private_source_media_file_count":len(frames),
        "previous_catalog_record_count":len(previous),
        "approved_withdrawal_count":len(withdrawn),
        "approved_withdrawals":list(withdrawn.values()),
        "website_modified":False,"published":False,
        "note":"PRIVATE staged full-snapshot replacement. Do not deploy without separate owner authorization.",
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    temp=Path(tempfile.mkdtemp(prefix=".area33-release-",dir=output.parent))
    try:
        for name,body in written_shards:
            dest=temp/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(body)
        for frame in frames:
            relative=frame["public"]["url"]
            if (not isinstance(relative,str) or
                    not re.fullmatch(
                        r"assets/approved/catalog/catalog_[a-f0-9]{20}/view-0[1-8]\.jpg",
                        relative,
                    )):
                raise ShardedReleaseError("Unexpected public image path")
            target=temp/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(frame["source"],target)
            if hashlib.sha256(target.read_bytes()).digest()!=hashlib.sha256(
                frame["source"].read_bytes()
            ).digest():
                raise ShardedReleaseError("Original approved image changed when copied")
        destination=temp/"assets/catalog-index.v2.json"
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(_encode(index))
        (temp/"catalog-private-release-audit.json").write_bytes(_encode(audit))
        (temp/"READ_ME_FIRST.txt").write_text(
            "PRIVATE staged catalog release. Do NOT upload/merge/deploy automatically.\n"
            "All inputs must be independently approved. Every removal requires "
            "a reviewed withdrawal. Live website is unchanged.\n",
            encoding="utf-8",
        )
        # Final move exposes the complete private tree or none of it.
        temp.rename(output)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return audit,index


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle",action="append",type=Path,default=[],
                        help="Explicitly approved PRIVATE owner-review bundle; repeat for more")
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--previous-index",type=Path)
    parser.add_argument("--withdrawal-file",type=Path)
    parser.add_argument("--prepare-private-release",action="store_true")
    args=parser.parse_args(argv)
    if not args.prepare_private_release:
        parser.error("Explicit --prepare-private-release required; no automatic publication")
    try:
        audit,index=prepare_private_release(
            args.bundle,args.out,previous_index=args.previous_index,
            withdrawal_file=args.withdrawal_file,
        )
    except (OSError,ValueError) as exc:
        parser.error(str(exc))
    print("PRIVATE v2 approved-only catalog release prepared:")
    print("  Approved product records:",index["total"])
    print("  Verified catalog shards:",len(index["shards"]))
    print("  Explicit withdrawals:",audit["approved_withdrawal_count"])
    print("  Public site changes: none; release NOT deployed")
    print("  Private output:",args.out)


if __name__=="__main__":
    main()
