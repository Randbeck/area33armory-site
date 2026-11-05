"""Private catalog media provenance and removal-only rights withdrawal tests."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from prepare_approved_catalog_shards import prepare_private_release
from stage_private_media_withdrawal import (
    PrivateWithdrawalError,stage_media_withdrawal,
)

DAY="2026-11-05"


class PrivateRightsWithdrawalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.img1=self.root/"image-a.jpg"
        self.img2=self.root/"image-b.jpg"
        Image.new("RGB",(400,250),(240,240,240)).save(self.img1,"JPEG")
        Image.new("RGB",(400,250),(20,20,20)).save(self.img2,"JPEG")
        self.sha1=hashlib.sha256(self.img1.read_bytes()).hexdigest()
        self.sha2=hashlib.sha256(self.img2.read_bytes()).hexdigest()
        self.records=[
            self.record(1,manufacturer="Brand A",photo=self.img1), 
            self.record(2,manufacturer="Brand A",photo=self.img1), 
            self.record(3,manufacturer="Brand B",photo=self.img1), 
            self.record(4,manufacturer="Brand B",photo=self.img2),
            self.record(5,manufacturer="Brand A",photo=None),
        ]
        self.bundle=self.root/"approved-private.json"
        self.bundle.write_text(json.dumps(self.records),encoding="utf-8")
        self.previous=self.root/"original-private-release"
        self.audit,self.index=prepare_private_release([self.bundle],self.previous)
        self.before=(self.previous/"assets/catalog-index.v2.json").read_bytes()
        self.manifest=Path(__file__).resolve().parents[1]/"assets/catalog-public.json"
        self.site_before=self.manifest.read_bytes()

    def tearDown(self):
        self.tmp.cleanup()

    def record(self,n,*,manufacturer,photo):
        is_image=photo is not None
        return {
            "id":"catalog_"+f"{n:020x}",
            "status":"published","listing_mode":"image" if is_image else "text_only",
            "content_origin":"source_review_pending" if is_image else "owner_written",
            "manufacturer":manufacturer,"model":"Exact Model "+str(n),
            "variant":"","description":"Owner-reviewed synthetic product "+str(n),
            "category":"Holsters","product_type":"accessory",
            "rights_source":"Synthetic licensed rights evidence" if is_image else "",
            "identity_evidence_label":"Exact product verified in synthetic review",
            "source_checked_at":DAY,
            "photos":[{
                "angle":"view-01","source_path":str(photo),
                "source_sha256":hashlib.sha256(photo.read_bytes()).hexdigest(),
                "alt":"Authorized synthetic sample photo "+str(n),
            }] if is_image else [],
            "approvals":{
                "owner_publication":True,"exact_identity":True,
                "media_rights":is_image,
                "content_review":True,"offered_for_sale":True,
            },
            "dealer_cost":"DO_NOT_PUBLISH_COST",
        }

    def stage(self,**kwargs):
        return stage_media_withdrawal(
            self.previous,self.root/"private-withdrawal",
            reviewer="Independent shop owner",
            reason="Synthetic rights holder has withdrawn photo usage",
            reviewed_on=DAY,**kwargs,
        )

    def test_release_provenance_is_private_and_hash_bound(self):
        provenance=json.loads((
            self.previous/"catalog-private-media-provenance.json"
        ).read_text())
        self.assertEqual(provenance["public_catalog_record_count"],5)
        entries={x["id"]:x for x in provenance["records"]}
        self.assertEqual(entries[self.records[0]["id"]]["images"][0]["original_sha256"],self.sha1)
        self.assertEqual(entries[self.records[2]["id"]]["images"][0]["original_sha256"],self.sha1)
        self.assertEqual(entries[self.records[3]["id"]]["images"][0]["original_sha256"],self.sha2)
        self.assertEqual(entries[self.records[4]["id"]]["images"],[])
        public=(self.previous/"assets/catalog-index.v2.json").read_text()
        self.assertNotIn(self.sha1,public)
        self.assertNotIn("Synthetic licensed rights evidence",public)
        self.assertNotIn("DO_NOT_PUBLISH_COST",public)

    def test_specific_image_hash_removes_all_brand_uses_not_text_only(self):
        audit,index=self.stage(image_sha256=self.sha1)
        self.assertEqual(audit["affected_product_count"],3)
        self.assertEqual(index["total"],2)
        self.assertEqual({p["id"] for p in index["products"]},{
            self.records[3]["id"],self.records[4]["id"],
        })
        self.assertEqual(index["shards"][0]["count"],2)
        withdrawal=json.loads((
            self.root/"private-withdrawal/catalog-private-withdrawals.json"
        ).read_text())
        self.assertEqual({r["id"] for r in withdrawal["items"]},{
            self.records[0]["id"],self.records[1]["id"],self.records[2]["id"],
        })
        self.assertTrue(all(r["reason"]==audit["reason"] for r in withdrawal["items"]))
        # The remaining Brand B image is still intact, unchanged.
        target=self.root/"private-withdrawal/assets/approved/catalog"/self.records[3]["id"]/"view-01.jpg"
        self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(),self.sha2)
        for removed in self.records[:3]:
            self.assertFalse((
                self.root/"private-withdrawal/assets/approved/catalog"/removed["id"]
            ).exists())
        self.assertFalse(audit["deployment_performed"])
        self.assertFalse(audit["site_changed"])
        self.assertEqual(self.manifest.read_bytes(),self.site_before)
        self.assertEqual((
            self.previous/"assets/catalog-index.v2.json"
        ).read_bytes(),self.before)

    def test_brand_rights_issue_only_removes_that_brands_photo_listings(self):
        audit,index=self.stage(manufacturer="brand a")
        self.assertEqual(audit["affected_product_count"],2)
        self.assertEqual(index["total"],3)
        self.assertIn(self.records[4]["id"],{p["id"] for p in index["products"]})
        retained=json.loads((
            self.root/"private-withdrawal/catalog-private-media-provenance.json"
        ).read_text())
        self.assertEqual(retained["public_catalog_record_count"],3)

    def test_explicit_brand_sale_restriction_can_remove_text_only_too(self):
        audit,index=self.stage(manufacturer="Brand A",include_text_only=True)
        self.assertEqual(audit["affected_product_count"],3)
        self.assertEqual(index["total"],2)
        self.assertNotIn(self.records[4]["id"],{p["id"] for p in index["products"]})

    def test_missing_or_tampered_provenance_fails_closed(self):
        ledger=self.previous/"catalog-private-media-provenance.json"
        ledger.unlink()
        with self.assertRaises(PrivateWithdrawalError):
            self.stage(manufacturer="Brand A")
        self.assertFalse((self.root/"private-withdrawal").exists())

    def test_tampered_shard_fails_closed(self):
        shard=self.previous/self.index["shards"][0]["url"]
        shard.write_bytes(shard.read_bytes()+b"\n")
        with self.assertRaises(PrivateWithdrawalError):
            self.stage(manufacturer="Brand A")

    def test_tampered_original_approved_photo_fails_closed(self):
        path=self.previous/"assets/approved/catalog"/self.records[0]["id"]/"view-01.jpg"
        path.write_bytes(path.read_bytes()+b"corrupted")
        with self.assertRaises(PrivateWithdrawalError):
            self.stage(manufacturer="Brand A")

    def test_no_matching_brand_or_sha_will_not_stage(self):
        with self.assertRaises(PrivateWithdrawalError):
            self.stage(manufacturer="Unknown Maker")
        with self.assertRaises(PrivateWithdrawalError):
            self.stage(image_sha256="0"*64)
        self.assertFalse((self.root/"private-withdrawal").exists())

    def test_bad_review_inputs_fail(self):
        with self.assertRaises(PrivateWithdrawalError):
            stage_media_withdrawal(self.previous,self.root/"private-withdrawal",
                                   manufacturer="Brand A",image_sha256=self.sha1,
                                   reviewer="Owner",reason="Revoked rights",
                                   reviewed_on=DAY)
        with self.assertRaises(PrivateWithdrawalError):
            stage_media_withdrawal(self.previous,self.root/"private-withdrawal",
                                   manufacturer="Brand A",reviewer="Owner",
                                   reason="Revoked rights",reviewed_on="2036-01-01")

    def test_new_release_can_be_rights_withdrawn_again(self):
        audit,first=self.stage(manufacturer="Brand A")
        next_out=self.root/"second-private-withdrawal"
        second_audit,second=stage_media_withdrawal(
            self.root/"private-withdrawal",next_out,
            image_sha256=self.sha2,reviewer="Independent shop owner",
            reason="Independent rights review of second image",reviewed_on=DAY,
        )
        self.assertEqual(second_audit["affected_product_count"],1)
        self.assertEqual(second["total"],2)
        self.assertIn(self.records[4]["id"],{p["id"] for p in second["products"]})
        self.assertFalse(second_audit["deployment_performed"])


if __name__=="__main__":
    unittest.main()
