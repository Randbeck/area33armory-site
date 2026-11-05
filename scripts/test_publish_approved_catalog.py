"""Private-to-public catalog gate tests; all fixtures are synthetic and local."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from publish_approved_catalog import (
    CatalogPublicationError, build, publish,
)
from prepare_catalog_candidates import prepare, DraftError


class CatalogApprovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp.name)
        self.media = self.dir / "media"
        self.media.mkdir()
        self.sku = "17912WH-1-SBL-R"
        (self.media / self.sku).mkdir()
        self.photo = self.media / self.sku / (self.sku + "_1.jpg")
        Image.new("RGB", (400, 250), (240, 240, 240)).save(self.photo, "JPEG")
        self.sha = hashlib.sha256(self.photo.read_bytes()).hexdigest()
        self.handoff = self.dir / "area33-private-candidates.json"
        self.handoff.write_text(json.dumps({
            "schema": "randbeck.area33_private_handoff.v1",
            "publication_enabled": False,
            "items": [{
                "source_sku": self.sku, "manufacturer": "1791 Gunleather",
                "model": "2-Way Holster", "public_export_allowed": False,
                "frames": [{
                    "source_filename": self.photo.name,
                    "source_private_relative_path": self.sku + "/" + self.photo.name,
                    "sha256": self.sha,
                }],
            }],
        }))
        self.out = self.dir / "approvals"
        self.template = prepare(self.handoff, self.media, self.out)
        self.records = json.loads(self.template.read_text())
        self.original_draft = json.loads(self.template.read_text())
        self.approved = self.records[0]
        self.approved.update({
            "description": "Manufacturer-described synthetic sample; owner-reviewed.",
            "status": "published", "category": "Holsters",
            "product_type": "accessory", "rights_source": "RSR dealer permitted sale display",
            "identity_evidence_label": "RSR approved item verified",
            "source_checked_at": "2026-11-04",
        })
        self.approved["photos"][0]["alt"] = "Black holster product photograph"
        for key in self.approved["approvals"]:
            self.approved["approvals"][key] = True
        self.write()
        self.site = self.dir / "site"
        self.site.mkdir()
        self.assets = self.site / "assets" / "approved" / "catalog"
        self.manifest = self.site / "assets" / "catalog-public.json"
        self.manifest.parent.mkdir()
        self.manifest.write_text(json.dumps({
            "schema": "area33.catalog.public.v1", "items": [],
        }))

    def tearDown(self):
        self.temp.cleanup()

    def write(self):
        self.template.write_text(json.dumps(self.records))

    def build(self):
        with patch("publish_approved_catalog.ROOT", self.site):
            return build(self.template)

    def publish(self, do_publish=True):
        with patch("publish_approved_catalog.ROOT", self.site), patch(
            "publish_approved_catalog.ASSET_ROOT", self.assets
        ), patch("publish_approved_catalog.MANIFEST", self.manifest):
            return publish(self.template, do_publish=do_publish)

    def test_draft_defaults_all_false(self):
        draft = self.original_draft[0]
        self.assertEqual(draft["status"], "draft")
        self.assertTrue(all(value is False for value in draft["approvals"].values()))
        self.assertEqual(draft["product_type"], "")
        self.assertEqual(draft["rights_source"], "")
        self.assertEqual(draft["photos"][0]["alt"], "")
        self.assertIn("photos", draft)

    def test_private_approval_file_contains_no_public_media(self):
        self.assertTrue(self.template.exists())
        self.assertFalse((self.out / "assets").exists())
        with self.assertRaises(DraftError):
            prepare(self.handoff, self.media, self.out)

    def test_fully_approved_static_public_fields_only(self):
        payload, photos = self.build()
        self.assertEqual(payload["schema"], "area33.catalog.public.v1")
        self.assertEqual(len(photos), 1)
        public = json.dumps(payload)
        for private_value in (self.sku, self.sha, str(self.photo), "source_sha256",
                              "source_path", "source_sku", "dealer_cost"):
            self.assertNotIn(private_value, public)
        self.assertIn("Holsters", public)
        self.assertIn("Manufacturer-described synthetic sample; owner-reviewed.", public)
        self.assertIn("assets/approved/catalog/", public)

    def test_requires_all_independent_approvals_and_sale_scope(self):
        for key in list(self.approved["approvals"]):
            self.approved["approvals"][key] = False
            self.write()
            with self.assertRaises(CatalogPublicationError):
                self.build()
            self.approved["approvals"][key] = True
        self.write()

    def test_refuse_draft_and_unapproved_image_reuse(self):
        self.approved["status"] = "draft"
        self.write()
        with self.assertRaises(CatalogPublicationError):
            self.build()

    def test_changed_jpeg_is_refused(self):
        self.photo.write_bytes(b"\xff\xd8\xfftampered")
        with self.assertRaises(CatalogPublicationError):
            self.build()

    def test_low_resolution_is_refused(self):
        Image.new("RGB", (180, 120), (255, 255, 255)).save(self.photo, "JPEG")
        self.approved["photos"][0]["source_sha256"] = hashlib.sha256(
            self.photo.read_bytes()).hexdigest()
        self.write()
        with self.assertRaises(CatalogPublicationError):
            self.build()

    def test_publisher_copies_original_bytes_and_does_not_checkout(self):
        payload = self.publish()
        path = self.site / payload["items"][0]["images"][0]["url"]
        self.assertTrue(path.is_file())
        self.assertEqual(path.read_bytes(), self.photo.read_bytes())
        self.assertEqual(len(json.loads(self.manifest.read_text())["items"]), 1)
        with self.assertRaises(CatalogPublicationError):
            self.publish()

    def test_false_publication_flag_not_upgraded(self):
        self.assertFalse(self.approved["photos"][0].get("rights", False))
        self.assertIn("offered_for_sale", self.approved["approvals"])

    def test_rsr_handoff_sha_mismatch_prevents_draft(self):
        bad = self.dir / "changed.json"
        packet = json.loads(self.handoff.read_text())
        packet["items"][0]["frames"][0]["sha256"] = "0" * 64
        bad.write_text(json.dumps(packet))
        with self.assertRaises(DraftError):
            prepare(bad, self.media, self.dir / "new-approvals")


if __name__ == "__main__":
    unittest.main()
