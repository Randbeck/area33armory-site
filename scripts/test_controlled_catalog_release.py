"""Synthetic, fully approved catalog refresh + controlled cutover rehearsal.

Never connects to the live website or supplier. All images are generated
inside temporary test folders; rights holds are denial-only.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from catalog_release_safety import (
    CatalogRightsHoldError, read_rights_holds,
)
from prepare_approved_catalog_shards import prepare_private_release
from refresh_approved_catalog_snapshot import (
    CatalogRefreshError, refresh_approved_catalog,
)
from stage_private_catalog_site_preview import (
    SITE, ReleasePreflightError, prepare_private_website_preview,
)
from plan_controlled_catalog_deployment import (
    ControlledReleaseError, stage_controlled_deployment,
)
from rehearse_catalog_cutover import (
    CutoverRehearsalError, rehearse_private_cutover,
)


class ControlledCatalogReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.a=self.root/"approved-one.jpg"
        self.b=self.root/"approved-two.jpg"
        Image.new("RGB",(420,280),(240,240,240)).save(self.a,"JPEG")
        Image.new("RGB",(420,280),(25,25,25)).save(self.b,"JPEG")
        self.ha=hashlib.sha256(self.a.read_bytes()).hexdigest()
        self.hb=hashlib.sha256(self.b.read_bytes()).hexdigest()
        self.records=[
            self.record(1,"Sample Manufacturer",self.a),
            self.record(2,"Sample Manufacturer",None),
            self.record(3,"Different Manufacturer",None),
        ]
        self.private=self.root/"private-approved-bundles.json"
        self.write_bundle(self.records,self.private)
        self.base=self.root/"previous-owner-approved-release"
        prepare_private_release([self.private],self.base)
        self.holds=self.root/"private-rights-holds.json"
        self.make_holds([])
        self.candidate=self.root/"refreshed-catalog"
        self.preview=self.root/"local-web-preview"
        self.package=self.root/"controlled-deployment-package"
        self.site_initial=(SITE/"assets/catalog-public.json").read_bytes()

    def tearDown(self):
        self.tmp.cleanup()

    def record(self,n,manufacturer,photo,*,description=None):
        image=photo is not None
        return {
            "id":"catalog_"+format(n,"020x"),"status":"published",
            "listing_mode":"image" if image else "text_only",
            "content_origin":"source_review_pending" if image else "owner_written",
            "manufacturer":manufacturer,"model":"Model "+str(n),"variant":"",
            "description":description or "Separately owner-written product "+str(n),
            "category":"Holsters","product_type":"accessory",
            "rights_source":"Synthetic owner-verified image license" if image else "",
            "identity_evidence_label":"Owner-verified sample exact identity",
            "source_checked_at":"2026-11-04",
            "photos":[{
                "angle":"view-01","source_path":str(photo),
                "source_sha256":hashlib.sha256(photo.read_bytes()).hexdigest(),
                "alt":"Owner-approved synthetic product image",
            }] if image else [],
            "approvals":{
                "owner_publication":True,"exact_identity":True,
                "media_rights":image,"content_review":True,
                "offered_for_sale":True,
            },
            "private_dealer_cost":"DEALER_COST_MUST_NOT_APPEAR",
        }

    def write_bundle(self,records,path):
        path.write_text(json.dumps(records),encoding="utf-8")

    def make_holds(self,items):
        self.holds.write_text(json.dumps({
            "schema":"area33.catalog.private_rights_holds.v1",
            "reviewer":"Area 33 test owner","reviewed_on":"2026-11-05",
            "holds":items,
        }),encoding="utf-8")

    def hold(self,kind,value):
        return {
            "kind":kind,"value":value,
            "reason":"Documented rights claim under review",
            "recorded_on":"2026-11-05",
        }

    def withdraw_file(self,ident):
        file=self.root/"owner-reviewed-withdrawals.json"
        file.write_text(json.dumps({
            "schema":"area33.catalog.withdrawals.private.v1",
            "items":[{
                "id":ident,
                "reason":"Owner-reviewed rights withdrawal",
                "approved_by":"Area 33 test owner",
                "reviewed_at":"2026-11-05",
            }],
        }),encoding="utf-8")
        return file

    def refreshed(self,**kwargs):
        return refresh_approved_catalog(
            self.base,self.candidate,rights_holds_file=self.holds,**kwargs
        )

    def preflight(self):
        return prepare_private_website_preview(
            self.candidate,self.preview,previous_release_root=self.base,
        )

    def plan(self):
        return stage_controlled_deployment(
            self.preview,self.candidate,self.holds,self.package,
            previous_release=self.base,
        )

    def test_repeatable_noop_refresh_keeps_all_prior_approvals_and_hashes(self):
        prior=json.loads((self.base/"assets/catalog-index.v2.json").read_text())
        audit,index=self.refreshed()
        self.assertEqual(audit["source_approved_bundle_count"],0)
        self.assertEqual(audit["unchanged_previously_approved_records"],3)
        self.assertEqual(index["total"],3)
        self.assertEqual(index["products"],[
            {**item,"shard":0} for item in prior["products"]
        ])
        self.assertEqual(audit["previous_version"],prior["version"])
        self.assertFalse(audit["published"])
        self.assertEqual(
            (self.candidate/"assets/approved/catalog"/self.records[0]["id"]/"view-01.jpg").read_bytes(),
            self.a.read_bytes(),
        )
        report=self.preflight()
        self.assertEqual(report["approved_product_count"],3)
        self.assertEqual(report["changed_product_count"],0)
        plan=self.plan()
        self.assertEqual(plan["candidate_approved_products"],3)
        self.assertEqual(plan["withdrawn_product_count"],0)
        self.assertEqual(plan["rollback_eligible_under_current_rights_holds"],True)
        self.assertFalse(plan["deployment_performed"])
        self.assertEqual(plan["host"],"unconfirmed")
        self.assertTrue((self.package/"site/catalog.html").is_file())
        self.assertTrue((self.package/"rollback-site/assets/catalog-index.v2.json").is_file())
        approval=json.loads(
            (self.package/"owner-deployment-authorization-TEMPLATE.json").read_text()
        )
        self.assertIs(approval["approved"],False)
        self.assertEqual((SITE/"assets/catalog-public.json").read_bytes(),self.site_initial)
        self.assertFalse((SITE/"assets/catalog-index.v2.json").exists())
        rehearsal=rehearse_private_cutover(
            self.package,self.root/"private-local-cutover-rehearsal",
        )
        self.assertTrue(rehearsal["activation_index_last_verified"])
        self.assertTrue(rehearsal["rollback_rehearsed"])
        self.assertFalse(rehearsal["live_site_modified"])

    def test_new_approved_item_and_separately_reapproved_text_update(self):
        updated=self.record(2,"Sample Manufacturer",None,
                            description="New separately approved original copy")
        new=self.record(4,"Newly Approved Brand",None)
        fresh_bundle=self.root/"new-owner-approved.json"
        self.write_bundle([updated,new],fresh_bundle)
        audit,index=self.refreshed(approved_bundles=[fresh_bundle])
        self.assertEqual(audit["new_independently_approved_records"],1)
        self.assertEqual(audit["independently_reapproved_changed_records"],1)
        self.assertEqual(audit["unchanged_previously_approved_records"],2)
        self.assertEqual(index["total"],4)
        report=self.preflight()
        self.assertEqual(report["new_product_count"],1)
        self.assertEqual(report["changed_product_count"],1)
        self.assertEqual(report["withdrawn_product_count"],0)
        plan=self.plan()
        self.assertEqual(plan["new_product_count"],1)
        self.assertEqual(plan["withdrawn_product_count"],0)

    def test_unapproved_draft_rejected_without_mutating_release(self):
        invalid=self.record(20,"Sample Manufacturer",None)
        invalid["approvals"]["content_review"]=False
        bundle=self.root/"unapproved.json"
        self.write_bundle([invalid],bundle)
        with self.assertRaises(ValueError):
            self.refreshed(approved_bundles=[bundle])
        self.assertFalse(self.candidate.exists())
        self.assertEqual((SITE/"assets/catalog-public.json").read_bytes(),self.site_initial)

    def test_changed_identity_cannot_reuse_catalog_id(self):
        renamed=self.record(2,"Different Brand",None)
        bundle=self.root/"changed-identity.json"
        self.write_bundle([renamed],bundle)
        with self.assertRaisesRegex(CatalogRefreshError,"Changed exact product identity"):
            self.refreshed(approved_bundles=[bundle])

    def test_changed_photo_cannot_reuse_immutable_public_url(self):
        replacement=self.record(1,"Sample Manufacturer",self.b)
        bundle=self.root/"different-photo.json"
        self.write_bundle([replacement],bundle)
        with self.assertRaisesRegex(CatalogRefreshError,"Cannot replace media bytes"):
            self.refreshed(approved_bundles=[bundle])
        self.assertFalse(self.candidate.exists())

    def test_rights_hold_blocks_refresh_and_cannot_be_overridden_by_approval(self):
        self.make_holds([self.hold("image_sha256",self.ha)])
        with self.assertRaises(CatalogRightsHoldError):
            self.refreshed()
        bundle=self.root/"still-approved.json"
        self.write_bundle([self.record(1,"Sample Manufacturer",self.a)],bundle)
        with self.assertRaises(CatalogRightsHoldError):
            self.refreshed(approved_bundles=[bundle])

    def test_reviewed_withdrawal_produces_no_unsafe_rollback(self):
        self.make_holds([self.hold("image_sha256",self.ha)])
        reviewed=self.withdraw_file(self.records[0]["id"])
        audit,index=self.refreshed(reviewed_withdrawals=reviewed)
        self.assertEqual(index["total"],2)
        self.assertEqual(audit["approved_withdrawal_count"],1)
        report=self.preflight()
        self.assertEqual(report["withdrawn_product_count"],1)
        plan=self.plan()
        self.assertFalse(plan["rollback_eligible_under_current_rights_holds"])
        self.assertEqual(plan["rollback_blocked_product_ids"],[self.records[0]["id"]])
        self.assertEqual(len(plan["remove_old_images_after_switch"]),1)
        self.assertIn("assets/catalog-index.v2.json",
                      plan["invalidate_cdn_after_removal"])
        self.assertFalse((self.package/"rollback-site").exists())
        self.assertFalse((self.package/"site/assets/approved/catalog"/
                          self.records[0]["id"]).exists())
        self.assertEqual((SITE/"assets/catalog-public.json").read_bytes(),self.site_initial)
        rehearsal=rehearse_private_cutover(
            self.package,self.root/"private-local-cutover-rehearsal",
        )
        self.assertFalse(rehearsal["rollback_rehearsed"])
        self.assertTrue(rehearsal["old_media_removal_simulated"])

    def test_invalid_prior_withdrawal_evidence_blocks_preflight(self):
        ident=self.records[0]["id"]
        reviewed=self.withdraw_file(ident)
        self.refreshed(reviewed_withdrawals=reviewed)
        audit_path=self.candidate/"catalog-private-release-audit.json"
        audit=json.loads(audit_path.read_text())
        audit["approved_withdrawals"]=[]
        audit_path.write_text(json.dumps(audit))
        with self.assertRaises(ReleasePreflightError):
            self.preflight()
        self.assertFalse(self.preview.exists())

    def test_tampered_preview_data_blocks_deployment_package(self):
        self.refreshed()
        self.preflight()
        index=self.preview/"site/assets/catalog-index.v2.json"
        index.write_bytes(index.read_bytes()+b" ")
        with self.assertRaises(ControlledReleaseError):
            self.plan()
        self.assertFalse(self.package.exists())

    def test_rehearsal_rejects_tampered_release_assets(self):
        self.refreshed()
        self.preflight()
        self.plan()
        staged=self.package/"site/assets/catalog-index.v2.json"
        staged.write_bytes(staged.read_bytes()+b" ")
        with self.assertRaises(CutoverRehearsalError):
            rehearse_private_cutover(
                self.package,self.root/"tampered-rehearsal"
            )
        self.assertFalse((self.root/"tampered-rehearsal").exists())

    def test_rollforward_holds_rechecked_after_preview_created(self):
        self.refreshed()
        self.preflight()
        self.make_holds([self.hold("manufacturer_media","Sample Manufacturer")])
        with self.assertRaises(CatalogRightsHoldError):
            self.plan()
        self.assertFalse(self.package.exists())

    def test_explicit_brand_sale_hold_blocks_even_text_only_records(self):
        self.make_holds([self.hold("manufacturer_sales","Sample Manufacturer")])
        with self.assertRaises(CatalogRightsHoldError):
            self.refreshed()

    def test_missing_rights_ledger_fails_closed(self):
        self.holds.unlink()
        with self.assertRaises(CatalogRightsHoldError):
            self.refreshed()

    def test_no_removal_without_reviewed_withdrawal(self):
        fresh=self.record(4,"New Brand",None)
        approved=self.root/"new.json"
        self.write_bundle([fresh],approved)
        withdrawal=self.withdraw_file("catalog_"+"f"*20)
        with self.assertRaises(CatalogRefreshError):
            self.refreshed(
                approved_bundles=[approved],reviewed_withdrawals=withdrawal
            )

    def test_future_or_malformed_hold_records_fail_closed(self):
        self.make_holds([self.hold("image_sha256","not a sha")])
        with self.assertRaises(CatalogRightsHoldError):
            read_rights_holds(self.holds)
        self.make_holds([{
            "kind":"image_sha256","value":self.ha,
            "reason":"Owner case investigation",
            "recorded_on":"2099-01-01",
        }])
        with self.assertRaises(CatalogRightsHoldError):
            read_rights_holds(self.holds)


if __name__=="__main__":
    unittest.main()
