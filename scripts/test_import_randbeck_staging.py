"""RSR -> Area 33 approved-only ingestion: private files and zero auto approvals."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image
from import_randbeck_staging import BridgeError, build, write_private_bridge
from build_private_catalog_review import validate_source
from publish_approved_catalog import CatalogPublicationError, build as build_public

UPC = "816161020234"


def jpeg(*, with_exif=False):
    stream = io.BytesIO()
    picture = Image.new("RGB", (900, 600), "white")
    if with_exif:
        source_metadata = Image.Exif()
        source_metadata[274] = 1  # Orientation; metadata presence itself needs review.
        picture.save(stream, "JPEG", exif=source_metadata)
    else:
        picture.save(stream, "JPEG")
    return stream.getvalue()


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.batch = self.root / "verified-batch"
        self.out = self.root / "new-site-intake"
        self.batch.mkdir()
        self.sku = "AAA-101"
        self.original = self.batch / "media" / self.sku / "AAA-101_1_HR.jpg"
        self.original.parent.mkdir(parents=True)
        self.original.write_bytes(jpeg())
        self.sha = hashlib.sha256(self.original.read_bytes()).hexdigest()
        self.item = {
            "source_sku": self.sku, "source_category": "Holsters & Pouches",
            "manufacturer": "Sample Brand", "model": "Model X",
            "manufacturer_part_number": "X-123", "upc": UPC,
            "description": "Source product details",
            "publication_approved": False, "media_rights_approved": False,
            "source_offer_verified": False, "blockers": [
                "source_policy_disabled",
                "sale_display_policy_not_approved",
                "image_rights_not_approved",
                "public_category_not_enabled",
            ],
            "source_media": [{
                "private_relative_file": "media/AAA-101/AAA-101_1_HR.jpg",
                "sha256": self.sha, "width": 900, "height": 600,
                "exif_present": False,
                "thumbnail_resolution_candidate": True,
                "showroom_resolution_candidate": True,
                "source_tier": "highres",
            }],
            # A deliberately private field that must never reach a draft.
            "private_dealer_cost": "SENSITIVE-1717",
        }
        self.payload = {
            "schema": "randbeck.area33.private_catalog_staging.v1",
            "source": "RSR",
            "publication_enabled": False, "media_rights_approved": False,
            "source_offer_verified": False,
            "products_staged": 1, "items": [self.item],
        }
        self.staging = self.batch / "area33-private-catalog-staging.json"
        self.save()
        self.secret = bytes(range(32))

    def tearDown(self):
        self.tmp.cleanup()

    def save(self):
        self.payload["products_staged"] = len(self.payload["items"])
        self.staging.write_text(json.dumps(self.payload), encoding="utf-8")

    def test_real_approval_contract_and_private_only(self):
        items, report = build(self.staging, self.batch, self.secret)
        self.assertEqual(report["source_products"], 1)
        self.assertEqual(report["exact_identity_groups"], 1)
        self.assertEqual(report["review_drafts_generated"], 1)
        self.assertEqual(report["quarantined_identity_or_media_groups"], 0)
        item = items[0]
        self.assertEqual(item["category"], "Holsters & Pouches")
        self.assertEqual(item["description"], "Source product details")
        self.assertEqual(item["product_type"], "accessory")
        self.assertEqual(item["status"], "draft")
        self.assertEqual(item["source_checked_at"], "")
        self.assertEqual(item["rights_source"], "")
        self.assertEqual(item["identity_evidence_label"], "")
        self.assertTrue(all(flag is False for flag in item["approvals"].values()))
        self.assertEqual(item["photos"][0]["source_sha256"], self.sha)
        self.assertEqual(item["photos"][0]["source_path"], str(self.original.resolve()))
        self.assertEqual(len(validate_source_of_list(self.root, items)), 1)
        text = json.dumps(items)
        self.assertNotIn("SENSITIVE-1717", text)
        self.assertNotIn("private_dealer_cost", text)
        self.assertNotIn(UPC, text)
        with self.assertRaises(CatalogPublicationError):
            publication_of_list(self.root, items)

    def test_persistent_public_identity_with_private_key(self):
        a, _ = build(self.staging, self.batch, self.secret)
        b, _ = build(self.staging, self.batch, self.secret)
        c, _ = build(self.staging, self.batch, bytes(reversed(range(32))))
        self.assertEqual(a[0]["id"], b[0]["id"])
        self.assertNotEqual(a[0]["id"], c[0]["id"])
        self.assertTrue(a[0]["id"].startswith("catalog_"))

    def test_mismatched_upc_different_parts_go_to_exception(self):
        other = deepcopy(self.item)
        other["source_sku"] = "BBB-101"
        other["manufacturer_part_number"] = "DIFFERENT"
        folder = self.batch / "media" / "BBB-101"
        folder.mkdir()
        photo = folder / "BBB-101_1_HR.jpg"
        photo.write_bytes(jpeg())
        other["source_media"][0]["private_relative_file"] = (
            "media/BBB-101/BBB-101_1_HR.jpg"
        )
        self.payload["items"].append(other)
        self.save()
        records, report = build(self.staging, self.batch, self.secret)
        self.assertEqual(records, [])
        self.assertEqual(report["quarantined_identity_or_media_groups"], 2)
        self.assertEqual(report["exception_reason_counts"]["same_gtin_conflicting_exact_variant"], 2)

    def test_invalid_upc_quarantines(self):
        self.item["upc"] = "123"
        self.save()
        records, report = build(self.staging, self.batch, self.secret)
        self.assertEqual(records, [])
        self.assertEqual(report["exception_reason_counts"]["invalid_gtin"], 1)

    def test_unmapped_category_quarantines(self):
        self.item["source_category"] = "Unclassified Source Label"
        self.save()
        records, report = build(self.staging, self.batch, self.secret)
        self.assertEqual(records, [])
        self.assertIn("unknown_public_category_mapping", report["exceptions"][0]["reasons"])

    def test_exif_source_is_held_not_auto_stripped_or_published(self):
        changed = jpeg(with_exif=True)
        self.original.write_bytes(changed)
        self.item["source_media"][0]["sha256"] = hashlib.sha256(changed).hexdigest()
        self.item["source_media"][0]["exif_present"] = True
        self.item["blockers"].append(
            "source_exif_requires_review_before_any_public_export"
        )
        self.save()
        rows, report = build(self.staging, self.batch, self.secret)
        self.assertEqual(rows, [])
        self.assertEqual(report["source_products"], 1)
        self.assertEqual(report["quarantined_identity_or_media_groups"], 1)
        self.assertEqual(report["groups_held_for_photo_metadata_review"], 1)
        self.assertEqual(
            report["exception_reason_counts"]["photo_exif_metadata_requires_review"],
            1,
        )
        # Originals are untouched. Metadata-bearing JPEG never enters an
        # approval draft (and the importer cannot publish images).
        self.assertEqual(self.original.read_bytes(), changed)

    def test_mixed_exif_and_clean_source_keeps_clean_product_moving(self):
        flagged = deepcopy(self.item)
        flagged["source_sku"] = "BBB-101"
        flagged["upc"] = "816161020241"
        folder = self.batch / "media" / flagged["source_sku"]
        folder.mkdir()
        photo = folder / "BBB-101_1_HR.jpg"
        tagged = jpeg(with_exif=True)
        photo.write_bytes(tagged)
        flagged["source_media"][0]["private_relative_file"] = (
            "media/BBB-101/BBB-101_1_HR.jpg"
        )
        flagged["source_media"][0]["sha256"] = hashlib.sha256(tagged).hexdigest()
        flagged["source_media"][0]["exif_present"] = True
        flagged["blockers"].append(
            "source_exif_requires_review_before_any_public_export"
        )
        self.payload["items"].append(flagged)
        self.save()
        records, report = build(self.staging, self.batch, self.secret)
        self.assertEqual(report["source_products"], 2)
        self.assertEqual(report["review_drafts_generated"], 1)
        self.assertEqual(report["quarantined_identity_or_media_groups"], 1)
        self.assertEqual(report["groups_held_for_photo_metadata_review"], 1)
        self.assertEqual(records[0]["photos"][0]["source_path"],
                         str(self.original.resolve()))
        self.assertNotIn(str(photo.resolve()), json.dumps(records))
        self.assertTrue(all(flag is False for flag in
                            records[0]["approvals"].values()))

    def test_explicit_exif_private_copies_allow_source_draft_with_no_approval(self):
        from PIL import ImageChops
        from private_exif_derivatives import strip_private_jpeg_metadata
        original = jpeg(with_exif=True)
        self.original.write_bytes(original)
        self.item["source_media"][0]["sha256"] = hashlib.sha256(original).hexdigest()
        self.item["source_media"][0]["exif_present"] = True
        self.item["blockers"].append(
            "source_exif_requires_review_before_any_public_export"
        )
        self.save()

        # Without explicit opt-in, do not process photos.
        legacy, legacy_report = build(self.staging, self.batch, self.secret)
        self.assertEqual(legacy, [])
        self.assertEqual(legacy_report["groups_held_for_photo_metadata_review"], 1)

        keyfile = self.root / "private-catalog-key.bin"
        report = write_private_bridge(
            self.staging, self.batch, self.out, keyfile,
            prepare_private_derivatives=True,
        )
        self.assertEqual(report["review_drafts_generated"], 1)
        self.assertEqual(report["quarantined_identity_or_media_groups"], 0)
        self.assertEqual(report["private_metadata_only_derivative_files"], 1)
        self.assertEqual(report["groups_held_for_photo_metadata_review"], 0)

        draft = json.loads(
            (self.out / "catalog-approval-template-part-001.json").read_text()
        )[0]
        path = Path(draft["photos"][0]["source_path"])
        self.assertTrue(path.is_file())
        self.assertTrue(path.is_relative_to(self.out))
        self.assertEqual(path.read_bytes(), strip_private_jpeg_metadata(original)[0])
        with Image.open(path) as image:
            self.assertFalse(image.getexif())
            image.load()
            with Image.open(self.original) as first:
                first.load()
                self.assertIsNone(ImageChops.difference(first, image).getbbox())
        self.assertEqual(self.original.read_bytes(), original)
        self.assertTrue(all(v is False for v in draft["approvals"].values()))
        self.assertEqual(draft["rights_source"], "")
        self.assertEqual(draft["status"], "draft")
        with self.assertRaises(CatalogPublicationError):
            publication_of_list(self.root, [draft])

    def test_unsafe_exif_orientation_stays_quarantined_with_optin(self):
        picture = Image.new("RGB", (900, 600), "white")
        meta = Image.Exif()
        meta[274] = 6
        stream = io.BytesIO()
        picture.save(stream, "JPEG", exif=meta)
        raw = stream.getvalue()
        self.original.write_bytes(raw)
        self.item["source_media"][0]["sha256"] = hashlib.sha256(raw).hexdigest()
        self.item["source_media"][0]["exif_present"] = True
        self.save()
        report = write_private_bridge(
            self.staging, self.batch, self.out,
            self.root / "private-catalog-key.bin",
            prepare_private_derivatives=True,
        )
        self.assertEqual(report["review_drafts_generated"], 0)
        self.assertEqual(report["groups_held_for_photo_metadata_review"], 1)
        self.assertEqual(report["private_metadata_only_derivative_files"], 0)
        self.assertIn(
            "source_metadata_requires_manual_review",
            report["exception_reason_counts"],
        )
        self.assertEqual(self.original.read_bytes(), raw)

    def test_private_exif_cleaner_refuses_nonexif_or_corrupt_input(self):
        from private_exif_derivatives import (
            PrivateDerivativeError, strip_private_jpeg_metadata,
        )
        with self.assertRaises(PrivateDerivativeError):
            strip_private_jpeg_metadata(jpeg())
        with self.assertRaises(PrivateDerivativeError):
            strip_private_jpeg_metadata(b"not-a-jpeg")

    def test_explicit_derivative_does_not_auto_approve_unknown_photo_rights(self):
        raw = jpeg(with_exif=True)
        self.original.write_bytes(raw)
        self.item["source_media"][0]["sha256"] = hashlib.sha256(raw).hexdigest()
        self.item["source_media"][0]["exif_present"] = True
        self.save()
        drafts, report = build(
            self.staging, self.batch, self.secret,
            private_derivatives_root=self.out / "private-exif-copies",
        )
        self.assertEqual(len(drafts), 1)
        self.assertEqual(drafts[0]["approvals"]["media_rights"], False)
        self.assertEqual(drafts[0]["approvals"]["owner_publication"], False)
        self.assertEqual(report["private_metadata_only_derivative_files"], 1)
        audit = report["private_metadata_derivative_audit"][0]
        self.assertTrue(audit["same_compressed_image_scan_preserved"])
        self.assertFalse(audit["advertising_rights_approved"])
        self.assertFalse(audit["publication_approved"])
        self.assertEqual(audit["source_sha256"], hashlib.sha256(raw).hexdigest())

    def test_tampered_bytes_fail_closed(self):
        self.original.write_bytes(jpeg() + b"extra")
        with self.assertRaises(BridgeError):
            build(self.staging, self.batch, self.secret)

    def test_path_traversal_fail_closed(self):
        self.item["source_media"][0]["private_relative_file"] = (
            "../media/AAA-101/AAA-101_1_HR.jpg"
        )
        self.save()
        with self.assertRaises(BridgeError):
            build(self.staging, self.batch, self.secret)

    def test_different_private_source_rights_state_refused(self):
        self.payload["media_rights_approved"] = True
        self.save()
        with self.assertRaises(BridgeError):
            build(self.staging, self.batch, self.secret)

    def test_source_image_rights_not_inferred(self):
        self.item["blockers"] = []
        self.save()
        records, _ = build(self.staging, self.batch, self.secret)
        self.assertTrue(all(x is False for x in records[0]["approvals"].values()))

    def test_once_only_output_private_and_100_max_per_bundle(self):
        keyfile = self.root / "private-catalog-key.bin"
        report = write_private_bridge(self.staging, self.batch, self.out, keyfile)
        self.assertEqual(report["review_drafts_generated"], 1)
        self.assertTrue(keyfile.exists())
        self.assertEqual(keyfile.stat().st_size, 32)
        draft = self.out / "catalog-approval-template-part-001.json"
        self.assertTrue(draft.exists())
        self.assertTrue((self.out / "catalog-private-exceptions.json").exists())
        records = json.loads(draft.read_text())
        self.assertFalse(records[0]["approvals"]["owner_publication"])
        with self.assertRaises(BridgeError):
            write_private_bridge(self.staging, self.batch, self.out, keyfile)

    def test_fail_when_sources_are_labeled_published(self):
        self.item["publication_approved"] = True
        self.save()
        with self.assertRaises(BridgeError):
            build(self.staging, self.batch, self.secret)


def validate_source_of_list(root, rows):
    file = root / "private-owner-input.json"
    file.write_text(json.dumps(rows), encoding="utf-8")
    result, _ = validate_source(file)
    return result


def publication_of_list(root, rows):
    file = root / "private-publish-input.json"
    file.write_text(json.dumps(rows), encoding="utf-8")
    return build_public(file)


if __name__ == "__main__":
    unittest.main()
