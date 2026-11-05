"""Safety tests for independent text-only, owner-written Area 33 product listings."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from import_randbeck_staging import BridgeError, build as intake, write_private_bridge
from build_private_catalog_review import validate_source, make_review, ReviewError
from publish_approved_catalog import build as publish_check, CatalogPublicationError
from prepare_approved_catalog_shards import prepare_private_release

EXACT_ID = "catalog_0123456789abcdefabcd"


class TextFirstCatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.draft = self.root/"private-catalog-approval.json"
        self.sample = {
            "id": EXACT_ID,
            "status": "draft",
            "listing_mode": "text_only",
            "content_origin": "",
            "manufacturer": "Example Brand",
            "model": "Model One",
            "variant": "",
            "description": "",
            "category": "Holsters",
            "product_type": "accessory",
            "rights_source": "",
            "identity_evidence_label": "",
            "source_checked_at": "",
            "photos": [],
            "approvals": {
                "owner_publication": False,
                "exact_identity": False,
                "media_rights": False,
                "content_review": False,
                "offered_for_sale": False,
            },
            "dealer_cost": "PRIVATE_COST_12345",
        }
        self.write()
    def tearDown(self):
        self.tmp.cleanup()
    def write(self):
        self.draft.write_text(json.dumps([self.sample]),encoding="utf-8")

    def approved(self):
        self.sample["status"]="published"
        self.sample["content_origin"]="owner_written"
        self.sample["description"]="Original owner-written product details."
        self.sample["identity_evidence_label"]="Verified exact manufacturer and MPN in local record"
        self.sample["source_checked_at"]="2026-11-04"
        for check in ("owner_publication","exact_identity","content_review","offered_for_sale"):
            self.sample["approvals"][check]=True
        self.write()

    def test_private_text_only_owner_review_needs_no_photo_or_image_rights(self):
        rows, photos=validate_source(self.draft)
        self.assertEqual(len(rows),1)
        self.assertEqual(photos,[[]])
        page=make_review(self.draft)
        html=page.read_text(encoding="utf-8")
        self.assertIn("write your own description",html)
        self.assertIn("Owner-written and verified",html)
        self.assertIn('item.approvals.media_rights===false',html)
        self.assertIn("Nothing is published here",html)

    def test_text_only_explicit_review_allows_zero_media_files(self):
        self.approved()
        public, frames=publish_check(self.draft)
        self.assertEqual(frames,[])
        self.assertEqual(len(public["items"]),1)
        result=public["items"][0]
        self.assertEqual(result["presentation_mode"],"text_only")
        self.assertEqual(result["images"],[])
        self.assertEqual(result["description"],"Original owner-written product details.")
        text=json.dumps(public)
        self.assertNotIn("PRIVATE_COST_12345",text)
        self.assertNotIn("dealer_cost",text)
        self.assertNotIn("RSR",text)
        # Private only; scalable release has no source photos to copy.
        out=self.root/"private-text-first-release"
        audit,index=prepare_private_release([self.draft],out)
        self.assertEqual(index["total"],1)
        self.assertEqual(audit["private_source_media_file_count"],0)
        self.assertFalse(audit["published"])
        self.assertFalse((self.root/"assets/catalog-index.v2.json").exists())

    def test_unapproved_text_only_and_unapproved_copy_fail_closed(self):
        with self.assertRaises(CatalogPublicationError):
            publish_check(self.draft)
        self.approved()
        for key,bad in [
            ("content_origin","source_copied"),
            ("content_origin",""),
            ("listing_mode","unknown"),
            ("rights_source","RSR photo presumed licensed"),
        ]:
            original=self.sample[key]
            self.sample[key]=bad
            self.write()
            with self.assertRaises(CatalogPublicationError):
                publish_check(self.draft)
            self.sample[key]=original
        self.write()

    def test_photo_rights_cannot_be_laundered_into_text_only(self):
        self.approved()
        self.sample["approvals"]["media_rights"]=True
        self.write()
        with self.assertRaises(CatalogPublicationError):
            publish_check(self.draft)
        with self.assertRaises(ReviewError):
            validate_source(self.draft)
        self.sample["approvals"]["media_rights"]=False
        self.sample["photos"]=[{"angle":"view-01","source_path":"private.jpg",
                                "source_sha256":"a"*64,"alt":"Original image"}]
        self.write()
        with self.assertRaises(CatalogPublicationError):
            publish_check(self.draft)
        with self.assertRaises(ReviewError):
            validate_source(self.draft)

    def test_source_intake_text_only_never_copies_rsr_photo_or_description(self):
        original=self.root/"rsr-private"
        original.mkdir()
        stage=original/"area33-private-catalog-staging.json"
        source_record={
            "source_sku":"ABC-01","source_category":"Holsters & Pouches",
            "manufacturer":"Example Brand","manufacturer_part_number":"MPN-ONE",
            "model":"Model One","description":"PROTECTED_SOURCE_MARKETING_COPY",
            "upc":"816161020234","publication_approved":False,
            "media_rights_approved":False,"source_offer_verified":False,
            "blockers":["source_image_rights_unapproved",
                        "source_exif_requires_review_before_any_public_export"],
            "source_media":[{
                "thumbnail_resolution_candidate":True,"exif_present":True,
                "sha256":"a"*64,"private_relative_file":"media/ABC-01/unavailable.jpg",
                "width":2000,"height":2000,
            }],
        }
        stage.write_text(json.dumps({
            "schema":"randbeck.area33.private_catalog_staging.v1",
            "source":"RSR","publication_enabled":False,
            "media_rights_approved":False,"source_offer_verified":False,
            "products_staged":1,"items":[source_record]
        }),encoding="utf-8")
        rows,report=intake(stage,original,bytes(range(32)),text_only_drafts=True)
        self.assertEqual(report["text_only_owner_review_drafts"],1)
        self.assertEqual(report["private_metadata_only_derivative_files"],0)
        self.assertEqual(report["groups_held_for_photo_metadata_review"],0)
        item=rows[0]
        self.assertEqual(item["listing_mode"],"text_only")
        self.assertEqual(item["content_origin"],"")
        self.assertEqual(item["description"],"")
        self.assertEqual(item["photos"],[])
        self.assertEqual(item["rights_source"],"")
        self.assertTrue(all(v is False for v in item["approvals"].values()))
        self.assertNotIn("PROTECTED_SOURCE_MARKETING_COPY",json.dumps(rows))
        out=self.root/"private-intake"
        report=write_private_bridge(stage,original,out,self.root/"private-id-key.bin",
                                   text_only_drafts=True)
        self.assertEqual(report["review_drafts_generated"],1)
        self.assertFalse((out/"private-exif-copies").exists())
        self.assertEqual(json.loads(
            (out/"catalog-approval-template-part-001.json").read_text()
        )[0]["photos"],[])
        with self.assertRaises(BridgeError):
            write_private_bridge(
                stage,original,self.root/"new-output",
                self.root/"private-id-key.bin",
                text_only_drafts=True,prepare_private_derivatives=True,
            )


if __name__=="__main__":
    unittest.main()
