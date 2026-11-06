#!/usr/bin/env python3
"""Build a PRIVATE Github Pages candidate from an independently approved catalog.

GitHub Pages publishes a WHOLE static artifact, not file-by-file uploads.
Prepare an exact, privacy-limited public site/ folder with public integrity
manifest; place PRIVATE receipts outside it. Nothing is committed or deployed.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from catalog_release_safety import read_rights_holds,reject_held_products
from prepare_approved_catalog_shards import _private_destination,_encode
from stage_private_media_withdrawal import _approved_previous
from stage_private_catalog_site_preview import STATIC
from plan_controlled_catalog_deployment import _site_files,ControlledReleaseError

DOMAIN="area33armory.com"
PUBLIC_MANIFEST="pages-release-public.json"
PUBLIC_SCHEMA="area33.pages.public_candidate.v1"
PRIVATE_SCHEMA="area33.pages.private_candidate_receipt.v1"
MAX_PUBLIC_FILES=200000


class PagesCandidateError(ValueError):
    pass


def _digest(path: Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_github_pages_candidate(
    package:Path,approved_release:Path,rights_holds:Path,output:Path,
    *,previous_approved_release:Path|None=None
):
    package=Path(package).expanduser().resolve()
    approved_release=Path(approved_release).expanduser().resolve()
    output=_private_destination(Path(output))
    if any(output.is_relative_to(path) or path.is_relative_to(output)
           for path in (package,approved_release)):
        raise PagesCandidateError("Candidate folder must not contain private source folders")
    plan_path=package/"deployment-plan-private.json"
    if plan_path.is_symlink() or not plan_path.is_file():
        raise PagesCandidateError("Private controlled release plan missing")
    plan=json.loads(plan_path.read_text(encoding="utf-8"))
    if (plan.get("schema")!="area33.catalog.private_controlled_release.v1" or
        plan.get("host")!="unconfirmed" or
        plan.get("owner_deployment_authorized") is not False or
        plan.get("deployment_performed") is not False or
        plan.get("live_site_modified") is not False):
        raise PagesCandidateError("Expected an unpublished, private controlled release")
    holds=read_rights_holds(rights_holds)
    if holds["sha256"] != plan.get("rights_holds_sha256"):
        raise PagesCandidateError("Rights holds changed: repeat controlled preflight")
    index,products,provenance,media=_approved_previous(approved_release)
    reject_held_products(products,provenance,holds)
    if (plan.get("catalog_version")!=index["version"] or
        plan.get("candidate_approved_products")!=len(products) or
        plan.get("candidate_index_sha256")!=
            _digest(approved_release/"assets/catalog-index.v2.json")):
        raise PagesCandidateError("Approved release differs from controlled plan")
    if plan.get("previous_version") is not None:
        if previous_approved_release is None:
            raise PagesCandidateError("Previous approved release required for a replacement candidate")
        prior_index,old_products,old_provenance,old_images=_approved_previous(
            Path(previous_approved_release)
        )
        if prior_index["version"]!=plan["previous_version"]:
            raise PagesCandidateError("Reviewed previous release is not the planned predecessor")
        if bool(plan.get("rollback_eligible_under_current_rights_holds")):
            reject_held_products(old_products,old_provenance,holds)
    elif previous_approved_release is not None:
        raise PagesCandidateError("Unexpected previous release supplied to first publication")
    files=_site_files(package/"site")
    expected_paths=set(STATIC)|{"assets/catalog-index.v2.json"}|{
        x["url"] for x in index["shards"]
    }|set(media)
    if set(files)!=expected_paths or len(files)>MAX_PUBLIC_FILES:
        raise PagesCandidateError("Controlled package has a missing or unexpected public file")
    planned=plan.get("candidate_file_sha256")
    if not isinstance(planned,dict) or set(planned)!=set(files):
        raise PagesCandidateError("Private release plan does not cover exact public files")
    for name,path in files.items():
        if _digest(path)!=planned[name]:
            raise PagesCandidateError("Public artifact differs from controlled approval plan")
    original=approved_release/"assets/catalog-index.v2.json"
    if _digest(files["assets/catalog-index.v2.json"])!=_digest(original):
        raise PagesCandidateError("Public index does not match approved private release")
    for name in ("CNAME",".nojekyll",PUBLIC_MANIFEST):
        if name in files:
            raise PagesCandidateError("Uncontrolled GitHub Pages control or manifest file")

    public={
        "schema":PUBLIC_SCHEMA,
        "domain":DOMAIN,
        "catalog_version":index["version"],
        "index_sha256":_digest(original),
        "approved_product_count":len(products),
        "file_sha256":dict(sorted(planned.items())),
        "note":"Only approved public files. Not live distributor inventory, price or stock.",
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    temp=Path(tempfile.mkdtemp(prefix=".area33-pages-",dir=output.parent))
    try:
        site=temp/"site"
        for name,path in sorted(files.items()):
            dest=site.joinpath(*Path(name).parts)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,dest)
            if _digest(path)!=_digest(dest):
                raise PagesCandidateError("Copy of approved public file changed")
        (site/"CNAME").write_text(DOMAIN+"\n",encoding="ascii")
        (site/".nojekyll").write_bytes(b"")
        (site/PUBLIC_MANIFEST).write_bytes(_encode(public))
        receipt={
            "schema":PRIVATE_SCHEMA,
            "created_at":datetime.now(timezone.utc).isoformat(),
            "catalog_version":index["version"],
            "domain":DOMAIN,
            "public_manifest_sha256":_digest(site/PUBLIC_MANIFEST),
            "public_index_sha256":public["index_sha256"],
            "approved_product_count":len(products),
            "public_file_count":len(files)+3,
            "rights_holds_sha256":holds["sha256"],
            "controlled_plan_sha256":_digest(plan_path),
            "not_committed":True,
            "not_published":True,
            "human_approval_required":True,
        }
        (temp/"private-pages-candidate-receipt.json").write_bytes(_encode(receipt))
        (temp/"README_PRIVATE.txt").write_text(
            "PRIVATE GitHub Pages candidate. SITE/ IS PUBLIC IF COMMITTED.\n"
            "Do NOT commit or publish until each public record is authorized and "
            "the owner approves. Keep receipt and source release PRIVATE.\n"
            "GitHub Pages source must explicitly be switched from branch publication "
            "to GitHub Actions before first manual deployment.\n",
            encoding="utf-8",
        )
        temp.rename(output)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return receipt


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-deployment-package",required=True,type=Path)
    parser.add_argument("--approved-release",required=True,type=Path)
    parser.add_argument("--previous-approved-release",type=Path)
    parser.add_argument("--rights-holds",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--prepare-private-pages-candidate",action="store_true")
    args=parser.parse_args(argv)
    if not args.prepare_private_pages_candidate:
        parser.error("Explicit --prepare-private-pages-candidate required")
    try:
        result=prepare_github_pages_candidate(
            args.private_deployment_package,args.approved_release,args.rights_holds,
            args.out,previous_approved_release=args.previous_approved_release,
        )
    except (ValueError,OSError,KeyError,TypeError) as exc:
        parser.error(str(exc))
    print("PRIVATE GitHub Pages candidate created. NO website changes.")
    print("  Domain:",result["domain"])
    print("  Owner-approved records:",result["approved_product_count"])
    print("  Public manifest SHA-256:",result["public_manifest_sha256"])
    print("  Approved public index SHA-256:",result["public_index_sha256"])
    print("  Candidate:",args.out)
    print("  Do not commit/publicize without separate approval.")


if __name__=="__main__":
    main()
