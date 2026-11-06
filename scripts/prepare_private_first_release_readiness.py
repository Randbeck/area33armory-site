#!/usr/bin/env python3
"""Summarize REAL private Area 33 owner-review progress against catalog evidence.

Each product is clearly classified as: private_handoff_eligible,
needs_owner_review, needs_independent_research, or identity_conflict_hold.
This report NEVER approves any product, verifies inventory or licenses,
modifies the original 49 drafts, sends data to a website, or deploys.

Owner-checked status remains an assertion, not external evidence of reseller
eligibility. An approval is "private handoff eligible", NOT "live publishable".
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile

from build_private_catalog_review import validate_source, ReviewError
from build_private_text_batch_review import (
    _private_file, source_batch, validated_private_evidence,
)
from prepare_private_product_research import (
    validate_research_packet, CONFLICT_LEADS,
)
from prepare_approved_catalog_shards import _private_destination, _encode
from publish_approved_catalog import build as verify_publisher

SCHEMA="area33.catalog.private_first_release_readiness.v1"
REQUIRED_CHECKS=("owner_publication","exact_identity","content_review","offered_for_sale")
STATES={
    "private_handoff_eligible":0,
    "owner_review_pending":1,
    "independent_research_needed":2,
    "identity_conflict_hold":3,
}


class PrivateReadinessError(ValueError):
    pass


def _sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_complete(row:dict)->bool:
    try:
        day=date.fromisoformat(row.get("source_checked_at",""))
    except (TypeError,ValueError):
        return False
    if day>date.today():
        return False
    return (
        row.get("status")=="published"
        and row.get("listing_mode")=="text_only"
        and row.get("content_origin")=="owner_written"
        and row.get("photos")==[]
        and row.get("rights_source")==""
        and row["approvals"].get("media_rights") is False
        and all(row["approvals"].get(k) is True for k in REQUIRED_CHECKS)
        and isinstance(row.get("identity_evidence_label"),str)
        and bool(row["identity_evidence_label"].strip())
        and isinstance(row.get("description"),str)
        and 18<=len(row["description"].strip())<=200
    )


def create_private_readiness(
    drafts:Path,exceptions:Path,evidence_file:Path,research_file:Path,
    output:Path,*,review_progress:Path|None=None,
):
    drafts=_private_file(drafts)
    exceptions=_private_file(exceptions)
    evidence_file=_private_file(evidence_file)
    research_file=_private_file(research_file)
    output=_private_destination(Path(output))
    baseline,held=source_batch(drafts,exceptions)
    evidence=validated_private_evidence(evidence_file,drafts,exceptions,baseline)
    packet=json.loads(research_file.read_text(encoding="utf-8"))
    research=validate_research_packet(packet,evidence,drafts,evidence_file)
    base_by_id={row["id"]:row for row in baseline}
    if review_progress is None:
        progress=baseline
        progress_sha=None
    else:
        review_progress=_private_file(review_progress)
        progress_sha=_sha(review_progress)
        progress,previews=validate_source(review_progress)
        if (len(progress)!=len(baseline) or any(previews)
                or {row["id"] for row in progress}!=set(base_by_id)):
            raise PrivateReadinessError("Saved progress must contain all unchanged original candidate IDs")
        for row in progress:
            original=base_by_id[row["id"]]
            if (row["manufacturer"]!=original["manufacturer"] or
                    row["model"]!=original["model"] or
                    row["listing_mode"]!="text_only" or row["photos"]!=[] or
                    row["rights_source"]!="" or
                    row["approvals"]["media_rights"] is not False):
                raise PrivateReadinessError("Saved progress has an identity or photo-rights mismatch")
    by_research={r["id"]:r for r in research}
    by_evidence={r["id"]:r for r in evidence}
    findings=[]
    handoff=[]
    for row in progress:
        rec=by_research[row["id"]]
        ref=by_evidence[row["id"]]
        warnings=rec["identity_warnings"]
        known_conflict=CONFLICT_LEADS.get(ref["recorded_manufacturer_part_number"])
        if (known_conflict and
                ref["recorded_upc"] in known_conflict["observed_upcs"]
                and not warnings):
            raise PrivateReadinessError("Known UPC conflict was suppressed from research")
        checked=sum(1 for x in rec["facts"] if x["owner_checked"])
        fully_reviewed=_is_complete(row)
        reason=[]
        if warnings:
            state="identity_conflict_hold"
            reason.append("Two independent public listings disagree about the exact UPC: verify authoritative product identity")
        elif fully_reviewed:
            state="private_handoff_eligible"
            reason.append("All existing private owner confirmations present; separate sale/channel authorization still required")
            handoff.append(row)
        elif rec["sources"]:
            state="owner_review_pending"
            reason.append("Review cited exact-product claims and confirm identity, original copy and actual eligibility")
        else:
            state="independent_research_needed"
            reason.append("No independently sourced product facts recorded yet; research exact UPC and MPN first")
        if row["status"]=="published" and not fully_reviewed:
            # Do not silently accept a forged/inconsistent published status.
            state="owner_review_pending" if not warnings else "identity_conflict_hold"
            reason.append("INVALID owner-approved status: missing required confirmations or verified content")
        findings.append({
            "id":row["id"],
            "manufacturer":row["manufacturer"],
            "model":row["model"],
            "recorded_upc":ref["recorded_upc"],
            "recorded_mpn":ref["recorded_manufacturer_part_number"],
            "state":state,
            "source_count":len(rec["sources"]),
            "checked_fact_count":checked,
            "reason":"; ".join(reason),
            "identity_warnings":[x["code"] for x in warnings],
        })
    # Reuse the existing strict approved-only text publisher for all the
    # purportedly eligible products; do not trust browser checkbox JSON alone.
    if handoff:
        with tempfile.TemporaryDirectory(prefix="area33-ready-check-") as temp:
            approved_file=Path(temp)/"approved-check.json"
            approved_file.write_bytes(_encode(handoff))
            public,frames=verify_publisher(approved_file)
            if frames or len(public["items"])!=len(handoff):
                raise PrivateReadinessError("Independent text publisher rejected eligible review records")
    findings.sort(key=lambda x:(STATES[x["state"]],x["manufacturer"].casefold(),
                                x["model"].casefold(),x["recorded_mpn"]))
    counts={state:sum(x["state"]==state for x in findings) for state in STATES}
    report={
        "schema":SCHEMA,
        "created_at":datetime.now(timezone.utc).isoformat(),
        "baseline_drafts_sha256":_sha(drafts),
        "identity_evidence_sha256":_sha(evidence_file),
        "research_packet_sha256":_sha(research_file),
        "saved_review_progress_sha256":progress_sha,
        "candidate_count":len(baseline),
        "held_identity_exceptions":len(held),
        "counts":counts,
        "items":findings,
        "public_site_modified":False,
        "approval_created":False,
        "release_published":False,
        "notice":"Private triage only. An owner-reviewed item is eligible for a separate private handoff, never automatically for public sale or deployment.",
    }
    if sum(counts.values())!=len(baseline):
        raise PrivateReadinessError("Internal status counts disagree with original draft total")
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():
        raise PrivateReadinessError("Readiness folder already exists")
    import shutil
    temp=Path(tempfile.mkdtemp(prefix=".area33-ready-",dir=output.parent))
    try:
        (temp/"private-first-release-readiness.json").write_bytes(_encode(report))
        with (temp/"private-first-release-worklist.csv").open("w",newline="",encoding="utf-8-sig") as handle:
            writer=csv.DictWriter(handle,fieldnames=[
                "state","manufacturer","model","recorded_mpn",
                "recorded_upc","source_count","checked_fact_count",
                "reason","id",
            ])
            writer.writeheader()
            for row in findings:
                writer.writerow({key:row[key] for key in writer.fieldnames})
        (temp/"README_PRIVATE.txt").write_text(
            "PRIVATE owner decision worklist. No new product approvals, rights, "
            "sales authorization, live inventory, price or website changes. "
            "Research links and public seller facts require human independent review.\n",
            encoding="utf-8",
        )
        temp.rename(output)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drafts",required=True,type=Path)
    parser.add_argument("--exceptions",required=True,type=Path)
    parser.add_argument("--evidence",required=True,type=Path)
    parser.add_argument("--research",required=True,type=Path)
    parser.add_argument("--saved-progress",type=Path)
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--prepare-private-readiness",action="store_true")
    args=parser.parse_args(argv)
    if not args.prepare_private_readiness:
        parser.error("Explicit --prepare-private-readiness required")
    try:
        report=create_private_readiness(
            args.drafts,args.exceptions,args.evidence,args.research,args.out,
            review_progress=args.saved_progress,
        )
    except (ValueError,OSError,TypeError,KeyError) as exc:
        parser.error(str(exc))
    print("PRIVATE first-release decision worklist created; NOT published.")
    print("  Original candidates:",report["candidate_count"])
    for name,count in report["counts"].items():
        print(f"  {name}: {count}")
    print("  Quarantined identity exceptions:",report["held_identity_exceptions"])
    print("  Output:",args.out)


if __name__=="__main__":
    main()
