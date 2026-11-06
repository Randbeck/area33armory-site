#!/usr/bin/env python3
"""Prepare actual Area 33 web pages with an APPROVED v2 catalog in private staging.

Does not deploy, modify Git, publish to any server, authorize product rights,
remove live media, or treat an RSR draft as an approved listing. Previous
approved snapshots and withdrawal records are verified when provided.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from prepare_approved_catalog_shards import _private_destination, _encode
from stage_private_media_withdrawal import (
    _approved_previous, PrivateWithdrawalError,
)

SITE = Path(__file__).resolve().parents[1]

from catalog_static_allowlist import STATIC


class ReleasePreflightError(ValueError):
    pass


def _trusted_source(root: Path, name: str) -> Path:
    path = root.joinpath(*Path(name).parts)
    if (path.is_symlink() or not path.is_file()
            or not path.resolve().is_relative_to(root)):
        raise ReleasePreflightError("Expected static website file is unavailable")
    return path


def _check_release_status(root: Path, index: dict) -> str:
    """Release scripts write PRIVATE audit files; never accept a public draft."""
    standard = root / "catalog-private-release-audit.json"
    withdrawal = root / "catalog-private-rights-withdrawal-audit.json"
    if standard.is_file() == withdrawal.is_file():
        raise ReleasePreflightError("Expected one private release-builder audit")
    audit = standard if standard.is_file() else withdrawal
    if audit.is_symlink():
        raise ReleasePreflightError("Private audit cannot be symlinked")
    raw = json.loads(audit.read_text(encoding="utf-8"))
    if audit == standard:
        if (raw.get("schema") != "area33.catalog.private_release_audit.v1"
                or raw.get("version") != index["version"]
                or raw.get("owner_approved_public_record_count") != index["total"]
                or raw.get("published") is not False
                or raw.get("website_modified") is not False
                or type(raw.get("source_approved_bundle_count")) is not int
                or raw["source_approved_bundle_count"] < 0):
            raise ReleasePreflightError("Private owner-approved release audit is invalid")
        if raw.get("release_kind") == "approved_refresh":
            if (raw.get("previous_snapshot_verified") is not True or
                    not isinstance(raw.get("previous_version"), str) or
                    not raw["previous_version"].startswith("r")):
                raise ReleasePreflightError("Approved refresh needs verified prior release evidence")
            return "approved_refresh"
        if raw.get("release_kind") is not None or raw["source_approved_bundle_count"] < 1:
            raise ReleasePreflightError("Owner-approved release requires approved source bundles")
        return "owner_approved_builder"
    if (raw.get("schema") != "area33.catalog.private_rights_withdrawal.v1"
            or raw.get("new_version") != index["version"]
            or raw.get("retained_product_count") != index["total"]
            or raw.get("deployment_performed") is not False
            or raw.get("site_changed") is not False):
        raise ReleasePreflightError("Private rights-withdrawal audit is invalid")
    return "reviewed_rights_withdrawal"


def _withdrawal_ids(root: Path, style: str) -> set[str]:
    if style in ("owner_approved_builder", "approved_refresh"):
        audit = json.loads((root / "catalog-private-release-audit.json").read_text())
        reviewed = audit.get("approved_withdrawals", [])
    else:
        path = root / "catalog-private-withdrawals.json"
        if path.is_symlink() or not path.is_file():
            raise ReleasePreflightError("No reviewed withdrawal evidence")
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("schema") != "area33.catalog.withdrawals.private.v1":
            raise ReleasePreflightError("Unexpected withdrawal evidence")
        reviewed = doc.get("items")
    if not isinstance(reviewed, list):
        raise ReleasePreflightError("Invalid withdrawal review set")
    ids = set()
    for entry in reviewed:
        if (not isinstance(entry, dict) or set(entry) != {
                "id", "reason", "approved_by", "reviewed_at"
            } or not isinstance(entry["id"], str) or entry["id"] in ids
                or not isinstance(entry["reason"], str)
                or len(entry["reason"].strip()) < 3
                or not isinstance(entry["approved_by"], str)
                or len(entry["approved_by"].strip()) < 3):
            raise ReleasePreflightError("Each withdrawn item needs exact approved review")
        try:
            day = date.fromisoformat(entry["reviewed_at"])
        except (TypeError, ValueError) as exc:
            raise ReleasePreflightError("Invalid withdrawal date") from exc
        if day > date.today():
            raise ReleasePreflightError("Withdrawal review is in the future")
        ids.add(entry["id"])
    return ids


def prepare_private_website_preview(
    release_root: Path, output_root: Path,
    *, previous_release_root: Path | None = None,
):
    """Verify approved source & stage real site UI and assets in a PRIVATE folder."""
    release_root = Path(release_root).expanduser().resolve()
    output_root = _private_destination(Path(output_root))
    if (output_root.is_relative_to(release_root)
            or release_root.is_relative_to(output_root)):
        raise ReleasePreflightError("Preview must not contain original approved release")
    index, products, provenance, media = _approved_previous(release_root)
    if not products and previous_release_root is None:
        raise ReleasePreflightError(
            "An empty catalog is only valid as a reviewed withdrawal from a previous release"
        )
    style = _check_release_status(release_root, index)

    new_ids = {p["id"] for p in products}
    previous_ids = set()
    prior_version = None
    obsolete_photos = []
    if previous_release_root is not None:
        previous_root = Path(previous_release_root).expanduser().resolve()
        prior, old_products, old_provenance, old_media = _approved_previous(previous_root)
        _check_release_status(previous_root, prior)
        if previous_root == release_root:
            raise ReleasePreflightError("Previous release must be distinct")
        if style == "approved_refresh":
            audit = json.loads(
                (release_root/"catalog-private-release-audit.json").read_text()
            )
            if audit.get("previous_version") != prior["version"]:
                raise ReleasePreflightError("Refresh audit does not match reviewed previous release")
        prior_version = prior["version"]
        previous_ids = {p["id"] for p in old_products}
        previous_urls = set(old_media)
        current_urls = set(media)
        obsolete_photos = sorted(previous_urls-current_urls)
        removed = previous_ids-new_ids
        confirmed = _withdrawal_ids(release_root, style)
        if removed != confirmed:
            raise ReleasePreflightError(
                "Changed approved snapshot must list exactly every reviewed removal"
            )
    elif style in ("reviewed_rights_withdrawal", "approved_refresh"):
        raise ReleasePreflightError(
            "A reviewed withdrawal or approved refresh requires the previous approved release"
        )

    created = sorted(new_ids-previous_ids)
    withdrawn = sorted(previous_ids-new_ids)
    changed = []
    if previous_release_root is not None:
        by_id = {p["id"]: p for p in old_products}
        changed = sorted(p["id"] for p in products if (
            p["id"] in by_id and p != by_id[p["id"]]
        ))

    report = {
        "schema": "area33.private_site_release_preflight.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "catalog_version": index["version"],
        "previous_version": prior_version,
        "approved_product_count": index["total"],
        "new_product_count": len(created),
        "changed_product_count": len(changed),
        "withdrawn_product_count": len(withdrawn),
        "approved_image_file_count": len(media),
        "index_sha256": hashlib.sha256(
            (release_root/"assets/catalog-index.v2.json").read_bytes()
        ).hexdigest(),
        "public_path_eligible_files": len(STATIC) + 1 + len(index["shards"]) + len(media),
        "reviewed_withdrawn_public_ids": withdrawn,
        "obsolete_image_urls_require_separate_host_removal": obsolete_photos,
        "pending_deployment_verification": [
            "Confirm every current grant is still active and unrevoked",
            "Verify hosting credentials, domain and publication owner authorization",
            "Remove obsolete server image files, old shards and CDN cache copies",
            "Verify rollback cannot reintroduce revoked media",
            "Verify MAP, shipping restrictions and customer sales eligibility separately",
        ],
        "private_preview_only": True,
        "site_modified": False,
        "deployed": False,
    }

    output_root.parent.mkdir(parents=True,exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".area33-preview-",dir=output_root.parent))
    try:
        site = temp/"site"
        for name in STATIC:
            source = _trusted_source(SITE, name)
            target = site.joinpath(*Path(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source,target)
        # Hard fail if the static fallback has any public products already.
        fallback = json.loads((site/"assets/catalog-public.json").read_text(encoding="utf-8"))
        if fallback.get("schema") != "area33.catalog.public.v1" or fallback.get("items") != []:
            raise ReleasePreflightError("Legacy static fallback unexpectedly contains product records")
        files = ["assets/catalog-index.v2.json"]
        files.extend(shard["url"] for shard in index["shards"])
        files.extend(sorted(media))
        for name in files:
            source = _trusted_source(release_root, name)
            target = site.joinpath(*Path(name).parts)
            if target.exists():
                raise ReleasePreflightError("Staged site has a public file collision")
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target)
            if hashlib.sha256(source.read_bytes()).digest()!=hashlib.sha256(
                target.read_bytes()
            ).digest():
                raise ReleasePreflightError("Approved static asset changed when copied")
        # Never place preflight report, source provenance, permission files,
        # dealer data or the former release audit inside the served site.
        (temp/"preflight-private-report.json").write_bytes(_encode(report))
        (temp/"README_PRIVATE.txt").write_text(
            "PRIVATE offline Area 33 preview. Do NOT upload the 'site' folder.\n"
            "For a local browser view, serve 'site' ONLY at 127.0.0.1 using "
            "scripts/serve_private_catalog_preview.py. "
            "This work did NOT publish anything or approve rights.\n",
            encoding="utf-8",
        )
        temp.rename(output_root)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return report


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--private-approved-release",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--previous-approved-release",type=Path)
    p.add_argument("--prepare-private-preview",action="store_true")
    args=p.parse_args(argv)
    if not args.prepare_private_preview:
        p.error("Explicit --prepare-private-preview required; never deploys")
    try:
        report=prepare_private_website_preview(
            args.private_approved_release,args.out,
            previous_release_root=args.previous_approved_release,
        )
    except (ValueError,OSError,KeyError,TypeError) as exc:
        p.error(str(exc))
    print("Actual Area 33 site in PRIVATE LOCAL preview:")
    print("  Approved products:",report["approved_product_count"])
    print("  New / changed / withdrawn:",
          report["new_product_count"],report["changed_product_count"],
          report["withdrawn_product_count"])
    print("  Approved image files:",report["approved_image_file_count"])
    print("  Preview output:",args.out)
    print("  Live website, Git and published catalog: UNCHANGED")


if __name__=="__main__":
    main()
