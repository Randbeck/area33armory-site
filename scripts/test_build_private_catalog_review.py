"""Offline private browser-review generation and safety checks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image
from build_private_catalog_review import ReviewError, make_review, validate_source


class PrivateOwnerReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.photo=self.root/"source.jpg"
        Image.new("RGB",(400,250),(245,245,245)).save(self.photo,"JPEG")
        self.item={
            "id":"catalog_0123456789abcdefabcd",
            "status":"draft",
            "manufacturer":"Example maker","model":"Example exact model",
            "variant":"","category":"","product_type":"","rights_source":"",
            "identity_evidence_label":"","source_checked_at":"",
            "photos":[{
                "angle":"view-01",
                "source_path":str(self.photo),
                "source_sha256":hashlib.sha256(self.photo.read_bytes()).hexdigest(),
                "alt":"",
            }],
            "approvals":{
                "exact_identity":False,
                "media_rights":False,
                "content_review":False,
                "offered_for_sale":False,
                "owner_publication":False,
            },
        }
        self.file=self.root/"catalog-approval-template.json"
        self.write()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self):
        self.file.write_text(json.dumps([self.item]),encoding="utf-8")

    def test_generates_review_beside_private_template_only(self):
        html=make_review(self.file)
        self.assertEqual(html.parent,self.root)
        page=html.read_text(encoding="utf-8")
        self.assertIn("Product approval workspace",page)
        self.assertIn("Save private progress",page)
        self.assertIn("Export approved items only",page)
        self.assertIn("offered_for_sale",page)
        self.assertIn("media_rights",page)
        self.assertIn("Draft — not approved",page)
        self.assertIn("file://",page)
        self.assertIn("photo",page)
        self.assertNotIn("fetch(",page)
        self.assertNotIn("XMLHttpRequest",page)
        self.assertNotIn("localStorage",page)
        self.assertNotIn("sessionStorage",page)
        self.assertNotIn("sendBeacon",page)
        self.assertFalse(self.item["approvals"]["owner_publication"])
        with self.assertRaises(ReviewError):
            make_review(self.file)

    def test_never_marks_an_approval_automatically(self):
        page=make_review(self.file).read_text()
        self.assertIn('"owner_publication": false',page)
        self.assertIn('"media_rights": false',page)
        self.assertIn('if(!confirm(',page)
        self.assertIn('item.status="published"',page)
        self.assertIn('function edited(){item.status="draft"',page)

    def test_escapes_malicious_source_labels_inside_json(self):
        self.item["manufacturer"]='</script><script>bad()</script>'
        self.write()
        page=make_review(self.file).read_text()
        self.assertNotIn('</script><script>bad()</script>',page)
        self.assertIn(r'\u003c/script\u003e',page)

    def test_reject_missing_or_changed_private_photo(self):
        self.photo.write_bytes(b"tampered")
        with self.assertRaises(ReviewError):
            validate_source(self.file)

    def test_reject_duplicate_ids(self):
        self.file.write_text(json.dumps([self.item,self.item]))
        with self.assertRaises(ReviewError):
            validate_source(self.file)

    def test_approval_flags_must_be_bools(self):
        self.item["approvals"]["media_rights"]="true"
        self.write()
        with self.assertRaises(ReviewError):
            validate_source(self.file)

    def test_works_with_previously_saved_owner_draft(self):
        self.item["category"]="Holsters"
        self.item["product_type"]="accessory"
        self.item["photos"][0]["alt"]="One source photo"
        self.write()
        page=make_review(self.file).read_text()
        self.assertIn("Holsters",page)
        self.assertIn("One source photo",page)

    def test_browser_javascript_syntax_if_node_is_installed(self):
        node=shutil.which("node")
        if not node:
            self.skipTest("Node not installed in local environment")
        page=make_review(self.file).read_text()
        found=re.findall(r"<script>\s*(.*?)\s*</script>",page,flags=re.S)
        self.assertEqual(len(found),1)
        test_script=self.root/"review-js-check.js"
        test_script.write_text(found[0],encoding="utf-8")
        completed=subprocess.run([node,"--check",str(test_script)],capture_output=True,text=True)
        self.assertEqual(completed.returncode,0,completed.stderr)


if __name__=="__main__":
    unittest.main()
