#!/usr/bin/env python3
"""Build a controlled, PRIVATE Area 33 deployment/rollback package.

Verifies the actual staged website against an approved private catalog release,
separately checked rights holds, and an optional previously-approved release.
Generates exact asset hashes and immutable-first/activate-index-last operations.
No Git push, CDN request, live upload, credentials, website edit or auto rollback.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from catalog_release_safety import (
    read_rights_holds, blocked_records, reject_held_products,
)
from prepare_approved_catalog_shards import _private_destination, _encode
from stage_private_media_withdrawal import _approved_previous
from stage_private_catalog_site_preview import (
    SITE, STATIC, _check_release_status, _withdrawal_ids,
)


class ControlledReleaseError(ValueError):
    pass


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _site_files(root: Path) -> dict[str, Path]:
    if not root.is_dir() or root.is_symlink():
        raise ControlledReleaseError("Release site folder is not an ordinary private directory")
    found = {}
    for candidate in root.rglob("*"):
        if candidate.is_symlink():
            raise ControlledReleaseError("Release cannot contain symlinked files or directories")
        if not candidate.is_file():
            continue
        name = candidate.relative_to(root).as_posix()
        if name.startswith(".") or not candidate.resolve().is_relative_to(root):
            raise ControlledReleaseError("Unsafe release file path")
        found[name] = candidate
    return found


def _expected_paths(index: dict, media: dict) -> set[str]:
    return set(STATIC) | {"assets/catalog-index.v2.json"} | {
        entry["url"] for entry in index["shards"]
    } | set(media)


def _copy_exact_file(source: Path, target: Path) -> None:
    if source.is_symlink() or not source.is_file():
        raise ControlledReleaseError("Release source file is missing or symlinked")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source,target)
    if _sha_file(source) != _sha_file(target):
        raise ControlledReleaseError("Release bytes changed while copying")


def _previous_rollback_files(prior_root: Path, prior_index: dict,
                             prior_media: dict, static_source: dict) -> dict:
    paths = {}
    for name in STATIC:
        paths[name] = static_source[name]
    paths["assets/catalog-index.v2.json"] = prior_root / "assets/catalog-index.v2.json"
    for shard in prior_index["shards"]:
        paths[shard["url"]] = prior_root.joinpath(*Path(shard["url"]).parts)
    paths.update(prior_media)
    return paths


def stage_controlled_deployment(
    private_preview: Path, approved_release: Path, rights_holds_file: Path,
    output: Path, *, previous_release: Path | None = None,
):
    private_preview = Path(private_preview).expanduser().resolve()
    approved_release = Path(approved_release).expanduser().resolve()
    output = _private_destination(Path(output))
    for src in (private_preview,approved_release):
        if output.is_relative_to(src) or src.is_relative_to(output):
            raise ControlledReleaseError("Deployment package may not contain private source folders")
    preview_site = private_preview / "site"
    report_path = private_preview / "preflight-private-report.json"
    if not report_path.is_file() or report_path.is_symlink():
        raise ControlledReleaseError("Missing private, validated website preflight report")
    preflight = json.loads(report_path.read_text(encoding="utf-8"))
    if (preflight.get("schema") != "area33.private_site_release_preflight.v1"
            or preflight.get("deployed") is not False
            or preflight.get("site_modified") is not False
            or preflight.get("private_preview_only") is not True):
        raise ControlledReleaseError("Only unpublished private website previews can be packaged")
    index, products, provenance, media = _approved_previous(approved_release)
    style = _check_release_status(approved_release, index)
    holds = read_rights_holds(rights_holds_file)
    reject_held_products(products, provenance, holds)
    if (preflight.get("catalog_version") != index["version"]
            or preflight.get("approved_product_count") != index["total"]
            or preflight.get("index_sha256") !=
                _sha_file(approved_release/"assets/catalog-index.v2.json")):
        raise ControlledReleaseError("Website preflight and approved release disagree")
    public_files = _site_files(preview_site)
    required_paths = _expected_paths(index, media)
    if set(public_files) != required_paths:
        raise ControlledReleaseError(
            "Preview contains a missing, unexpected or private website file"
        )
    for name in STATIC:
        expected = SITE.joinpath(*Path(name).parts)
        if expected.is_symlink() or not expected.is_file() or (
            _sha_file(public_files[name]) != _sha_file(expected)
        ):
            raise ControlledReleaseError("Preview no longer matches reviewed website code")
    approved_files = {"assets/catalog-index.v2.json":
                      approved_release/"assets/catalog-index.v2.json"}
    approved_files.update({
        desc["url"]: approved_release.joinpath(*Path(desc["url"]).parts)
        for desc in index["shards"]
    })
    approved_files.update(media)
    for name, original in approved_files.items():
        if _sha_file(original) != _sha_file(public_files[name]):
            raise ControlledReleaseError("Staged site asset differs from approved catalog bytes")

    prior_root = None
    old_index, old_provenance, old_media, old_products = None,None,None,None
    rollback_blockers = {}
    prior_files = {}
    previously_approved_ids = set()
    if previous_release is not None:
        prior_root = Path(previous_release).expanduser().resolve()
        if prior_root == approved_release:
            raise ControlledReleaseError("Previous and candidate release cannot be identical")
        old_index, old_products, old_provenance, old_media = _approved_previous(prior_root)
        _check_release_status(prior_root, old_index)
        if preflight.get("previous_version") != old_index["version"]:
            raise ControlledReleaseError("Preflight did not review this previous release")
        previously_approved_ids = {p["id"] for p in old_products}
        removed = previously_approved_ids - {p["id"] for p in products}
        if _withdrawal_ids(approved_release, style) != removed:
            raise ControlledReleaseError("A prior approved item was removed without review")
        rollback_blockers = blocked_records(old_products, old_provenance, holds)
        prior_files = _previous_rollback_files(prior_root,old_index,old_media,public_files)
        # A cached URL may still reference old pixels; never silently replace
        # previously published image bytes at an unchanged path.
        for url in set(old_media) & set(media):
            if _sha_file(old_media[url]) != _sha_file(media[url]):
                raise ControlledReleaseError(
                    "Approved image changed at a previously used URL; cache-safe replacement required"
                )
    elif (style in ("approved_refresh","reviewed_rights_withdrawal") or
          preflight.get("previous_version") is not None):
        raise ControlledReleaseError("Refresh/withdrawal deployment needs prior approved snapshot")

    newly_approved_ids = {p["id"] for p in products} - previously_approved_ids
    withdrawn_ids = previously_approved_ids - {p["id"] for p in products}
    obsolete_images = sorted(set(old_media or {}) - set(media))
    old_shards = {p["url"] for p in old_index["shards"]} if old_index else set()
    new_shards = {p["url"] for p in index["shards"]}
    current_hashes = {name:_sha_file(path) for name,path in public_files.items()}
    prior_hashes = {name:_sha_file(path) for name,path in prior_files.items()}
    if previous_release is not None:
        if set(obsolete_images) != set(
            preflight.get("obsolete_image_urls_require_separate_host_removal", [])
        ):
            raise ControlledReleaseError("Preflight image deletion plan is incomplete")
    rollback_allowed = bool(prior_root) and not rollback_blockers
    rollback_reason = (
        "Previous approved catalog passes current rights holds"
        if rollback_allowed else
        "Prior catalog cannot be reused because rights are now held"
        if rollback_blockers else
        "No verified previous approved catalog available"
    )
    manifest = {
        "schema":"area33.catalog.private_controlled_release.v1",
        "created_at":datetime.now(timezone.utc).isoformat(),
        "catalog_version":index["version"],
        "previous_version":old_index["version"] if old_index else None,
        "rights_holds_sha256":holds["sha256"],
        "candidate_index_sha256":_sha_file(approved_files["assets/catalog-index.v2.json"]),
        "candidate_approved_products":len(products),
        "new_product_count":len(newly_approved_ids),
        "withdrawn_product_count":len(withdrawn_ids),
        "upload_immutable_first":sorted(new_shards | (set(media)-set(old_media or {}))),
        "update_mutable_site_files":sorted(name for name in STATIC
                                           if prior_hashes.get(name) != current_hashes[name]),
        "activate_index_last":"assets/catalog-index.v2.json",
        "remove_old_images_after_switch":obsolete_images,
        "remove_old_shards_after_switch":sorted(old_shards-new_shards),
        "invalidate_cdn_after_removal":sorted(
            set(obsolete_images) | old_shards |
            {"assets/catalog-index.v2.json"}
        ) if prior_root else ["assets/catalog-index.v2.json"],
        "rollback_eligible_under_current_rights_holds":rollback_allowed,
        "rollback_blocked_product_ids":sorted(rollback_blockers),
        "rollback_reason":rollback_reason,
        "candidate_file_sha256":dict(sorted(current_hashes.items())),
        "previous_file_sha256":dict(sorted(prior_hashes.items())),
        "required_external_steps":[
            "Verify actual production host and current deployed revision; this is only a local staged snapshot",
            "Confirm actual current manufacturer permissions, MAP rules, sale restrictions and owner signoff",
            "Back up the live host before any upload and verify target path permissions",
            "Upload immutable shards and approved assets, then switch catalog-index.v2.json",
            "Remove obsolete old hosted media and versioned shards; invalidate CDN/browser caches",
            "Verify live catalog search/pagination and no dealer costs, stock claims or restricted media",
            "Do not run rollback unless the old release passes CURRENT rights holds",
        ],
        "host":"unconfirmed",
        "owner_deployment_authorized":False,
        "deployment_performed":False,
        "live_site_modified":False,
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".area33-cutover-",dir=output.parent))
    try:
        for name, source in sorted(public_files.items()):
            _copy_exact_file(source,temp/"site"/Path(name))
        if rollback_allowed:
            for name, source in sorted(prior_files.items()):
                _copy_exact_file(source,temp/"rollback-site"/Path(name))
        (temp/"deployment-plan-private.json").write_bytes(_encode(manifest))
        (temp/"owner-deployment-authorization-TEMPLATE.json").write_bytes(_encode({
            "schema":"area33.catalog.private_owner_deployment_approval.v1",
            "catalog_version":index["version"],
            "expected_index_sha256":manifest["candidate_index_sha256"],
            "approved":False,
            "approved_by":"",
            "approved_on":None,
            "verified_host":"",
            "verified_current_live_revision":"",
            "note":"Template only. This script does not accept or execute live deployment.",
        }))
        (temp/"README_PRIVATE.txt").write_text(
            "PRIVATE release package: no live host, Git, GoDaddy or GitHub Pages changed.\n"
            "Public files are under site/. All reports/templates and rollback-site "
            "must stay private. Hosting and owner approval are still required.\n",
            encoding="utf-8",
        )
        temp.rename(output)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return manifest


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--private-preview",type=Path,required=True)
    p.add_argument("--approved-release",type=Path,required=True)
    p.add_argument("--rights-holds",type=Path,required=True)
    p.add_argument("--previous-approved-release",type=Path)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--stage-private-deployment",action="store_true")
    args=p.parse_args(argv)
    if not args.stage_private_deployment:
        p.error("Explicit --stage-private-deployment required; nothing goes live")
    try:
        result=stage_controlled_deployment(
            args.private_preview,args.approved_release,args.rights_holds,
            args.out,previous_release=args.previous_approved_release,
        )
    except (OSError,ValueError,KeyError,TypeError) as exc:
        p.error(str(exc))
    print("PRIVATE controlled catalog deployment package staged; NOT DEPLOYED.")
    print("  Approved catalog products:",result["candidate_approved_products"])
    print("  Added / withdrawn:",result["new_product_count"],result["withdrawn_product_count"])
    print("  Rollback with current rights holds:",result["rollback_eligible_under_current_rights_holds"])
    print("  Old host images requiring deletion:",len(result["remove_old_images_after_switch"]))
    print("  Private package:",args.out)


if __name__=="__main__":
    main()
