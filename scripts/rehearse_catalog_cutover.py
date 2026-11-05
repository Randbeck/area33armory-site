#!/usr/bin/env python3
"""Rehearse catalog cutover and rights-safe rollback in a LOCAL PRIVATE folder.

No network, hosting credentials, Git commands, servers or production writes.
The exercise validates the staged plan, upload order, old-asset cleanup and
rollback only when the original catalog passes the current rights-hold gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from prepare_approved_catalog_shards import _private_destination, _encode
from plan_controlled_catalog_deployment import _site_files


class CutoverRehearsalError(ValueError):
    pass


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_snapshot(site: Path, hashes: dict) -> None:
    actual = _site_files(site)
    if set(actual) != set(hashes):
        raise CutoverRehearsalError("Mock-host asset list differs from signed preflight manifest")
    for name, path in actual.items():
        if _sha(path) != hashes[name]:
            raise CutoverRehearsalError("Mock-host asset differs from reviewed release hash")


def rehearse_private_cutover(package_root: Path, output: Path):
    package_root=Path(package_root).expanduser().resolve()
    output=_private_destination(Path(output))
    if output.is_relative_to(package_root) or package_root.is_relative_to(output):
        raise CutoverRehearsalError("Local rehearsal may not overwrite release package")
    if any((p/".git").exists() for p in (package_root,*package_root.parents)):
        raise CutoverRehearsalError("Private package must remain outside Git")
    manifest=package_root/"deployment-plan-private.json"
    if manifest.is_symlink() or not manifest.is_file():
        raise CutoverRehearsalError("Private deployment plan not found")
    plan=json.loads(manifest.read_text(encoding="utf-8"))
    if (plan.get("schema")!="area33.catalog.private_controlled_release.v1"
            or plan.get("owner_deployment_authorized") is not False
            or plan.get("deployment_performed") is not False
            or plan.get("live_site_modified") is not False):
        raise CutoverRehearsalError("Only an unpublished, private plan may be rehearsed")
    expected=plan.get("candidate_file_sha256")
    old_expected=plan.get("previous_file_sha256")
    if not isinstance(expected,dict) or not isinstance(old_expected,dict):
        raise CutoverRehearsalError("Release plan missing asset hashes")
    files=_site_files(package_root/"site")
    if not expected or set(files)!=set(expected):
        raise CutoverRehearsalError("Private deployment plan has untracked public assets")
    for name,path in files.items():
        if _sha(path)!=expected[name]:
            raise CutoverRehearsalError("Release package asset tampered after preflight")
    rollback=plan.get("rollback_eligible_under_current_rights_holds") is True
    rolled_files={}
    if rollback:
        rolled_files=_site_files(package_root/"rollback-site")
        if not old_expected or set(rolled_files)!=set(old_expected):
            raise CutoverRehearsalError("Rollback package no longer matches previous release")
        for name,path in rolled_files.items():
            if _sha(path)!=old_expected[name]:
                raise CutoverRehearsalError("Previous approved release rollback bytes changed")
    elif (package_root/"rollback-site").exists():
        raise CutoverRehearsalError("Blocked rollback files should not be included")
    activation=plan.get("activate_index_last")
    immutable=plan.get("upload_immutable_first")
    if (activation!="assets/catalog-index.v2.json" or
            not isinstance(immutable,list) or len(immutable)!=len(set(immutable)) or
            any(v not in files or v==activation for v in immutable)):
        raise CutoverRehearsalError("Deployment sequence is unsafe or incomplete")
    output.parent.mkdir(parents=True,exist_ok=True)
    temp=Path(tempfile.mkdtemp(prefix=".area33-cutover-test-",dir=output.parent))
    try:
        mock=temp/"mock-host"
        if rollback:
            for name,path in rolled_files.items():
                target=mock.joinpath(*Path(name).parts)
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(path,target)
            _assert_snapshot(mock,old_expected)
        # Phase 1: prepare versioned shards and new approved images.
        for name in immutable:
            target=mock.joinpath(*Path(name).parts)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(files[name],target)
        # Phase 2: update other reviewed website assets, but hold back index.
        for name,path in files.items():
            if name==activation or name in immutable:
                continue
            target=mock.joinpath(*Path(name).parts)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,target)
        # Phase 3: index activation LAST.
        target=mock.joinpath(*Path(activation).parts)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(files[activation],target)
        # Phase 4: prune removed versioned shard and disallowed image URLs.
        for name in sorted(set(_site_files(mock))-set(expected)):
            (mock/Path(name)).unlink()
        _assert_snapshot(mock,expected)
        rollback_rehearsed=False
        if rollback:
            for name,path in rolled_files.items():
                target=mock.joinpath(*Path(name).parts)
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(path,target)
            for name in sorted(set(_site_files(mock))-set(old_expected)):
                (mock/Path(name)).unlink()
            _assert_snapshot(mock,old_expected)
            rollback_rehearsed=True
        audit={
            "schema":"area33.catalog.private_cutover_rehearsal.v1",
            "catalog_version":plan["catalog_version"],
            "approved_product_count":plan["candidate_approved_products"],
            "rights_holds_sha256":plan["rights_holds_sha256"],
            "candidate_file_count":len(expected),
            "activation_index_last_verified":True,
            "old_media_removal_simulated":True,
            "rollback_rehearsed":rollback_rehearsed,
            "rollback_allowed":rollback,
            "real_host_reached":False,
            "live_site_modified":False,
            "notes":"PRIVATE simulation only; actual host, CDN/old image removal and owner publication approval remain external.",
        }
        (temp/"private-rehearsal-audit.json").write_bytes(_encode(audit))
        temp.rename(output)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return audit


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--private-release-package",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--rehearse-local-only",action="store_true")
    args=p.parse_args(argv)
    if not args.rehearse_local_only:
        p.error("Explicit --rehearse-local-only required")
    try:
        audit=rehearse_private_cutover(args.private_release_package,args.out)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        p.error(str(exc))
    print("PRIVATE release cutover rehearsal complete; NO deployment.")
    print("  Index activated last:",audit["activation_index_last_verified"])
    print("  Safe rollback rehearsed:",audit["rollback_rehearsed"])
    print("  Website changed:",audit["live_site_modified"])
    print("  Private results:",args.out)


if __name__=="__main__":
    main()
