"""Synthetic 49-draft / 11-exception text-only owner batch review tests.

All products and data here are fake and unpublished. No media licenses,
reseller approvals or genuine manufacturer identity reviews are implied.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from build_private_text_batch_review import (
    make_batch_review,source_batch,ReviewError,
)
from prepare_private_text_batch_handoff import (
    prepare_private_text_handoff,PrivateHandoffError,
)
from publish_approved_catalog import CatalogPublicationError
from stage_private_media_withdrawal import _approved_previous


class OwnerTextBatchReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.draft=self.root/"catalog-approval-template-part-001.json"
        self.exceptions=self.root/"catalog-private-exceptions.json"
        self.output=self.root/"private-approved-handoff"
        self.rows=[self.make_draft(i) for i in range(49)]
        self.write_drafts()
        self.write_exceptions()
        self.live=Path(__file__).resolve().parents[1]/"assets/catalog-public.json"
        self.live_bytes=self.live.read_bytes()

    def tearDown(self):
        self.temp.cleanup()

    def make_draft(self,i):
        return {
            "id":"catalog_"+format(i+1,"020x"),
            "status":"draft",
            "manufacturer":"Example Manufacturer",
            "model":"Synthetic Model "+str(i+1),
            "variant":"","category":"Holsters & Pouches",
            "product_type":"accessory",
            "description":"","listing_mode":"text_only",
            "content_origin":"",
            "rights_source":"","photos":[],
            "identity_evidence_label":"","source_checked_at":"",
            "approvals":{
                "owner_publication":False,"exact_identity":False,
                "media_rights":False,"content_review":False,
                "offered_for_sale":False,
            },
        }

    def write_drafts(self):
        self.draft.write_text(json.dumps(self.rows),encoding="utf-8")

    def write_exceptions(self):
        entries=[{
            "upc":"","manufacturer":"Example Review Brand","model":"",
            "source_skus":["TEST-"+str(i)],
            "reasons":["missing_manufacturer_mpn_or_model"],
            "owner_review_required":True,"publication_approved":False,
        } for i in range(11)]
        self.exceptions.write_text(json.dumps({
            "schema":"randbeck.area33.private_catalog_bridge_report.v1",
            "publication_enabled":False,
            "source_products":60,
            "exact_identity_groups":60,
            "review_drafts_generated":49,
            "quarantined_identity_or_media_groups":11,
            "exceptions":entries,
        }),encoding="utf-8")

    def approve(self,i,*,description=None):
        row=self.rows[i]
        row["status"]="published"
        row["content_origin"]="owner_written"
        row["description"]=description or "Original, independently written information for exact item "+str(i)
        row["identity_evidence_label"]="Exact model independently verified from private sample"
        row["source_checked_at"]="2026-11-05"
        for key in ("owner_publication","exact_identity","content_review","offered_for_sale"):
            row["approvals"][key]=True

    def test_49_drafts_and_11_quarantined_exceptions_offline_and_unapproved(self):
        rows,exceptions=source_batch(self.draft,self.exceptions)
        self.assertEqual(len(rows),49)
        self.assertEqual(len(exceptions),11)
        page=make_batch_review(self.draft,self.exceptions)
        text=page.read_text(encoding="utf-8")
        self.assertIn("Batch product review",text)
        self.assertIn("Next unfinished",text)
        self.assertIn("Resume saved progress",text)
        self.assertIn("Export approved-only JSON",text)
        self.assertIn("Quarantined identity exceptions",text)
        self.assertIn("There is no bulk-approval button",text)
        self.assertIn("zero images",text.lower().replace("no images","zero images") if "zero images" in text.lower() else "zero images")
        self.assertNotIn("fetch(",text)
        self.assertNotIn("XMLHttpRequest",text)
        self.assertNotIn("localStorage",text)
        self.assertNotIn("sessionStorage",text)
        self.assertNotIn("sendBeacon(",text)
        self.assertNotIn("https://",text)
        self.assertFalse(any(row["approvals"]["owner_publication"] for row in self.rows))
        self.assertEqual(self.live.read_bytes(),self.live_bytes)
        with self.assertRaises(ReviewError):
            make_batch_review(self.draft,self.exceptions)

    def test_offline_page_escapes_script_injected_identity_label(self):
        self.rows[1]["model"]='</script><img src=x onerror=alert(1)>'
        self.write_drafts()
        text=make_batch_review(self.draft,self.exceptions).read_text()
        self.assertNotIn('</script><img src=x onerror=alert(1)>',text)
        self.assertIn(r"\u003c/script\u003e",text)

    def test_node_checks_review_browser_script_syntax(self):
        node=shutil.which("node")
        if not node:
            self.skipTest("Node.js is not installed")
        page=make_batch_review(self.draft,self.exceptions).read_text()
        scripts=re.findall(r"<script>\s*(.*?)\s*</script>",page,flags=re.S)
        self.assertEqual(len(scripts),1)
        path=self.root/"batch-review-check.js"
        path.write_text(scripts[0],encoding="utf-8")
        result=subprocess.run([node,"--check",str(path)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_private_handoff_excludes_unapproved_and_identity_exceptions(self):
        self.approve(0)
        self.approve(3)
        self.write_drafts()
        approved_file=self.root/"downloaded-reviewed-progress.json"
        approved_file.write_text(json.dumps(self.rows),encoding="utf-8")
        audit=prepare_private_text_handoff(
            approved_file,self.draft,self.exceptions,self.output,
            stage_private_release=True,
        )
        self.assertEqual(audit["baseline_candidate_count"],49)
        self.assertEqual(audit["review_input_count"],49)
        self.assertEqual(audit["individually_approved_count"],2)
        self.assertEqual(audit["other_input_records_kept_as_draft"],47)
        self.assertEqual(audit["quarantined_identity_exception_count"],11)
        self.assertFalse(audit["published"])
        bundle=json.loads((self.output/"catalog-owner-approved-part-001.json").read_text())
        self.assertEqual(len(bundle),2)
        self.assertEqual({x["id"] for x in bundle},{
            self.rows[0]["id"],self.rows[3]["id"],
        })
        self.assertTrue(all(x["photos"]==[] and x["approvals"]["media_rights"] is False
                            for x in bundle))
        staged=self.output/"approved-private-v2-release"
        idx,full,provenance,media=_approved_previous(staged)
        self.assertEqual(idx["total"],2)
        self.assertEqual(len(full),2)
        self.assertEqual(media,{})
        self.assertEqual(len(provenance),2)
        self.assertEqual(self.live.read_bytes(),self.live_bytes)
        self.assertFalse((self.live.parent/"catalog-index.v2.json").exists())
        # No exception SKU should enter public-approved catalog.
        self.assertNotIn("TEST-",json.dumps(idx))

    def test_handoff_works_with_browser_approved_only_subset(self):
        self.approve(0)
        self.write_drafts()
        exported=self.root/"only-approved.json"
        exported.write_text(json.dumps([self.rows[0]]),encoding="utf-8")
        audit=prepare_private_text_handoff(
            exported,self.draft,self.exceptions,self.output
        )
        self.assertEqual(audit["individually_approved_count"],1)
        self.assertFalse(audit["private_approved_release_staged"])
        self.assertFalse((self.output/"approved-private-v2-release").exists())

    def test_cannot_promote_empty_or_unreviewed_batch(self):
        with self.assertRaises(PrivateHandoffError):
            prepare_private_text_handoff(
                self.draft,self.draft,self.exceptions,self.output,
                stage_private_release=True,
            )
        self.assertFalse(self.output.exists())
        self.rows[0]["status"]="published"
        self.write_drafts()
        with self.assertRaises(PrivateHandoffError):
            prepare_private_text_handoff(
                self.draft,self.draft,self.exceptions,self.output
            )
        self.assertFalse(self.output.exists())

    def test_changed_manufacturer_or_model_fails_even_when_checks_all_true(self):
        self.approve(0)
        progress=self.root/"progress.json"
        changed=[dict(x) for x in self.rows]
        changed[0]={**self.rows[0],"model":"Different Model"}
        progress.write_text(json.dumps(changed),encoding="utf-8")
        with self.assertRaisesRegex(PrivateHandoffError,"identity"):
            prepare_private_text_handoff(progress,self.draft,self.exceptions,self.output)
        self.assertFalse(self.output.exists())

    def test_image_rights_cannot_be_claimed_in_text_handoff(self):
        self.approve(0)
        changed=[dict(x) for x in self.rows]
        changed[0]={**self.rows[0],
                    "approvals":{**self.rows[0]["approvals"],"media_rights":True}}
        progress=self.root/"progress.json"
        progress.write_text(json.dumps(changed),encoding="utf-8")
        with self.assertRaises(ReviewError):
            prepare_private_text_handoff(progress,self.draft,self.exceptions,self.output)

    def test_exception_report_mismatch_blocks_review_and_handoff(self):
        raw=json.loads(self.exceptions.read_text())
        raw["quarantined_identity_or_media_groups"]=12
        self.exceptions.write_text(json.dumps(raw),encoding="utf-8")
        with self.assertRaises(ReviewError):
            make_batch_review(self.draft,self.exceptions)
        self.assertFalse((self.root/"catalog-batch-owner-review.html").exists())
        self.approve(0)
        self.write_drafts()
        with self.assertRaises(ReviewError):
            prepare_private_text_handoff(
                self.draft,self.draft,self.exceptions,self.output
            )

    def test_unrecognized_product_id_cannot_be_injected_into_export(self):
        self.approve(0)
        injected=self.make_draft(900)
        injected["id"]="catalog_"+"f"*20
        progress=self.root/"progress.json"
        progress.write_text(json.dumps([self.rows[0],injected]),encoding="utf-8")
        with self.assertRaises(PrivateHandoffError):
            prepare_private_text_handoff(progress,self.draft,self.exceptions,self.output)

    def test_no_source_copy_attribution_or_trademark_license_is_inferred(self):
        self.approve(0)
        self.rows[0]["content_origin"]="source_copied"
        self.write_drafts()
        with self.assertRaises(PrivateHandoffError):
            prepare_private_text_handoff(self.draft,self.draft,self.exceptions,self.output)


if __name__=="__main__":
    unittest.main()
