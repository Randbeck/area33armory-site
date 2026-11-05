"""Verify current owner-signed Randbeck supplier grants and private cohort receipt.

Never assumes a supplier license from distributor connectivity or web evidence.
The receipt can only FILTER private draft intake; it never sets publication
approvals or public rights/source flags.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone, timedelta
import hashlib
import hmac
import json
from pathlib import Path
import re

LEDGER_SCHEMA="randbeck.area33.catalog_scope_ledger.v1"
REPORT_SCHEMA="randbeck.area33.private_scope_eligibility.v1"
STAGING_SCHEMA="randbeck.area33.private_catalog_staging.v1"
DOMAIN="area33armory.com"
HEX64=re.compile(r"^[0-9a-f]{64}$")
RECEIPT_AGE=timedelta(minutes=30)
RECEIPT_FIELDS={
    "schema","publication_enabled","supplier_license_validated_by_platform",
    "ledger_revision","source_snapshot_modified_at","evaluated_at","source_products",
    "private_policy_candidates","held_exceptions","reasons","note","items",
    "source_staging_sha256","ledger_signature","receipt_hmac_sha256",
}
ITEM_FIELDS={
    "source_sku","source_category","status","blocking_reasons","grant_id",
    "proposed_public_category","proposed_public_type","media_next_step",
    "owner_publication_approved","rights_approved_for_publication",
    "actual_stock_verified",
}


class ScopeReceiptError(ValueError):
    pass


def _mac(value,key):
    content=json.dumps(value,sort_keys=True,separators=(",",":"),
                       ensure_ascii=False).encode("utf-8")
    return hmac.new(key,content,hashlib.sha256).hexdigest()


def validate_scoped_receipt(staging_path:Path,receipt_path:Path,
                            ledger_path:Path,key_path:Path,
                            *,now=None):
    """Require signed, time-bound policy receipt for exact private source bytes.

    The ledger must be current as supplied by the owner; no remote rights
    server exists. Each grant's direct evidence file is rehashed locally.
    """
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ScopeReceiptError("Timestamp must be timezone-aware")
    key_path=Path(key_path).expanduser().resolve()
    if not key_path.is_file() or key_path.stat().st_size!=32:
        raise ScopeReceiptError("Missing private scope signing key")
    key=key_path.read_bytes()
    source_bytes=Path(staging_path).expanduser().resolve().read_bytes()
    staging=json.loads(source_bytes)
    ledger=json.loads(Path(ledger_path).expanduser().resolve().read_text(encoding="utf-8"))
    receipt=json.loads(Path(receipt_path).expanduser().resolve().read_text(encoding="utf-8"))

    if (not isinstance(ledger,dict) or ledger.get("schema")!=LEDGER_SCHEMA
            or ledger.get("site")!=DOMAIN or
            type(ledger.get("revision")) is not int or
            not isinstance(ledger.get("grants"),list) or
            not isinstance(ledger.get("revocations"),list) or
            not isinstance(ledger.get("signature"),str)):
        raise ScopeReceiptError("Invalid owner authorization ledger")
    if (not hmac.compare_digest(
        _mac({k:v for k,v in ledger.items() if k!="signature"},key),
        ledger["signature"],
    )):
        raise ScopeReceiptError("Owner authorization ledger signature mismatch")
    if (not isinstance(receipt,dict) or set(receipt)!=RECEIPT_FIELDS or
            receipt.get("schema")!=REPORT_SCHEMA or
            receipt.get("publication_enabled") is not False or
            receipt.get("supplier_license_validated_by_platform") is not False or
            not isinstance(receipt.get("receipt_hmac_sha256"),str) or
            not hmac.compare_digest(
                _mac({k:v for k,v in receipt.items() if k!="receipt_hmac_sha256"},key),
                receipt["receipt_hmac_sha256"],
            )):
        raise ScopeReceiptError("Unverified or unauthenticated private cohort receipt")
    if receipt["ledger_revision"]!=ledger["revision"] or receipt["ledger_signature"]!=ledger["signature"]:
        raise ScopeReceiptError("Cohort was evaluated under a different owner policy revision")
    if receipt["source_staging_sha256"]!=hashlib.sha256(source_bytes).hexdigest():
        raise ScopeReceiptError("Cohort receipt does not match the exact staging input")
    try:
        evaluated=datetime.fromisoformat(receipt["evaluated_at"])
        source_observed=datetime.fromisoformat(staging["private_inventory_snapshot_modified_at"])
        if evaluated.tzinfo is None or source_observed.tzinfo is None:
            raise ValueError()
    except (TypeError,KeyError,ValueError) as exc:
        raise ScopeReceiptError("Missing source and evaluation timestamps") from exc
    if (evaluated>now or now-evaluated>RECEIPT_AGE):
        raise ScopeReceiptError("Source eligibility receipt expired; re-evaluate current policy")
    if receipt["source_snapshot_modified_at"]!=staging["private_inventory_snapshot_modified_at"]:
        raise ScopeReceiptError("Scope receipt and source freshness metadata disagree")
    if (not isinstance(staging,dict) or staging.get("schema")!=STAGING_SCHEMA
            or staging.get("source")!="RSR" or
            staging.get("publication_enabled") is not False or
            not isinstance(staging.get("items"),list) or
            staging.get("products_staged")!=len(staging["items"])):
        raise ScopeReceiptError("Cohort source staging is invalid")
    items=receipt.get("items")
    if (not isinstance(items,list) or len(items)!=len(staging["items"])
            or receipt["source_products"]!=len(items)):
        raise ScopeReceiptError("Cohort and source item counts differ")
    by_sku={}
    counts=Counter()
    for raw,prior in zip(items,staging["items"]):
        if (not isinstance(raw,dict) or set(raw)!=ITEM_FIELDS or
                raw.get("source_sku")!=prior.get("source_sku") or
                raw.get("source_category")!=prior.get("source_category") or
                raw.get("owner_publication_approved") is not False or
                raw.get("rights_approved_for_publication") is not False or
                raw.get("actual_stock_verified") is not False or
                raw.get("status") not in ("policy_eligible_private_candidate","exception") or
                not isinstance(raw.get("blocking_reasons"),list) or
                not all(isinstance(x,str) for x in raw["blocking_reasons"]) or
                raw["source_sku"] in by_sku):
            raise ScopeReceiptError("Unsafe or contradictory source cohort outcome")
        if (raw["status"]=="policy_eligible_private_candidate" and
                (raw["blocking_reasons"] or not raw.get("grant_id"))):
            raise ScopeReceiptError("Eligible cohort item has missing rights evidence")
        if raw["status"]=="exception" and not raw["blocking_reasons"]:
            raise ScopeReceiptError("Exception must contain an explicit blocker")
        by_sku[raw["source_sku"]]=raw
        counts[raw["status"]]+=1
    if (counts["policy_eligible_private_candidate"]!=receipt["private_policy_candidates"]
            or counts["exception"]!=receipt["held_exceptions"]):
        raise ScopeReceiptError("Cohort eligibility totals do not match signed receipt")
    revoked={r.get("grant_id") for r in ledger["revocations"]}
    authorized={g.get("id"):g for g in ledger["grants"]
                if g.get("id") not in revoked}
    for entry in items:
        if entry["status"]!="policy_eligible_private_candidate":
            continue
        grant=authorized.get(entry["grant_id"])
        if grant is None or grant.get("supplier")!=staging["source"] or (
            grant.get("source_category")!=entry["source_category"]
        ):
            raise ScopeReceiptError("Cohort references unauthorized or revoked scope")
        owner=grant.get("owner_review") or {}
        try:
            approved=date.fromisoformat(owner["approved_on"])
            expires=date.fromisoformat(owner["expires_on"])
        except (KeyError,TypeError,ValueError) as exc:
            raise ScopeReceiptError("Invalid owner grant dates") from exc
        if not approved<=now.date()<=expires:
            raise ScopeReceiptError("Supplier authorization is expired")
        freshness=grant.get("max_snapshot_age_hours")
        if (type(freshness) is not int or not 1<=freshness<=168 or
                source_observed>now or
                now-source_observed>timedelta(hours=freshness)):
            raise ScopeReceiptError("Supplier source snapshot is stale under owner scope")
        ev=grant.get("evidence") or {}
        path=Path(str(ev.get("private_file") or "")).expanduser().resolve()
        if (not path.is_file() or not isinstance(ev.get("sha256"),str) or
                not HEX64.fullmatch(ev["sha256"]) or
                hashlib.sha256(path.read_bytes()).hexdigest()!=ev["sha256"]):
            raise ScopeReceiptError("Supplier permission source evidence was changed or removed")
        perms=grant.get("permissions") or {}
        if (perms.get("show_source_product_listing") is not True or
                perms.get("display_original_product_photo") is not True):
            raise ScopeReceiptError("Source listing or image rights missing")
        staged=next(x for x in staging["items"] if x["source_sku"]==entry["source_sku"])
        if (any(p.get("exif_present") is True for p in staged.get("source_media",[]))
                and perms.get("display_metadata_cleared_photo") is not True):
            raise ScopeReceiptError("Source image transformation is not approved")
        if staged.get("description") and perms.get("reuse_source_description") is not True:
            raise ScopeReceiptError("Description permission missing")
        if (entry.get("proposed_public_category")!=grant.get("public_category") or
                entry.get("proposed_public_type")!=grant.get("product_type")):
            raise ScopeReceiptError("Public category proposal differs from grant")

    return {
        "eligible_by_sku":by_sku,
        "eligible_product_count":counts["policy_eligible_private_candidate"],
        "held_product_count":counts["exception"],
        "scope_revision":ledger["revision"],
        "scope_authorization_signed":True,
        "release_approved":False,
    }
