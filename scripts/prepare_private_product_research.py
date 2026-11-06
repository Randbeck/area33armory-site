#!/usr/bin/env python3
"""Prepare an owner-private source-linked research packet for the existing catalog.

No automatic sales/media approval. Public citations from independent retailers
are research leads, NOT manufacturer confirmation or current availability.
Only exact UPC+MPN matches receive a seeded research lead; all other products
get an exact identity lookup query, never invented specifications.

This private packet is NOT a catalog source and MUST NOT be published.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from build_private_text_batch_review import (
    _private_file,source_batch,validated_private_evidence,ReviewError,HERE,
)

SCHEMA="area33.catalog.private_research_packet.v1"
ALLOWED_LABELS={"Magazine configuration","Carry options","Finish/color","Material",
                "Compatibility","Product dimensions","Other verified attribute"}
# Only public product evidence observed from independent retailer pages on Nov 6,
# not assertions of manufacturer approval, media rights, or stock.
SEED_REFERENCES={
    ("193858308883","CMCS-2-D"):{
        "sources":[
            {"title":"KYGunCo — Single Mag Carrier CMCS-2-D",
             "url":"https://www.kygunco.com/product/alien-gear-holsters-cmcs-2-d-single-mag-carrier-mag-blk-9mm-40-cal-single-stack",
             "source_kind":"independent_retailer","observed_on":"2026-11-06"},
            {"title":"OpticsPlanet — Cloak Mag Carrier orderable models",
             "url":"https://www.opticsplanet.com/alien-gear-holsters-single-cloak-mag-carrier.html",
             "source_kind":"independent_retailer","observed_on":"2026-11-06"},
        ],
        "facts":[
            {"label":"Magazine configuration",
             "value":"9mm/.40 S&W single-stack magazines",
             "source_index":0,"owner_checked":False},
            {"label":"Carry options","value":"Inside- or outside-waistband carry",
             "source_index":0,"owner_checked":False},
        ],
    },
    ("193858308906","CMCS-4-D"):{
        "sources":[
            {"title":"WBT Guns — Single Mag Carrier CMCS-4-D",
             "url":"https://wbtguns.com/holsters-pouches/alien-gear-holsters-single-mag-carrier-cmcs-4-d/",
             "source_kind":"independent_retailer","observed_on":"2026-11-06"},
            {"title":"OpticsPlanet — Cloak Mag Carrier orderable models",
             "url":"https://www.opticsplanet.com/alien-gear-holsters-single-cloak-mag-carrier.html",
             "source_kind":"independent_retailer","observed_on":"2026-11-06"},
        ],
        "facts":[
            {"label":"Magazine configuration",
             "value":"9mm/.40 S&W double-stack magazines",
             "source_index":0,"owner_checked":False},
            {"label":"Carry options","value":"Inside- or outside-waistband carry",
             "source_index":0,"owner_checked":False},
        ],
    },
    ("193858308937","CT35-0057-RH-D"):{
        "sources":[
            {"title":"GunMag Warehouse — Cloak Tuck Glock 19/23/19X/44/45, CT35-0057-RH-D",
             "url":"https://gunmagwarehouse.com/alien-gear-cloak-tuck-right-handed-iwb-holster-for-glock-19-23-19x-44-45.html",
             "source_kind":"independent_retailer","observed_on":"2026-11-06"},
            {"title":"Bud's Gun Shop — Cloak Tuck CT35-0057-RH-D UPC cross-check",
             "url":"https://www.budsgunshop.com/products/holsters/alien-gear-cloak-tuck-3-5-iwb-holster-glock-19-45-rh-722124814",
             "source_kind":"independent_retailer","observed_on":"2026-11-06"},
        ],
        "facts":[
            {"label":"Compatibility",
             "value":"Glock 19/23/19X/44/45 (confirm generation and configuration)",
             "source_index":0,"owner_checked":False},
            {"label":"Carry options","value":"Right-hand inside-waistband holster",
             "source_index":0,"owner_checked":False},
        ],
    },
    ("193858309125","CT35-0939-RH-D"):{
        "sources":[
            {"title":"WBT Guns — Cloak Tuck 3.5 CT35-0939-RH-D UPC/fit",
             "url":"https://wbtguns.com/holsters-pouches/alien-gear-holsters-cloak-tuck-3-5-ct35-0939-rh-d/",
             "source_kind":"independent_retailer","observed_on":"2026-11-06"},
            {"title":"PSA — Cloak Tuck 3.5 Glock 43/43X CT35-0939-RH-D",
             "url":"https://palmettostatearmory.com/alien-gear-cloak-tuck-3-5-glock-g43-g43x-iwb-holster-right-boltaron-black.html",
             "source_kind":"independent_retailer","observed_on":"2026-11-06"},
        ],
        "facts":[
            {"label":"Compatibility","value":"Glock 43/43X",
             "source_index":0,"owner_checked":False},
            {"label":"Carry options","value":"Right-hand IWB holster",
             "source_index":0,"owner_checked":False},
            {"label":"Material","value":"Boltaron",
             "source_index":0,"owner_checked":False},
        ],
    },
    ("193858752136","PHO-0057-L1-D"):{
        "sources":[
            {"title":"BattleHawk — Photon PHO-0057-L1-D UPC and light-bearing fit",
             "url":"https://battlehawkarmory.com/product/alien-gear-photon-iwb-owb-holster",
             "source_kind":"independent_retailer","observed_on":"2026-11-06"},
            {"title":"WBT Guns — Photon PHO-0057-L1-D",
             "url":"https://wbtguns.com/holsters-pouches/alien-gear-holsters-photon-holster-pho-0057-l1-d/",
             "source_kind":"independent_retailer","observed_on":"2026-11-06"},
        ],
        "facts":[
            {"label":"Compatibility",
             "value":"Glock 19/44/45/19X/23 family; verify generation and light fit",
             "source_index":0,"owner_checked":False},
            {"label":"Carry options","value":"Ambidextrous IWB/OWB light-bearing holster",
             "source_index":0,"owner_checked":False},
            {"label":"Material","value":"Polymer",
             "source_index":1,"owner_checked":False},
        ],
    },
}


# Multiple public retailer listings disagree over the UPC for CT35-1198-RH-D.
# A matching MPN alone must not silently authorize an exact identity.
CONFLICT_LEADS={
    "CT35-1198-RH-D":{
        "observed_upcs":["193858332383","193858373485"],
        "sources":[
            {"title":"BattleHawk — CT35-1198-RH-D lists UPC 193858332383",
             "url":"https://battlehawkarmory.com/product/alien-gear-holsters-cloak-tuck-3.5-inside-waistband-holster-fits-sig-p365x-macro-boltaron-construction-right-hand-black",
             "source_kind":"independent_retailer","observed_on":"2026-11-06"},
            {"title":"GunMag Warehouse — CT35-1198-RH-D lists UPC 193858373485",
             "url":"https://gunmagwarehouse.com/alien-gear-cloak-tuck-3-5-right-handed-iwb-holster-for-sig-sauer-p365-x-macro.html",
             "source_kind":"independent_retailer","observed_on":"2026-11-06"},
        ],
    }
}


def digest(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_https_url(url:str)->bool:
    if not isinstance(url,str) or len(url)>1500 or any(ord(c)<32 for c in url):
        return False
    try:
        parsed=urlsplit(url)
        host=parsed.hostname or ""
        return (parsed.scheme=="https" and parsed.username is None
                and parsed.password is None and bool(re.fullmatch(
                    r"[A-Za-z0-9][A-Za-z0-9.-]{2,252}",host))
                and "." in host and not host.startswith("localhost")
                and not parsed.fragment)
    except ValueError:
        return False


def validate_research_packet(packet:dict,evidence:list[dict],drafts:Path,
                             sidecar:Path)->list[dict]:
    if (not isinstance(packet,dict) or set(packet)!={
            "schema","source_drafts_sha256","private_identity_evidence_sha256",
            "candidate_count","items","publication_approved",
            "source_research_is_owner_verified"
        } or packet["schema"]!=SCHEMA
            or packet["publication_approved"] is not False
            or packet["source_research_is_owner_verified"] is not False
            or packet["source_drafts_sha256"]!=digest(_private_file(drafts))
            or packet["private_identity_evidence_sha256"]!=digest(_private_file(sidecar))
            or type(packet["candidate_count"]) is not int
            or packet["candidate_count"]!=len(evidence)
            or not isinstance(packet["items"],list)
            or len(packet["items"])!=len(evidence)):
        raise ReviewError("Private research packet does not match original recorded identities")
    by_id={e["id"]:e for e in evidence}
    seen=set()
    for item in packet["items"]:
        if not isinstance(item,dict) or set(item)!={
            "id","recorded_upc","recorded_mpn","research_query","sources","facts","identity_warnings"
        }:
            raise ReviewError("Private research item has unexpected fields")
        ident=item["id"]
        if ident not in by_id or ident in seen:
            raise ReviewError("Private research has unknown or repeated product")
        seen.add(ident)
        orig=by_id[ident]
        if (item["recorded_upc"]!=orig["recorded_upc"] or
                item["recorded_mpn"]!=orig["recorded_manufacturer_part_number"] or
                not isinstance(item["research_query"],str) or
                len(item["research_query"])>300
                or not isinstance(item["sources"],list)
                or len(item["sources"])>8
                or not isinstance(item["facts"],list)
                or len(item["facts"])>12):
            raise ReviewError("Private product research identity changed or too large")
        if not isinstance(item["identity_warnings"],list) or len(item["identity_warnings"])>3:
            raise ReviewError("Invalid private identity warnings")
        for warning in item["identity_warnings"]:
            if (not isinstance(warning,dict) or set(warning)!={
                    "code","observed_upcs","source_indices","explanation"
                } or warning["code"]!="conflicting_public_upc"
                    or not isinstance(warning["observed_upcs"],list)
                    or len(warning["observed_upcs"])<2
                    or not all(isinstance(u,str) and re.fullmatch(r"\d{12,14}",u)
                               for u in warning["observed_upcs"])
                    or not isinstance(warning["source_indices"],list)
                    or len(warning["source_indices"])<2
                    or not all(type(i) is int and 0<=i<len(item["sources"])
                               for i in warning["source_indices"])
                    or not isinstance(warning["explanation"],str)
                    or not 12<=len(warning["explanation"])<=300):
                raise ReviewError("An unresolved UPC identity conflict has invalid evidence")
        for source in item["sources"]:
            if (not isinstance(source,dict) or set(source)!={
                "title","url","source_kind","observed_on"
            } or not isinstance(source["title"],str)
                or not 4<=len(source["title"])<=160
                or not validate_https_url(source["url"])
                or source["source_kind"] not in ("manufacturer","independent_retailer",
                                                "other_public_reference")):
                raise ReviewError("Private research source URL or title invalid")
            try:
                observed=date.fromisoformat(source["observed_on"])
                if observed>date.today():
                    raise ReviewError("Research source observed in the future")
            except (ValueError,TypeError) as exc:
                raise ReviewError("Invalid research source observation date") from exc
        for fact in item["facts"]:
            if (not isinstance(fact,dict) or set(fact)!={
                    "label","value","source_index","owner_checked"
                } or fact["label"] not in ALLOWED_LABELS
                    or not isinstance(fact["value"],str)
                    or not 4<=len(fact["value"].strip())<=130
                    or type(fact["source_index"]) is not int
                    or not 0<=fact["source_index"]<len(item["sources"])
                    or type(fact["owner_checked"]) is not bool):
                raise ReviewError("Uncited, malformed or unreviewed fact structure")
    if seen!=set(by_id):
        raise ReviewError("Private research packet omits catalog candidates")
    return packet["items"]


def prepare_research_packet(drafts:Path,exceptions:Path,evidence_file:Path,
                            output:Path)->dict:
    drafts=_private_file(drafts);exceptions=_private_file(exceptions)
    evidence_file=_private_file(evidence_file)
    rows,_=source_batch(drafts,exceptions)
    evidence=validated_private_evidence(evidence_file,drafts,exceptions,rows)
    items=[]
    for entry in evidence:
        key=(entry["recorded_upc"],entry["recorded_manufacturer_part_number"])
        lead=SEED_REFERENCES.get(key,{"sources":[],"facts":[]})
        conflict=CONFLICT_LEADS.get(key[1])
        warnings=[]
        extra_sources=[]
        if conflict and key[0] in conflict["observed_upcs"]:
            extra_sources=[dict(src) for src in conflict["sources"]]
            offset=len(lead["sources"])
            warnings.append({
                "code":"conflicting_public_upc",
                "observed_upcs":list(conflict["observed_upcs"]),
                "source_indices":list(range(offset,offset+len(extra_sources))),
                "explanation":"Retailer sources disagree about this manufacturer's exact UPC. HOLD for authoritative manufacturer or source-identity confirmation before approval.",
            })
        name=entry["recorded_manufacturer"]+" "+entry["recorded_model"]
        query=f"{name} {key[1]} {key[0]} specifications"
        items.append({
            "id":entry["id"],
            "recorded_upc":key[0],
            "recorded_mpn":key[1],
            "research_query":query[:300],
            "sources":[dict(s) for s in lead["sources"]]+extra_sources,
            "facts":[dict(f) for f in lead["facts"]],
            "identity_warnings":warnings,
        })
    packet={
        "schema":SCHEMA,
        "source_drafts_sha256":digest(drafts),
        "private_identity_evidence_sha256":digest(evidence_file),
        "candidate_count":len(rows),"items":items,
        "publication_approved":False,
        "source_research_is_owner_verified":False,
    }
    validate_research_packet(packet,evidence,drafts,evidence_file)
    output=Path(output).expanduser().resolve()
    if (output.exists() or output.parent!=drafts.parent
            or output.suffix.lower()!=".json"
            or output.is_relative_to(HERE)
            or any((p/".git").exists() for p in (output,*output.parents))):
        raise ReviewError("Choose a new private research JSON file beside existing drafts")
    output.write_text(json.dumps(packet,indent=2,ensure_ascii=True)+"\n",encoding="utf-8")
    return packet


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drafts",required=True,type=Path)
    parser.add_argument("--exceptions",required=True,type=Path)
    parser.add_argument("--evidence",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args(argv)
    try:
        result=prepare_research_packet(
            args.drafts,args.exceptions,args.evidence,args.out
        )
    except (ValueError,OSError,TypeError,KeyError) as exc:
        parser.error(str(exc))
    print("PRIVATE research evidence packet created; no publication.")
    print("  Candidates:",result["candidate_count"])
    print("  Source-linked research leads:",
          sum(bool(x["sources"]) for x in result["items"]))
    print("  Products automatically reviewed or approved: 0")
    print("  Output:",args.out)


if __name__=="__main__":
    main()
