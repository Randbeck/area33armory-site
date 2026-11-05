"""Cryptographically verified, never-auto-published supplier/category policy receipt."""
from __future__ import annotations

from datetime import datetime,timedelta,timezone
from pathlib import Path
from copy import deepcopy
import hashlib
import hmac
import io
import json
import tempfile
import unittest

from PIL import Image

from import_randbeck_staging import build,write_private_bridge,BridgeError
from verify_randbeck_scope_receipt import (
    validate_scoped_receipt,ScopeReceiptError,
)


def canonical_mac(data,key):
    raw=json.dumps(data,sort_keys=True,separators=(",",":"),
                   ensure_ascii=False).encode("utf-8")
    return hmac.new(key,raw,hashlib.sha256).hexdigest()


def jpeg():
    buf=io.BytesIO()
    Image.new("RGB",(400,250),"white").save(buf,"JPEG")
    return buf.getvalue()


class ScopedImportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.photos=self.root/"private-source"
        self.photos.mkdir()
        self.sku="AAA-101"
        photo=self.photos/"media"/self.sku/(self.sku+"_1.jpg")
        photo.parent.mkdir(parents=True)
        photo.write_bytes(jpeg())
        self.photo=photo
        self.key=bytes(range(32))
        self.keypath=self.root/"key.bin"
        self.keypath.write_bytes(self.key)
        self.identitykey=self.root/"catalog-id.bin"
        self.now=datetime.now(timezone.utc)
        self.record={
            "source_sku":self.sku,"source_category":"Holsters & Pouches",
            "manufacturer":"Verified Maker","manufacturer_part_number":"M-101",
            "model":"Sample Case","upc":"816161020234",
            "description":"Source manufacturer description",
            "publication_approved":False,"media_rights_approved":False,
            "source_offer_verified":False,"blockers":[],
            "source_media":[{
                "private_relative_file":"media/AAA-101/AAA-101_1.jpg",
                "sha256":hashlib.sha256(photo.read_bytes()).hexdigest(),
                "width":400,"height":250,"exif_present":False,
                "thumbnail_resolution_candidate":True,
                "showroom_resolution_candidate":False,
                "source_tier":"standard",
            }],
        }
        self.staging=self.photos/"area33-private-catalog-staging.json"
        self.snapshot=(self.now-timedelta(hours=1)).isoformat()
        self.write_staging()
        self.evidence=self.root/"RSR-owner-held-supplier-terms.txt"
        self.evidence.write_text("Synthetic fixture - supplier grants display rights for one category")
        self.grant={
            "id":"a"*24,
            "supplier":"RSR","source_category":"Holsters & Pouches",
            "public_category":"Holsters","product_type":"accessory",
            "permissions":{
                "show_source_product_listing":True,
                "reuse_source_description":True,
                "display_original_product_photo":True,
                "display_metadata_cleared_photo":False,
            },
            "offer_mode":"inquiry_only","max_snapshot_age_hours":48,
            "excluded_upcs":[],"excluded_brands":[],
            "evidence":{
                "type":"direct_supplier_written_permission",
                "private_file":str(self.evidence),
                "sha256":hashlib.sha256(self.evidence.read_bytes()).hexdigest(),
            },
            "owner_review":{
                "reviewer":"Sample Owner",
                "approved_on":(self.now-timedelta(days=1)).date().isoformat(),
                "expires_on":(self.now+timedelta(days=30)).date().isoformat(),
                "attestation":"I reviewed the supplier terms for this exact scope",
            },
        }
        self.ledgerpath=self.root/"ledger.json"
        self.receiptpath=self.root/"signed-receipt.json"
        self.write_ledger()
        self.write_receipt()
        self.output=self.root/"private-intake"
    def tearDown(self):
        self.temp.cleanup()

    def write_staging(self):
        self.staging.write_text(json.dumps({
            "schema":"randbeck.area33.private_catalog_staging.v1",
            "source":"RSR","publication_enabled":False,
            "media_rights_approved":False,"source_offer_verified":False,
            "products_staged":1,"items":[self.record],
            "private_inventory_snapshot_modified_at":self.snapshot,
        }),encoding="utf-8")

    def write_ledger(self,revocations=None):
        unsigned={
            "schema":"randbeck.area33.catalog_scope_ledger.v1",
            "revision":1+len(revocations or []),
            "site":"area33armory.com",
            "grants":[self.grant],
            "revocations":revocations or [],
        }
        self.ledgerpath.write_text(json.dumps({
            **unsigned,"signature":canonical_mac(unsigned,self.key)
        }),encoding="utf-8")

    def write_receipt(self,*,status="policy_eligible_private_candidate",
                      blockers=None,evaluated=None):
        ledger=json.loads(self.ledgerpath.read_text())
        doc={
            "schema":"randbeck.area33.private_scope_eligibility.v1",
            "publication_enabled":False,
            "supplier_license_validated_by_platform":False,
            "ledger_revision":ledger["revision"],
            "source_snapshot_modified_at":self.snapshot,
            "evaluated_at":evaluated or self.now.isoformat(),
            "source_products":1,
            "private_policy_candidates":int(status=="policy_eligible_private_candidate"),
            "held_exceptions":int(status=="exception"),
            "reasons":{},
            "note":"Synthetic policy candidate, never publication",
            "items":[{
                "source_sku":self.sku,"source_category":"Holsters & Pouches",
                "status":status,"blocking_reasons":blockers or [],
                "grant_id":self.grant["id"],
                "proposed_public_category":"Holsters",
                "proposed_public_type":"accessory",
                "media_next_step":"verified_original_private_photo",
                "owner_publication_approved":False,
                "rights_approved_for_publication":False,
                "actual_stock_verified":False,
            }],
            "source_staging_sha256":hashlib.sha256(self.staging.read_bytes()).hexdigest(),
            "ledger_signature":ledger["signature"],
        }
        self.receiptpath.write_text(json.dumps({
            **doc,"receipt_hmac_sha256":canonical_mac(doc,self.key)
        }),encoding="utf-8")

    def verify(self,now=None):
        return validate_scoped_receipt(
            self.staging,self.receiptpath,self.ledgerpath,self.keypath,
            now=now or self.now+timedelta(minutes=1),
        )

    def test_valid_scope_receipt_imports_private_draft_without_rights_approval(self):
        valid=self.verify()
        self.assertEqual(valid["eligible_product_count"],1)
        report=write_private_bridge(
            self.staging,self.photos,self.output,self.identitykey,
            scope_receipt=self.receiptpath,
            scope_ledger=self.ledgerpath,scope_key=self.keypath,
        )
        self.assertTrue(report["scope_gate_enabled"])
        self.assertEqual(report["scope_signed_eligible_drafts"],1)
        links=report["private_scope_to_catalog_product_links"]
        self.assertEqual(len(links),1)
        self.assertEqual(links[0]["grant_id"],self.grant["id"])
        self.assertFalse(links[0]["publication_approved"])
        drafts=json.loads((self.output/"catalog-approval-template-part-001.json").read_text())
        self.assertEqual(len(drafts),1)
        self.assertEqual(drafts[0]["status"],"draft")
        self.assertEqual(drafts[0]["rights_source"],"")
        self.assertTrue(all(v is False for v in drafts[0]["approvals"].values()))
        self.assertFalse(report["publication_enabled"])

    def test_policy_held_item_produces_exception_not_owner_review_draft(self):
        self.write_receipt(status="exception",blockers=[
            "supplier_rights_evidence_changed_or_missing",
        ])
        report=write_private_bridge(
            self.staging,self.photos,self.output,self.identitykey,
            scope_receipt=self.receiptpath,scope_ledger=self.ledgerpath,scope_key=self.keypath,
        )
        self.assertEqual(report["scope_signed_eligible_drafts"],0)
        self.assertEqual(report["review_drafts_generated"],0)
        self.assertEqual(report["quarantined_identity_or_media_groups"],1)
        self.assertFalse((self.output/"catalog-approval-template-part-001.json").exists())

    def test_tampered_signed_eligibility_refused(self):
        obj=json.loads(self.receiptpath.read_text())
        obj["items"][0]["status"]="exception"
        self.receiptpath.write_text(json.dumps(obj))
        with self.assertRaises(ScopeReceiptError):
            self.verify()

    def test_changed_source_staging_refused(self):
        self.record["description"]="Changed after signing receipt"
        self.write_staging()
        with self.assertRaises(ScopeReceiptError):
            self.verify()

    def test_changed_supplier_evidence_refused(self):
        self.evidence.write_text("Terms replaced")
        with self.assertRaises(ScopeReceiptError):
            self.verify()

    def test_owner_revocation_refuses_earlier_receipt(self):
        self.write_ledger(revocations=[{
            "grant_id":self.grant["id"],
            "reviewer":"Sample Owner",
            "reason":"Revoked old supplier policy",
            "revoked_on":self.now.date().isoformat(),
        }])
        with self.assertRaises(ScopeReceiptError):
            self.verify()

    def test_signed_but_stale_receipt_is_refused(self):
        older=self.now-timedelta(hours=3)
        self.write_receipt(evaluated=older.isoformat())
        with self.assertRaises(ScopeReceiptError):
            self.verify()

    def test_source_snapshot_too_old_under_policy_refused(self):
        self.snapshot=(self.now-timedelta(days=7)).isoformat()
        self.write_staging()
        self.write_receipt()
        with self.assertRaises(ScopeReceiptError):
            self.verify()

    def test_expired_grant_is_refused_by_site_even_if_receipt_signed(self):
        self.grant["owner_review"]["expires_on"]=(self.now-timedelta(days=1)).date().isoformat()
        self.write_ledger()
        self.write_receipt()
        with self.assertRaises(ScopeReceiptError):
            self.verify()

    def test_missing_three_scope_arguments_fails_closed(self):
        with self.assertRaises(BridgeError):
            write_private_bridge(
                self.staging,self.photos,self.output,self.identitykey,
                scope_receipt=self.receiptpath,
            )

    def test_new_scope_receipt_never_overwrites_older_sources(self):
        self.verify()
        self.assertTrue(self.photo.is_file())
        self.assertFalse(self.output.exists())


if __name__=="__main__":
    unittest.main()
