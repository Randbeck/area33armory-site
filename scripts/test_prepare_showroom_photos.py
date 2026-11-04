"""Offline intake tests: no actual product claims or images published."""
import json
import tempfile
import unittest
from pathlib import Path
import sys
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_showroom_photos import IntakeError, process_photos


class PhotoIntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.src = self.base / "src"
        self.src.mkdir()
        for p in ["left.jpg", "right.jpg"]:
            im = Image.new("RGB", (1000, 600), (90, 90, 90))
            exif = Image.Exif()
            exif[271] = "PRIVATE_CAMERA_METADATA"
            im.save(self.src/p, exif=exif)
        self.out = self.base / "private-review"

    def prepare(self, **kw):
        opts = dict(manufacturer="Example", model="Exact model", variant="Variant", public_id="record_test_123456",
                    photo_args=["left="+str(self.src/"left.jpg"),"right="+str(self.src/"right.jpg")], out=self.out)
        opts.update(kw)
        return process_photos(**opts)

    def test_creates_review_without_claiming_approval(self):
        dest = self.prepare()
        data = json.loads((dest/"private-review.json").read_text())[0]
        self.assertEqual(data["status"], "draft")
        self.assertFalse(any(data["approvals"].values()))
        self.assertEqual(len(data["frames"]), 2)
        self.assertTrue((dest/"review.html").exists())
        for f in data["frames"]:
            photo = dest / f["src"]
            self.assertTrue(photo.is_file())
            with Image.open(photo) as im:
                self.assertEqual(im.format, "WEBP")
                self.assertFalse(im.info.get("exif"))
                self.assertLessEqual(max(im.size), 1800)

    def test_rejects_duplicate_angles(self):
        with self.assertRaises(IntakeError):
            self.prepare(photo_args=["left="+str(self.src/"left.jpg"),"left="+str(self.src/"right.jpg")])

    def test_refuses_overwrite(self):
        self.prepare()
        with self.assertRaises(IntakeError): self.prepare()

    def test_rejects_too_small_image_and_removes_partial_bundle(self):
        Image.new("RGB", (200, 200), "white").save(self.src/"right.jpg")
        with self.assertRaises(IntakeError): self.prepare()
        self.assertFalse((self.out/"area33-review-record_test_123456").exists())

    def test_rejects_disguised_file(self):
        (self.src/"right.jpg").write_text("not a photo")
        with self.assertRaises(IntakeError): self.prepare()

    def test_rejects_insufficient_photos(self):
        with self.assertRaises(IntakeError): self.prepare(photo_args=["left="+str(self.src/"left.jpg")])

if __name__ == "__main__":
    unittest.main()
