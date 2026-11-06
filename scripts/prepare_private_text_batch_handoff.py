#!/usr/bin/env python3
"""Validate a completed PRIVATE owner review and stage only approved text listings.

The browser review's status/checkboxes are NOT accepted at face value:
every approved item is revalidated by the strict existing catalog publisher.
Unapproved drafts are skipped without alteration, identity exceptions never
graduate automatically, and photos, prices and supplier copy are not imported.

Optional --stage-first-private-release creates a PRIVATE owner-approved v2
release. No GitHub, GoDaddy, live site or publication is modified.
"""
from __future__ import annotations

import argparse
from datetime import date,datetime,timezone
import hashlib
import json
from pathlib import Path
import tempfile
import shutil

from build_private_text_batch_review import source_batch,_private_file
from build_private_catalog_review import validate_source,ReviewError
from prepare_approved_catalog_shards import (
    prepare_private_release,_private_destination,_encode,
)
from publish_approved_catalog import build as verify_approved_catalog


class PrivateHandoffError(ValueError):
    pass


def _digest(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_private_text_handoff(
    input_file:Path,source_drafts:Path,exceptions_file:Path,out:Path,
    *,stage_private_release:bool=False,
):
    input_file=_private_file(input_file)
    source_drafts=_private_file(source_drafts)
    exceptions_file=_private_file(exceptions_file)
    out=_private_destination(Path(out))
    original,exceptions=source_batch(source_drafts,exceptions_file)
    baseline={item["id"]:item for item in original}
    rows,previews=validate_source(input_file)
    seen=set()
    approved=[]
    hold_count=0
    for row,pics in zip(rows,previews):
        ident=row["id"]
        if ident not in baseline or ident in seen:
            raise PrivateHandoffError("Handoff contains unknown or duplicated original catalog ID")
        seen.add(ident)
        orig=baseline[ident]
        if (row.get("listing_mode")!="text_only" or pics or
                row.get("photos")!=[] or row.get("rights_source","")!=""
                or row["approvals"]["media_rights"] is not False):
            raise PrivateHandoffError("Handoff contains a photo-based or rights-claiming record")
        if (row["manufacturer"]!=orig["manufacturer"] or row["model"]!=orig["model"]):
            raise PrivateHandoffError(
                "Manufacturer or exact model was changed; hold this product and re-intake "
                "the corrected identity with a new consistent public ID"
            )
        if row["status"]=="published":
            copy=row.get("description")
            if not isinstance(copy,str) or not 18<=len(copy.strip())<=200:
                raise PrivateHandoffError("Approved text requires a substantive original description")
            when=row.get("source_checked_at")
            try:
                reviewed=date.fromisoformat(when)
            except (TypeError,ValueError) as exc:
                raise PrivateHandoffError("Approved product has no valid identity evidence date") from exc
            if reviewed>date.today():
                raise PrivateHandoffError("Identity evidence review is future-dated")
            if row.get("content_origin")!="owner_written":
                raise PrivateHandoffError("Approved copy must be independently owner-written")
            approved.append(row)
        else:
            hold_count+=1
    if not approved:
        raise PrivateHandoffError("No individually approved text-only records; save progress and continue review")
    if len(approved)>100:
        raise PrivateHandoffError("A private approval bundle cannot exceed 100 products")
    if out.exists():
        raise PrivateHandoffError("Private handoff destination already exists")
    out.parent.mkdir(parents=True,exist_ok=True)
    temp=Path(tempfile.mkdtemp(prefix=".area33-private-approved-batch-",dir=out.parent))
    try:
        bundle=temp/"catalog-owner-approved-part-001.json"
        bundle.write_bytes(_encode(approved))
        public,frames=verify_approved_catalog(bundle)
        if frames or len(public["items"])!=len(approved):
            raise PrivateHandoffError("Approved-only server validation did not match reviewed text listings")
        if any(item["presentation_mode"]!="text_only" or item["images"]!=[]
               for item in public["items"]):
            raise PrivateHandoffError("Private handoff would introduce product photos")
        audit={
            "schema":"area33.catalog.private_owner_text_batch_handoff.v1",
            "created_at":datetime.now(timezone.utc).isoformat(),
            "input_sha256":_digest(input_file),
            "baseline_source_sha256":_digest(source_drafts),
            "exception_report_sha256":_digest(exceptions_file),
            "baseline_candidate_count":len(original),
            "review_input_count":len(rows),
            "individually_approved_count":len(approved),
            "other_input_records_kept_as_draft":hold_count,
            "quarantined_identity_exception_count":len(exceptions),
            "public_photographs_copied":0,
            "website_modified":False,
            "published":False,
            "private_approved_release_staged":bool(stage_private_release),
            "note":"Approvals are private human assertions, not automatic distributor/media/license grants.",
        }
        if stage_private_release:
            private_release=temp/"approved-private-v2-release"
            release_audit,index=prepare_private_release([bundle],private_release)
            if index["total"]!=len(approved) or release_audit["published"] is not False:
                raise PrivateHandoffError("First private release preparation was incomplete")
        (temp/"private-text-batch-review-audit.json").write_bytes(_encode(audit))
        (temp/"README_PRIVATE.txt").write_text(
            "PRIVATE approved-only review handoff. No website was changed.\n"
            "Review current product eligibility, exact identity and content origin "
            "before a separately authorized publication. Identity exceptions "
            "remain withheld; do not upload this folder into public GitHub.\n",
            encoding="utf-8",
        )
        temp.rename(out)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return audit


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",required=True,type=Path,
                   help="Downloaded approved-only JSON or saved private review progress")
    p.add_argument("--source-drafts",required=True,type=Path)
    p.add_argument("--exceptions",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--stage-first-private-release",action="store_true")
    args=p.parse_args(argv)
    try:
        audit=prepare_private_text_handoff(
            args.input,args.source_drafts,args.exceptions,args.out,
            stage_private_release=args.stage_first_private_release,
        )
    except (OSError,ValueError,KeyError,TypeError) as exc:
        p.error(str(exc))
    print("PRIVATE owner-reviewed text-only catalog handoff. NOTHING published.")
    print("  Individually approved:",audit["individually_approved_count"])
    print("  Quarantined identity exceptions:",audit["quarantined_identity_exception_count"])
    print("  Photos copied: 0")
    print("  Private first release staged:",audit["private_approved_release_staged"])
    print("  Private output:",args.out)


if __name__=="__main__":
    main()
