#!/usr/bin/env python3
"""Safely carry owner-edited private research notes into a NEW source packet.

Accepts previously saved v1 research notes with or without identity_warnings.
Preserves checked facts and user-added HTTPS sources, but NEVER allows old
notes to suppress a newly discovered UPC conflict. No live-site action.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from build_private_text_batch_review import (
    _private_file,source_batch,validated_private_evidence,ReviewError,HERE,
)
from prepare_private_product_research import (
    validate_research_packet,SCHEMA,
)


def migrate_saved_notes(
    saved:Path,new_packet:Path,drafts:Path,exceptions:Path,evidence_file:Path,
    output:Path,
):
    saved=_private_file(saved)
    new_packet=_private_file(new_packet)
    drafts=_private_file(drafts)
    exceptions=_private_file(exceptions)
    evidence_file=_private_file(evidence_file)
    rows,_=source_batch(drafts,exceptions)
    evidence=validated_private_evidence(evidence_file,drafts,exceptions,rows)
    base=json.loads(new_packet.read_text(encoding="utf-8"))
    validate_research_packet(base,evidence,drafts,evidence_file)
    older=json.loads(saved.read_text(encoding="utf-8"))
    if (not isinstance(older,dict) or
            set(older)!=set(base) or older.get("schema")!=SCHEMA or
            older.get("publication_approved") is not False or
            older.get("source_research_is_owner_verified") is not False or
            older.get("source_drafts_sha256")!=base["source_drafts_sha256"] or
            older.get("private_identity_evidence_sha256")!=base["private_identity_evidence_sha256"] or
            older.get("candidate_count")!=base["candidate_count"] or
            not isinstance(older.get("items"),list) or
            len(older["items"])!=len(base["items"])):
        raise ReviewError("Saved research notes refer to different private source identities")
    original={item["id"]:item for item in base["items"]}
    seen=set()
    updated=copy.deepcopy(base)
    merge_by_id={item["id"]:item for item in updated["items"]}
    for old in older["items"]:
        if (not isinstance(old,dict) or
                set(old) not in (
                    {"id","recorded_upc","recorded_mpn",
                     "research_query","sources","facts"},
                    {"id","recorded_upc","recorded_mpn",
                     "research_query","sources","facts","identity_warnings"},
                ) or
                old.get("id") not in original or old["id"] in seen):
            raise ReviewError("Research notes contain unrecognized or repeated product")
        seen.add(old["id"])
        new=merge_by_id[old["id"]]
        if (old["recorded_upc"]!=new["recorded_upc"]
                or old["recorded_mpn"]!=new["recorded_mpn"]
                or old["research_query"]!=new["research_query"]
                or not isinstance(old["sources"],list)
                or len(old["sources"])>8
                or not isinstance(old["facts"],list)
                or len(old["facts"])>12):
            raise ReviewError("Previous notes changed exact private research identity")
        # New authoritative conflict warnings always win. Never carry forward
        # an older warning state, including one edited out of saved JSON.
        # Seeded sources are first so warning reference indexes stay fixed.
        sources=copy.deepcopy(new["sources"])
        canonical={entry["url"]:i for i,entry in enumerate(sources)}
        remap={}
        for i,source in enumerate(old["sources"]):
            if (not isinstance(source,dict)
                    or set(source)!={"title","url","source_kind","observed_on"}):
                raise ReviewError("Saved research notes contain malformed reference")
            url=source["url"]
            if not isinstance(url,str):
                raise ReviewError("Saved research URL missing")
            if url not in canonical:
                canonical[url]=len(sources)
                sources.append(copy.deepcopy(source))
            remap[i]=canonical[url]
        facts=copy.deepcopy(new["facts"])
        old_facts_index={(f["label"],f["value"],f["source_index"]):i
                         for i,f in enumerate(facts)}
        for fact in old["facts"]:
            if (not isinstance(fact,dict)
                    or set(fact)!={"label","value","source_index","owner_checked"}
                    or type(fact["source_index"]) is not int
                    or fact["source_index"] not in remap
                    or type(fact["owner_checked"]) is not bool):
                raise ReviewError("Saved source-linked fact malformed")
            adjusted=copy.deepcopy(fact)
            adjusted["source_index"]=remap[fact["source_index"]]
            key=(adjusted["label"],adjusted["value"],adjusted["source_index"])
            if key in old_facts_index:
                if adjusted["owner_checked"]:
                    facts[old_facts_index[key]]["owner_checked"]=True
            else:
                old_facts_index[key]=len(facts)
                facts.append(adjusted)
        if len(sources)>8 or len(facts)>12:
            raise ReviewError("Saved notes exceed safe references/facts limits; nothing was discarded")
        new["sources"]=sources
        new["facts"]=facts
    if seen!=set(original):
        raise ReviewError("Saved research notes omit or add exact product identities")
    validate_research_packet(updated,evidence,drafts,evidence_file)
    output=Path(output).expanduser().resolve()
    if (output.exists() or output.parent!=drafts.parent or
            output.suffix.lower()!=".json" or output.is_relative_to(HERE)
            or any((p/".git").exists() for p in (output,*output.parents))):
        raise ReviewError("Choose a NEW private merged research file beside the 49 draft candidates")
    output.write_text(json.dumps(updated,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
    return updated


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--saved",required=True,type=Path)
    p.add_argument("--new-research",required=True,type=Path)
    p.add_argument("--drafts",required=True,type=Path)
    p.add_argument("--exceptions",required=True,type=Path)
    p.add_argument("--evidence",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args(argv)
    try:
        merged=migrate_saved_notes(
            args.saved,args.new_research,args.drafts,args.exceptions,
            args.evidence,args.out,
        )
    except (ValueError,OSError,KeyError,TypeError) as exc:
        p.error(str(exc))
    print("PRIVATE research notes safely migrated; no publication.")
    print("  Products:",merged["candidate_count"])
    print("  Identity warnings applied:",sum(bool(x["identity_warnings"]) for x in merged["items"]))
    print("  Owner-checked facts preserved:",sum(
        sum(bool(f["owner_checked"]) for f in row["facts"])
        for row in merged["items"]
    ))
    print("  New private file:",args.out)


if __name__=="__main__":
    main()
