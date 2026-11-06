#!/usr/bin/env python3
"""Build a PRIVATE source-identity evidence sidecar for existing text-only drafts.

Uses the ORIGINAL Randbeck staging file and SAME 32-byte identity key as the
original intake. HMAC joins by UPC + manufacturer + MPN + model. Never guesses
a missing variant, changes an ID, copies supplier prose, approves anything,
reads source media or produces public JSON. The recorded fields are research
clues, NOT independent product verification or current stock evidence.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import hmac
import json
from pathlib import Path

from build_private_catalog_review import HERE,ReviewError
from build_private_text_batch_review import _private_file,source_batch
from import_randbeck_staging import (
    SOURCE_SCHEMA, _identity, _clean, _gtin_valid, SKU, ID,
)

EVIDENCE_SCHEMA="area33.catalog.private_identity_evidence.v1"
PUBLICATION_FIELDS=("publication_approved","media_rights_approved","source_offer_verified")
MAX_RECORDS=200


def _hash(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _identity_key(path:Path)->bytes:
    original=Path(path).expanduser()
    resolved=original.resolve()
    if (original.is_symlink() or not resolved.is_file()
            or resolved.stat().st_size!=32
            or resolved==HERE or resolved.is_relative_to(HERE)
            or any((p/".git").exists() for p in (resolved,*resolved.parents))):
        raise ReviewError("Use the SAME existing private 32-byte identity key outside Git; never create a new key")
    return resolved.read_bytes()


def neutral_suggestion(brand:str,model:str,mpn:str,category:str)->str:
    """Editorial starting point from factual *labels only*, never vendor copy."""
    # Avoid claimed specs, finish, color, handedness, caliber, fit or stock.
    phrase=f"{brand} {model}. Manufacturer part number: {mpn}. "
    phrase+=f"Source category: {category}. Confirm the exact variant and fit before ordering."
    if len(phrase)>200 or len(phrase.strip())<18:
        return ""
    return phrase


def build_private_evidence(
    staging:Path,drafts:Path,exceptions:Path,identity_key:Path,
    output:Path
)->dict:
    staging=_private_file(staging)
    drafts=_private_file(drafts)
    exceptions=_private_file(exceptions)
    key=_identity_key(identity_key)
    rows,quarantined=source_batch(drafts,exceptions)
    payload=json.loads(staging.read_text(encoding="utf-8"))
    if (not isinstance(payload,dict) or payload.get("schema")!=SOURCE_SCHEMA
            or payload.get("source")!="RSR"
            or payload.get("publication_enabled") is not False
            or payload.get("media_rights_approved") is not False
            or payload.get("source_offer_verified") is not False
            or not isinstance(payload.get("items"),list)
            or not 1<=len(payload["items"])<=MAX_RECORDS
            or type(payload.get("products_staged")) is not int
            or payload["products_staged"]!=len(payload["items"])):
        raise ReviewError("Original private Randbeck source staging is missing or has changed publication status")
    raw_report=json.loads(exceptions.read_text(encoding="utf-8"))
    if (raw_report.get("source_products")!=len(payload["items"]) or
            raw_report.get("exact_identity_groups")!=len(rows)+len(quarantined)):
        raise ReviewError("Original pilot count/identity coverage disagrees with private source evidence")
    grouped=defaultdict(list)
    sku_to_group={}
    for source in payload["items"]:
        if not isinstance(source,dict):
            raise ReviewError("Malformed source identity evidence")
        if (source.get("publication_approved") is not False or
                source.get("media_rights_approved") is not False or
                source.get("source_offer_verified") is not False):
            raise ReviewError("Source unexpectedly asserts sale/media/publication approval")
        sku=source.get("source_sku")
        if not isinstance(sku,str) or not SKU.fullmatch(sku):
            raise ReviewError("Private source contains invalid source SKU")
        identity=_identity(source)
        if sku in sku_to_group and sku_to_group[sku]!=identity:
            raise ReviewError("Source SKU is reused for incompatible exact identities")
        sku_to_group[sku]=identity
        grouped[identity].append(source)
    if len(grouped)!=raw_report["exact_identity_groups"]:
        raise ReviewError("Source identity groups changed since private intake")
    candidate_by_id={row["id"]:row for row in rows}
    verified={}
    seen_groups=set()
    for identity,sources in grouped.items():
        ident="catalog_"+hmac.new(
            key,"\x1f".join(identity).encode("utf-8"),hashlib.sha256
        ).hexdigest()[:20]
        if ident not in candidate_by_id:
            continue
        if ident in verified or identity in seen_groups:
            raise ReviewError("Duplicate source identity group")
        if not _gtin_valid(identity[0]) or not all(identity):
            raise ReviewError("An invalid identity appeared as an ordinary draft")
        candidate=candidate_by_id[ident]
        first=sources[0]
        brand=_clean(first.get("manufacturer"),100)
        model=_clean(first.get("model"),120)
        mpn=_clean(first.get("manufacturer_part_number"),120)
        category=_clean(first.get("source_category"),100)
        if (candidate["manufacturer"]!=brand or candidate["model"]!=model or
                candidate["category"]!=category or
                not mpn or
                any(_identity(rec)!=identity or
                    _clean(rec.get("source_category"),100)!=category
                    for rec in sources)):
            raise ReviewError("Source and existing private draft identity/category differ")
        source_skus=sorted({rec["source_sku"] for rec in sources})
        verified[ident]={
            "id":ident,
            "recorded_upc":identity[0],
            "recorded_manufacturer_part_number":mpn,
            "recorded_source_skus":source_skus,
            "recorded_category":category,
            "recorded_manufacturer":brand,
            "recorded_model":model,
            "neutral_draft_suggestion":neutral_suggestion(brand,model,mpn,category),
            "evidence_status":"RSR source identity only — not independently verified",
        }
        seen_groups.add(identity)
    if set(verified)!=set(candidate_by_id):
        raise ReviewError("Original private identity key or source pilot does not match existing 49 drafts")
    held_skus={
        sku for entry in quarantined for sku in entry["source_skus"]
    }
    candidate_skus={
        sku for e in verified.values() for sku in e["recorded_source_skus"]
    }
    if candidate_skus & held_skus:
        raise ReviewError("Identity exception and candidate share an unsafe source SKU")
    for identity,sources in grouped.items():
        if "catalog_"+hmac.new(
            key,"\x1f".join(identity).encode(),hashlib.sha256
        ).hexdigest()[:20] in candidate_by_id:
            continue
        if not set(s["source_sku"] for s in sources).issubset(held_skus):
            raise ReviewError("Unmapped identity group is not explained by original exception report")
    output=Path(output).expanduser().resolve()
    if (output.exists() or output.parent!=drafts.parent or
            output.suffix.lower()!=".json"
            or output==HERE or output.is_relative_to(HERE)
            or any((p/".git").exists() for p in (output,*output.parents))):
        raise ReviewError("Choose a NEW private JSON evidence file beside the 49-draft input")
    result={
        "schema":EVIDENCE_SCHEMA,
        "source":"RSR",
        "source_staging_sha256":_hash(staging),
        "source_drafts_sha256":_hash(drafts),
        "source_exceptions_sha256":_hash(exceptions),
        "candidate_count":len(rows),
        "held_identity_exception_count":len(quarantined),
        "evidence":[verified[rec["id"]] for rec in rows],
        "publication_approved":False,
        "media_rights_approved":False,
        "source_offer_verified":False,
        "note":"PRIVATE recorded source facts, not independent verification, licensing, offer/stock or automatic approvals.",
    }
    output.write_text(json.dumps(result,indent=2,ensure_ascii=True)+"\n",encoding="utf-8")
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--staging",required=True,type=Path)
    p.add_argument("--drafts",required=True,type=Path)
    p.add_argument("--exceptions",required=True,type=Path)
    p.add_argument("--identity-key",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args(argv)
    try:
        value=build_private_evidence(
            args.staging,args.drafts,args.exceptions,args.identity_key,args.out
        )
    except (OSError,ValueError,KeyError,TypeError) as exc:
        p.error(str(exc))
    print("PRIVATE identity-evidence sidecar prepared; no publication or approvals.")
    print("  Existing draft matches:",value["candidate_count"])
    print("  Separate held identity exceptions:",value["held_identity_exception_count"])
    print("  Source photos and marketing descriptions copied: 0")
    print("  Private file:",args.out)


if __name__=="__main__":
    main()
