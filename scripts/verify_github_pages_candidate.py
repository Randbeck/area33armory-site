#!/usr/bin/env python3
"""Verify a GitHub Pages candidate on disk, with Python stdlib only.

Designed to run from a TRUSTED main-branch Actions checkout against a separate
release-branch checkout. Checks every public byte and disallows extra files.
It cannot validate PRIVATE rights grants by itself; owners must separately
approve the source release and any media before public branch publication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from catalog_static_allowlist import STATIC

DOMAIN="area33armory.com"
META="pages-release-public.json"
SCHEMA="area33.pages.public_candidate.v1"
SHA=re.compile(r"[0-9a-f]{64}\Z")
VERSION=re.compile(r"r[0-9a-f]{20}\Z")
ID=re.compile(r"catalog_[0-9a-f]{20}\Z")
SHARD=re.compile(r"assets/catalog-shards/(r[0-9a-f]{20})/part-([0-9]{4})\.json\Z")
PHOTO=re.compile(r"assets/approved/catalog/(catalog_[0-9a-f]{20})/view-0[1-8]\.jpg\Z")
RECORD_FIELDS={
    "id","manufacturer","model","variant","description","presentation_mode",
    "category","product_type","specifications","evidence","images",
    "publication_updated_at",
}
INDEX_FIELDS={"schema","version","as_of","coverage","total","shards","products"}
SUMMARY_FIELDS={"id","manufacturer","model","variant","description","category","product_type","shard"}
PUBLIC_FIELDS={
    "schema","domain","catalog_version","index_sha256",
    "approved_product_count","file_sha256","note",
}


class PagesVerificationError(ValueError):
    pass


def digest(path:Path)->str:
    hasher=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def scan_files(root:Path)->dict[str,Path]:
    root=Path(root).expanduser().resolve()
    if not root.is_dir():
        raise PagesVerificationError("Candidate site/ folder missing")
    files={}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise PagesVerificationError("Symlinks cannot be hosted")
        if not path.is_file():
            continue
        name=path.relative_to(root).as_posix()
        if path.resolve().is_relative_to(root) is False or "\\" in name or name.startswith("./"):
            raise PagesVerificationError("Candidate contains an unsafe file path")
        files[name]=path
        if len(files)>200003:
            raise PagesVerificationError("Unexpected number of public files")
    return files


def _require(value,pattern,what):
    if not isinstance(value,str) or not pattern.fullmatch(value):
        raise PagesVerificationError("Invalid "+what)
    return value


def verify_github_pages_candidate(
    site:Path,*,expected_manifest_sha256:str,
    expected_index_sha256:str
)->dict:
    _require(expected_manifest_sha256,SHA,"expected public manifest SHA")
    _require(expected_index_sha256,SHA,"expected approved catalog index SHA")
    site=Path(site).expanduser().resolve()
    files=scan_files(site)
    if not {"CNAME",".nojekyll",META}.issubset(files):
        raise PagesVerificationError("Missing Pages domain, .nojekyll or signed manifest")
    if files["CNAME"].read_bytes()!=(DOMAIN+"\n").encode("ascii"):
        raise PagesVerificationError("Candidate domain does not match Area 33")
    if files[".nojekyll"].read_bytes()!=b"":
        raise PagesVerificationError("Invalid .nojekyll contents")
    if digest(files[META])!=expected_manifest_sha256:
        raise PagesVerificationError("Pages public manifest hash differs from owner's approved value")
    manifest=json.loads(files[META].read_text(encoding="utf-8"))
    if (not isinstance(manifest,dict) or set(manifest)!=PUBLIC_FIELDS
            or manifest["schema"]!=SCHEMA or manifest["domain"]!=DOMAIN
            or not isinstance(manifest["note"],str)):
        raise PagesVerificationError("Unexpected public release manifest")
    version=_require(manifest["catalog_version"],VERSION,"catalog version")
    _require(manifest["index_sha256"],SHA,"catalog index hash")
    if manifest["index_sha256"]!=expected_index_sha256:
        raise PagesVerificationError("Approved catalog index hash does not match owner input")
    listed=manifest["file_sha256"]
    if not isinstance(listed,dict) or len(listed)>200000:
        raise PagesVerificationError("Unrecognized public asset hash list")
    if set(files)!=set(listed)|{"CNAME",".nojekyll",META}:
        raise PagesVerificationError("Unexpected, missing or unapproved public file")
    if len(listed)!=len(set(listed)) or not set(STATIC).issubset(listed):
        raise PagesVerificationError("Required Area 33 website assets missing")
    for name,expected in listed.items():
        if (not isinstance(name,str) or not isinstance(expected,str)
                or not SHA.fullmatch(expected)
                or not (name in STATIC or name=="assets/catalog-index.v2.json"
                        or SHARD.fullmatch(name) or PHOTO.fullmatch(name))):
            raise PagesVerificationError("Public artifact contains a nonallowlisted file/hash")
        if digest(files[name])!=expected:
            raise PagesVerificationError("Actual public asset differs from signed manifest")
    if manifest["index_sha256"]!=listed.get("assets/catalog-index.v2.json"):
        raise PagesVerificationError("Manifest mismatches approved public index")
    idx=json.loads(files["assets/catalog-index.v2.json"].read_text(encoding="utf-8"))
    if (not isinstance(idx,dict) or set(idx)!=INDEX_FIELDS
            or idx["schema"]!="area33.catalog.index.v2"
            or idx["version"]!=version
            or type(idx.get("total")) is not int or
            not 0<=idx["total"]<=50000
            or not isinstance(idx.get("products"),list)
            or not isinstance(idx.get("shards"),list)
            or len(idx["products"])!=idx["total"]
            or not isinstance(idx.get("coverage"),dict)
            or not isinstance(idx["coverage"].get("description"),str)
            or manifest["approved_product_count"]!=idx["total"]):
        raise PagesVerificationError("Public approved-only index invalid")
    if len(idx["shards"]) != (idx["total"]+99)//100:
        raise PagesVerificationError("Missing or extra approved index shards")
    found_products=[]
    used_image_paths=set()
    used_ids=set()
    for part_number,entry in enumerate(idx["shards"],1):
        if not isinstance(entry,dict) or set(entry)!={"url","sha256","count"}:
            raise PagesVerificationError("Unrecognized index shard descriptor")
        name=_require(entry["url"],SHARD,"shard path")
        match=SHARD.fullmatch(name)
        if match.group(1)!=version or int(match.group(2))!=part_number:
            raise PagesVerificationError("Shard version or order mismatch")
        if entry["sha256"]!=listed.get(name):
            raise PagesVerificationError("Expected shard hash differs from release manifest")
        count=entry["count"]
        if type(count) is not int or not 1<=count<=100:
            raise PagesVerificationError("Unrecognized approved shard count")
        shard=json.loads(files[name].read_text(encoding="utf-8"))
        if (not isinstance(shard,dict) or set(shard)!={"schema","version","items"}
                or shard["schema"]!="area33.catalog.shard.v2"
                or shard["version"]!=version
                or not isinstance(shard.get("items"),list)
                or len(shard["items"])!=count):
            raise PagesVerificationError("Approved shard contents invalid")
        for row in shard["items"]:
            if not isinstance(row,dict) or set(row)!=RECORD_FIELDS:
                raise PagesVerificationError("Public product contains missing or private fields")
            ident=_require(row["id"],ID,"public product ID")
            if ident in used_ids or not isinstance(row["manufacturer"],str):
                raise PagesVerificationError("Duplicated public catalog identity")
            used_ids.add(ident)
            mode=row["presentation_mode"]
            images=row["images"]
            if mode not in ("image","text_only") or not isinstance(images,list):
                raise PagesVerificationError("Unexpected catalog image presentation mode")
            if mode=="text_only" and images:
                raise PagesVerificationError("Text-only record unexpectedly has images")
            if mode=="image" and not 1<=len(images)<=8:
                raise PagesVerificationError("Photo record missing its approved media")
            if not isinstance(row["specifications"],list) or not isinstance(row["evidence"],list):
                raise PagesVerificationError("Unexpected public product metadata")
            for pic in images:
                if (not isinstance(pic,dict) or set(pic)!={"url","alt","rights"}
                        or pic["rights"]!="approved" or not isinstance(pic["alt"],str)):
                    raise PagesVerificationError("Product photo missing approval marker")
                url=_require(pic["url"],PHOTO,"approved public image path")
                if PHOTO.fullmatch(url).group(1)!=ident or url in used_image_paths:
                    raise PagesVerificationError("Unapproved shared or misidentified photo path")
                used_image_paths.add(url)
                if url not in listed:
                    raise PagesVerificationError("Product references missing approved public photo")
            found_products.append({
                "id":ident,"manufacturer":row["manufacturer"],
                "model":row["model"],"variant":row["variant"],
                "description":row["description"],"category":row["category"],
                "product_type":row["product_type"],"shard":part_number-1,
            })
    if found_products!=idx["products"]:
        raise PagesVerificationError("Public search index differs from approved shard records")
    extra_shards={p for p in listed if SHARD.fullmatch(p)} - {
        x["url"] for x in idx["shards"]
    }
    extra_photos={p for p in listed if PHOTO.fullmatch(p)} - used_image_paths
    if extra_shards or extra_photos:
        raise PagesVerificationError("Retired or orphaned image/shard still in Pages artifact")
    if set(listed)!=set(STATIC)|{"assets/catalog-index.v2.json"}|{
        x["url"] for x in idx["shards"]
    }|used_image_paths:
        raise PagesVerificationError("Public asset inventory not exhaustive")
    fallback=json.loads(files["assets/catalog-public.json"].read_text(encoding="utf-8"))
    if fallback.get("schema")!="area33.catalog.public.v1" or fallback.get("items")!=[]:
        raise PagesVerificationError("Legacy public fallback is not empty")
    return {
        "schema":"area33.pages.verification.v1",
        "domain":DOMAIN,"catalog_version":version,
        "approved_product_count":idx["total"],
        "approved_image_count":len(used_image_paths),
        "asset_count":len(files),
        "index_sha256":expected_index_sha256,
        "public_manifest_sha256":expected_manifest_sha256,
        "not_deployed":True,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--site",required=True,type=Path)
    p.add_argument("--expected-manifest-sha256",required=True)
    p.add_argument("--expected-index-sha256",required=True)
    args=p.parse_args(argv)
    try:
        report=verify_github_pages_candidate(
            args.site,expected_manifest_sha256=args.expected_manifest_sha256,
            expected_index_sha256=args.expected_index_sha256,
        )
    except (OSError,ValueError,KeyError,TypeError,UnicodeError) as exc:
        p.error(str(exc))
    print("GitHub Pages artifact verified; not deployed.")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
