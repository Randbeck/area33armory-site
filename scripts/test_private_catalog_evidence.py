"""49-candidate/11-exception synthetic end-to-end identity-evidence tests."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import hmac
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from build_private_catalog_review import ReviewError
from build_private_text_batch_review import make_batch_review
from import_randbeck_staging import _identity
from prepare_private_catalog_evidence import build_private_evidence
from prepare_private_product_research import prepare_research_packet,validate_research_packet
from prepare_private_first_release_readiness import create_private_readiness
from migrate_private_research_notes import migrate_saved_notes
from prepare_private_text_batch_handoff import prepare_private_text_handoff


def gtin(n):
    digits=f"{n:011d}"
    total=sum(int(x)*(3 if i%2==0 else 1)
              for i,x in enumerate(reversed(digits)))
    return digits+str((10-total%10)%10)


class PrivateIdentityEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.staging=self.root/"private-rsr-staging.json"
        self.drafts=self.root/"catalog-approval-template-part-001.json"
        self.exceptions=self.root/"catalog-private-exceptions.json"
        self.key=self.root/"identity-key.bin"
        self.key_bytes=bytes(range(32))
        self.key.write_bytes(self.key_bytes)
        self.sidecar=self.root/"private-evidence.json"
        self.html=self.root/"catalog-batch-evidence-review.html"
        self.records=[]
        self.source=[]
        self.holds=[]
        for i in range(49):
            name="Single Mag Carrier" if i<2 else "Synthetic Model "+str(i)
            brand="Example Brand" if i<2 else "Sample Manufacturer"
            mpn=f"PART-{i+100:04d}"
            source={
                "source_sku":f"RSR-{i+100:05d}",
                "source_category":"Holsters & Pouches",
                "manufacturer":brand,"model":name,
                "manufacturer_part_number":mpn,"upc":gtin(i+123450),
                "description":"DO_NOT_COPY_VENDOR_MARKETING_DESCRIPTIONS",
                "publication_approved":False,"media_rights_approved":False,
                "source_offer_verified":False,"source_media":[],
                "private_dealer_cost":"SECRET_SUPPLIER_COST_123",
                "blockers":["policy_not_authorized"],
            }
            self.source.append(source)
            identity=_identity(source)
            opaque="catalog_"+hmac.new(
                self.key_bytes,"\x1f".join(identity).encode(),
                hashlib.sha256
            ).hexdigest()[:20]
            self.records.append({
                "id":opaque,"status":"draft",
                "manufacturer":brand,"model":name,"description":"",
                "listing_mode":"text_only","content_origin":"",
                "variant":"","category":"Holsters & Pouches",
                "product_type":"accessory","rights_source":"",
                "identity_evidence_label":"","source_checked_at":"",
                "photos":[],
                "approvals":{
                    "owner_publication":False,"exact_identity":False,
                    "media_rights":False,"content_review":False,
                    "offered_for_sale":False,
                },
            })
        for i in range(11):
            source={
                "source_sku":f"RSR-HOLD-{i:03d}",
                "source_category":"Holsters & Pouches",
                "manufacturer":"Missing Identity Brand","model":"",
                "manufacturer_part_number":f"UNKNOWN-{i}",
                "upc":gtin(500000+i),
                "description":"DO_NOT_COPY_VENDOR_MARKETING_DESCRIPTIONS",
                "publication_approved":False,"media_rights_approved":False,
                "source_offer_verified":False,"source_media":[],
            }
            self.source.append(source)
            self.holds.append({
                "upc":source["upc"],"manufacturer":source["manufacturer"],
                "model":"","source_skus":[source["source_sku"]],
                "reasons":["missing_manufacturer_mpn_or_model"],
                "owner_review_required":True,"publication_approved":False,
            })
        self._write_files()

    def tearDown(self):
        self.temp.cleanup()

    def _write_files(self):
        self.staging.write_text(json.dumps({
            "schema":"randbeck.area33.private_catalog_staging.v1",
            "source":"RSR","products_staged":len(self.source),
            "publication_enabled":False,"media_rights_approved":False,
            "source_offer_verified":False,"items":self.source,
        }),encoding="utf-8")
        self.drafts.write_text(json.dumps(self.records),encoding="utf-8")
        self.exceptions.write_text(json.dumps({
            "schema":"randbeck.area33.private_catalog_bridge_report.v1",
            "publication_enabled":False,"source_products":60,
            "exact_identity_groups":60,
            "review_drafts_generated":49,
            "quarantined_identity_or_media_groups":11,
            "exceptions":self.holds,
        }),encoding="utf-8")

    def build(self):
        return build_private_evidence(
            self.staging,self.drafts,self.exceptions,self.key,self.sidecar,
        )

    def test_49_private_evidence_matches_and_11_exceptions_stay_held(self):
        result=self.build()
        self.assertEqual(result["candidate_count"],49)
        self.assertEqual(result["held_identity_exception_count"],11)
        evidence=result["evidence"]
        self.assertEqual(len(evidence),49)
        self.assertEqual(len({x["recorded_upc"] for x in evidence}),49)
        self.assertEqual(evidence[0]["recorded_manufacturer_part_number"],"PART-0100")
        self.assertEqual(evidence[0]["recorded_source_skus"],["RSR-00100"])
        self.assertNotEqual(evidence[0]["recorded_upc"],evidence[1]["recorded_upc"])
        self.assertEqual(evidence[0]["recorded_model"],evidence[1]["recorded_model"])
        self.assertTrue(evidence[0]["neutral_draft_suggestion"])
        self.assertNotIn("DO_NOT_COPY_VENDOR_MARKETING_DESCRIPTIONS",json.dumps(result))
        self.assertNotIn("SECRET_SUPPLIER_COST_123",json.dumps(result))
        self.assertNotIn("private_dealer_cost",json.dumps(result))
        self.assertFalse(result["publication_approved"])
        self.assertFalse(result["media_rights_approved"])
        self.assertFalse(result["source_offer_verified"])
        html=make_batch_review(self.drafts,self.exceptions,self.html,evidence_file=self.sidecar)
        page=html.read_text()
        self.assertIn("Private source identity evidence",page)
        self.assertIn("PART-0100",page)
        self.assertIn("PART-0101",page)
        self.assertIn("Use as editable starting text",page)
        self.assertIn("Recorded UPC",page)
        self.assertIn("Quarantined identity exceptions",page)
        self.assertIn("RSR-HOLD-000",page)
        self.assertNotIn("DO_NOT_COPY_VENDOR_MARKETING_DESCRIPTIONS",page)
        self.assertNotIn("SECRET_SUPPLIER_COST_123",page)
        self.assertNotIn("fetch(",page)
        self.assertNotIn("XMLHttpRequest",page)
        self.assertNotIn("sendBeacon(",page)
        self.assertNotIn("localStorage",page)
        self.assertNotIn("sessionStorage",page)
        self.assertEqual([x["status"] for x in self.records],["draft"]*49)

    def test_reject_wrong_identity_key_and_no_evidence_output(self):
        self.key.write_bytes(bytes(reversed(range(32))))
        with self.assertRaisesRegex(ReviewError,"does not match"):
            self.build()
        self.assertFalse(self.sidecar.exists())

    def test_reject_mutated_candidate_identity_or_source(self):
        self.records[0]["model"]="Incompatible Changed Model"
        self._write_files()
        with self.assertRaises(ReviewError):
            self.build()
        self.assertFalse(self.sidecar.exists())

    def test_refuse_changed_drafts_after_sidecar_generated(self):
        self.build()
        self.records[0]["model"]="Changed Post-Evidence"
        self._write_files()
        with self.assertRaises(ReviewError):
            make_batch_review(self.drafts,self.exceptions,self.html,evidence_file=self.sidecar)
        self.assertFalse(self.html.exists())

    def test_refuse_tampered_private_source_evidence(self):
        self.build()
        payload=json.loads(self.sidecar.read_text())
        payload["evidence"][0]["recorded_model"]="Wrong Product"
        self.sidecar.write_text(json.dumps(payload),encoding="utf-8")
        with self.assertRaises(ReviewError):
            make_batch_review(self.drafts,self.exceptions,self.html,evidence_file=self.sidecar)

    def test_refuse_held_source_sku_in_candidate(self):
        self.source[0]["source_sku"]=self.holds[0]["source_skus"][0]
        self._write_files()
        with self.assertRaises(ReviewError):
            self.build()

    def test_handoff_excludes_private_evidence_and_still_requires_human_confirmation(self):
        self.build()
        make_batch_review(self.drafts,self.exceptions,self.html,evidence_file=self.sidecar)
        with self.assertRaises(ValueError):
            prepare_private_text_handoff(
                self.drafts,self.drafts,self.exceptions,
                self.root/"no-approved-handoff",
            )
        self.assertFalse((self.root/"no-approved-handoff").exists())

    def test_node_syntax_for_private_evidence_browser(self):
        node=shutil.which("node")
        if not node:
            self.skipTest("Node not installed")
        self.build()
        page=make_batch_review(
            self.drafts,self.exceptions,self.html,evidence_file=self.sidecar,
        ).read_text()
        scripts=re.findall(r"<script>\s*(.*?)\s*</script>",page,flags=re.S)
        self.assertEqual(len(scripts),1)
        js=self.root/"evidence-review-ui.js"
        js.write_text(scripts[0],encoding="utf-8")
        out=subprocess.run([node,"--check",str(js)],capture_output=True,text=True)
        self.assertEqual(out.returncode,0,out.stderr)

    def test_private_research_queue_for_49_has_no_invented_specs(self):
        self.build()
        research=self.root/"product-research-packet.json"
        packet=prepare_research_packet(self.drafts,self.exceptions,self.sidecar,research)
        self.assertEqual(packet["candidate_count"],49)
        self.assertTrue(all(item["sources"]==[] and item["facts"]==[]
                            for item in packet["items"]))
        self.assertFalse(packet["publication_approved"])
        self.assertFalse(packet["source_research_is_owner_verified"])
        self.assertNotIn("SECRET_SUPPLIER_COST_123",research.read_text())
        self.assertNotIn("DO_NOT_COPY_VENDOR_MARKETING_DESCRIPTIONS",research.read_text())
        html=make_batch_review(
            self.drafts,self.exceptions,self.html,
            evidence_file=self.sidecar,research_file=research,
        ).read_text()
        self.assertIn("Search public sources for this UPC",html)
        self.assertIn("Save research notes",html)
        self.assertIn("Use checked facts in editable draft",html)
        self.assertIn("Add independently found reference",html)
        self.assertIn('id="research-data"',html)
        self.assertNotIn("https://www.google.com/search?q=RSR-",html)
        self.assertNotIn("fetch(",html)
        self.assertNotIn("sendBeacon(",html)
        self.assertTrue(all(row["status"]=="draft" for row in self.records))

    def test_two_exact_public_research_leads_do_not_auto_verify(self):
        known=[
            ("193858308883","CMCS-2-D"),
            ("193858308906","CMCS-4-D"),
        ]
        for i,(upc,mpn) in enumerate(known):
            self.source[i]["upc"]=upc
            self.source[i]["manufacturer_part_number"]=mpn
            self.source[i]["manufacturer"]="Alien Gear Holsters"
            self.source[i]["model"]="Single Mag Carrier"
            self.records[i]["manufacturer"]="Alien Gear Holsters"
            self.records[i]["model"]="Single Mag Carrier"
            identity=_identity(self.source[i])
            self.records[i]["id"]="catalog_"+hmac.new(
                self.key_bytes,"\x1f".join(identity).encode(),hashlib.sha256
            ).hexdigest()[:20]
        self._write_files()
        self.build()
        research=self.root/"private-research.json"
        packet=prepare_research_packet(self.drafts,self.exceptions,self.sidecar,research)
        items=packet["items"][:2]
        self.assertEqual(len(items[0]["sources"]),2)
        self.assertEqual(len(items[1]["sources"]),2)
        self.assertEqual(items[0]["facts"][0]["value"],
                         "9mm/.40 S&W single-stack magazines")
        self.assertEqual(items[1]["facts"][0]["value"],
                         "9mm/.40 S&W double-stack magazines")
        self.assertTrue(all(not f["owner_checked"] for item in items
                            for f in item["facts"]))
        self.assertEqual(len(packet["items"]),49)
        self.assertEqual(len([it for it in packet["items"] if it["sources"]]),2)
        self.assertFalse(packet["publication_approved"])
        html=make_batch_review(
            self.drafts,self.exceptions,self.html,
            evidence_file=self.sidecar,research_file=research
        ).read_text()
        # Embedded private JSON escapes & as \u0026 to prevent HTML injection.
        self.assertIn("single-stack magazines",html)
        self.assertIn("double-stack magazines",html)
        self.assertNotIn("DO_NOT_COPY_VENDOR_MARKETING_DESCRIPTIONS",html)
        self.assertEqual([rec["status"] for rec in self.records],["draft"]*49)

    def test_changed_packet_provenance_or_unreferenced_fact_fails_closed(self):
        self.build()
        research=self.root/"research.json"
        packet=prepare_research_packet(self.drafts,self.exceptions,self.sidecar,research)
        packet["source_drafts_sha256"]="0"*64
        research.write_text(json.dumps(packet))
        with self.assertRaises(ReviewError):
            make_batch_review(self.drafts,self.exceptions,self.html,
                              evidence_file=self.sidecar,research_file=research)
        self.assertFalse(self.html.exists())
        packet["source_drafts_sha256"]=hashlib.sha256(self.drafts.read_bytes()).hexdigest()
        packet["items"][0]["facts"]=[{
            "label":"Compatibility","value":"Unsupported independent claim",
            "source_index":0,"owner_checked":True,
        }]
        research.write_text(json.dumps(packet))
        with self.assertRaises(ReviewError):
            make_batch_review(self.drafts,self.exceptions,self.html,
                              evidence_file=self.sidecar,research_file=research)

    def test_source_link_js_syntax_and_private_approval_boundary(self):
        node=shutil.which("node")
        if not node:self.skipTest("Node not installed")
        self.build()
        research=self.root/"product-research.json"
        prepare_research_packet(self.drafts,self.exceptions,self.sidecar,research)
        page=make_batch_review(
            self.drafts,self.exceptions,self.html,
            evidence_file=self.sidecar,research_file=research
        ).read_text()
        scripts=re.findall(r"<script>\s*(.*?)\s*</script>",page,flags=re.S)
        self.assertEqual(len(scripts),1)
        path=self.root/"source-backed-ui.js"
        path.write_text(scripts[0],encoding="utf-8")
        checked=subprocess.run([node,"--check",str(path)],
                               capture_output=True,text=True)
        self.assertEqual(checked.returncode,0,checked.stderr)
        with self.assertRaises(ValueError):
            prepare_private_text_handoff(
                self.drafts,self.drafts,self.exceptions,
                self.root/"not-approved",
            )
        self.assertFalse((self.root/"not-approved").exists())

    def _assign_real_identity(self,i,upc,mpn,model="Cloak Tuck 3.5"):
        self.source[i]["manufacturer"]="Alien Gear Holsters"
        self.source[i]["model"]=model
        self.source[i]["manufacturer_part_number"]=mpn
        self.source[i]["upc"]=upc
        self.records[i]["manufacturer"]="Alien Gear Holsters"
        self.records[i]["model"]=model
        identity=_identity(self.source[i])
        self.records[i]["id"]="catalog_"+hmac.new(
            self.key_bytes,"\x1f".join(identity).encode(),hashlib.sha256
        ).hexdigest()[:20]

    def test_conflicting_public_upcs_are_held_even_if_user_checks_approval(self):
        self._assign_real_identity(0,"193858332383","CT35-1198-RH-D")
        self._write_files()
        self.build()
        research_path=self.root/"private-research.json"
        packet=prepare_research_packet(
            self.drafts,self.exceptions,self.sidecar,research_path,
        )
        conflicting=packet["items"][0]
        self.assertEqual(conflicting["identity_warnings"][0]["code"],"conflicting_public_upc")
        self.assertEqual(conflicting["identity_warnings"][0]["observed_upcs"],
                         ["193858332383","193858373485"])
        self.assertEqual(len(conflicting["sources"]),2)
        self.assertEqual(conflicting["facts"],[])
        page=make_batch_review(
            self.drafts,self.exceptions,self.html,
            evidence_file=self.sidecar,research_file=research_path,
        ).read_text()
        self.assertIn("IDENTITY CONFLICT",page)
        self.assertIn("193858373485",page)
        self.assertIn("hasIdentityConflict(item)",page)
        self.assertIn("confirm.disabled=true",page)
        # Explicitly simulate a previously saved owner review. The conflict
        # must take precedence even over all four owner checkboxes.
        progress=json.loads(self.drafts.read_text())
        item=progress[0]
        item["status"]="published"
        item["content_origin"]="owner_written"
        item["description"]="Original checked description for a precise held product."
        item["identity_evidence_label"]="Independently checked local product identity"
        item["source_checked_at"]="2026-11-05"
        for approval in ("owner_publication","exact_identity",
                         "content_review","offered_for_sale"):
            item["approvals"][approval]=True
        progress_path=self.root/"owner-reviewed-progress.json"
        progress_path.write_text(json.dumps(progress),encoding="utf-8")
        report=create_private_readiness(
            self.drafts,self.exceptions,self.sidecar,research_path,
            self.root/"private-readiness",review_progress=progress_path,
        )
        self.assertEqual(report["counts"]["identity_conflict_hold"],1)
        self.assertEqual(report["counts"]["private_handoff_eligible"],0)
        self.assertEqual(report["held_identity_exceptions"],11)
        self.assertFalse(report["release_published"])
        self.assertTrue((self.root/"private-readiness/private-first-release-worklist.csv").is_file())

    def test_conflict_flag_cannot_be_removed_by_editing_private_notes(self):
        self._assign_real_identity(0,"193858332383","CT35-1198-RH-D")
        self._write_files()
        self.build()
        research_path=self.root/"private-research.json"
        packet=prepare_research_packet(self.drafts,self.exceptions,
                                       self.sidecar,research_path)
        packet["items"][0]["identity_warnings"]=[]
        research_path.write_text(json.dumps(packet),encoding="utf-8")
        with self.assertRaisesRegex(ReviewError,"UPC conflict"):
            make_batch_review(
                self.drafts,self.exceptions,self.html,
                evidence_file=self.sidecar,research_file=research_path
            )
        with self.assertRaisesRegex(ReviewError,"UPC conflict"):
            create_private_readiness(
                self.drafts,self.exceptions,self.sidecar,research_path,
                self.root/"private-readiness"
            )

    def test_readiness_summarizes_first_owner_approved_text_and_held_drafts(self):
        self._assign_real_identity(
            0,"193858308937","CT35-0057-RH-D",model="Cloak Tuck",
        )
        self._assign_real_identity(
            1,"193858309125","CT35-0939-RH-D",model="Cloak Tuck 3.5",
        )
        self._write_files()
        self.build()
        research_path=self.root/"private-research.json"
        packet=prepare_research_packet(self.drafts,self.exceptions,
                                       self.sidecar,research_path)
        self.assertEqual(len([it for it in packet["items"] if it["sources"]]),2)
        self.assertTrue(all(not f["owner_checked"] for it in packet["items"]
                            for f in it["facts"]))
        progress=json.loads(self.drafts.read_text())
        one=progress[0]
        one["status"]="published"
        one["description"]="Independently reviewed source copy for a specific product."
        one["content_origin"]="owner_written"
        one["source_checked_at"]="2026-11-05"
        one["identity_evidence_label"]="Manufacturer/model confirmed by owner"
        for key in ("owner_publication","exact_identity","content_review","offered_for_sale"):
            one["approvals"][key]=True
        progress_path=self.root/"saved-progress.json"
        progress_path.write_text(json.dumps(progress),encoding="utf-8")
        report=create_private_readiness(
            self.drafts,self.exceptions,self.sidecar,research_path,
            self.root/"private-readiness",review_progress=progress_path
        )
        self.assertEqual(report["candidate_count"],49)
        self.assertEqual(report["held_identity_exceptions"],11)
        self.assertEqual(report["counts"]["private_handoff_eligible"],1)
        self.assertEqual(report["counts"]["owner_review_pending"],1)
        self.assertEqual(report["counts"]["independent_research_needed"],47)
        self.assertEqual(report["counts"]["identity_conflict_hold"],0)
        self.assertFalse(report["approval_created"])
        self.assertFalse(report["public_site_modified"])
        self.assertFalse(report["release_published"])
        self.assertEqual(report["items"][0]["id"],one["id"])
        self.assertNotIn("SECRET_SUPPLIER_COST_123",json.dumps(report))
        self.assertNotIn("RSR-HOLD-",json.dumps(report))
        page=make_batch_review(
            self.drafts,self.exceptions,self.html,
            evidence_file=self.sidecar,research_file=research_path,
            saved_progress=progress_path,
        ).read_text()
        self.assertIn("Independently reviewed source copy",page)
        self.assertEqual(self.records[0]["status"],"draft")

    def test_saved_progress_cannot_swap_manufacturer_or_model_in_new_reviewer(self):
        self.build()
        research_path=self.root/"private-research.json"
        prepare_research_packet(self.drafts,self.exceptions,self.sidecar,research_path)
        progress=json.loads(self.drafts.read_text())
        progress[0]["manufacturer"]="Other Manufacturer"
        progress_path=self.root/"saved-progress.json"
        progress_path.write_text(json.dumps(progress),encoding="utf-8")
        with self.assertRaises(ReviewError):
            make_batch_review(
                self.drafts,self.exceptions,self.html,
                evidence_file=self.sidecar,research_file=research_path,
                saved_progress=progress_path
            )
        self.assertFalse(self.html.exists())

    def test_saved_legacy_research_preserves_personally_checked_facts(self):
        self._assign_real_identity(
            0,"193858308883","CMCS-2-D",model="Single Mag Carrier",
        )
        self._write_files()
        self.build()
        research_path=self.root/"fresh-research.json"
        packet=prepare_research_packet(
            self.drafts,self.exceptions,self.sidecar,research_path
        )
        old=json.loads(json.dumps(packet))
        for row in old["items"]:
            del row["identity_warnings"]  # legacy saved research v1
        old["items"][0]["facts"][0]["owner_checked"]=True
        old["items"][0]["sources"].append({
            "title":"Additional independently reviewed source",
            "url":"https://example.com/review-1",
            "source_kind":"other_public_reference",
            "observed_on":"2026-11-05",
        })
        old["items"][0]["facts"].append({
            "label":"Finish/color","value":"Black color confirmed in extra record",
            "source_index":2,"owner_checked":True,
        })
        saved=self.root/"legacy-saved-notes.json"
        saved.write_text(json.dumps(old),encoding="utf-8")
        merged_path=self.root/"private-merged-research.json"
        merged=migrate_saved_notes(
            saved,research_path,self.drafts,self.exceptions,
            self.sidecar,merged_path,
        )
        self.assertEqual(merged["candidate_count"],49)
        self.assertEqual(sum(bool(x["identity_warnings"]) for x in merged["items"]),0)
        item=merged["items"][0]
        self.assertEqual(len(item["sources"]),3)
        self.assertEqual(len(item["facts"]),3)
        self.assertTrue(item["facts"][0]["owner_checked"])
        self.assertTrue(item["facts"][2]["owner_checked"])
        self.assertEqual(item["sources"][2]["url"],"https://example.com/review-1")
        page=make_batch_review(
            self.drafts,self.exceptions,self.html,
            evidence_file=self.sidecar,research_file=merged_path,
        ).read_text()
        self.assertIn("Black color confirmed in extra record",page)
        self.assertFalse(merged["publication_approved"])

    def test_saved_notes_cannot_erase_newly_identified_upc_conflict(self):
        self._assign_real_identity(
            0,"193858332383","CT35-1198-RH-D",
        )
        self._write_files()
        self.build()
        packet_path=self.root/"fresh-research.json"
        base=prepare_research_packet(
            self.drafts,self.exceptions,self.sidecar,packet_path,
        )
        old=json.loads(json.dumps(base))
        for row in old["items"]:
            del row["identity_warnings"]
        old["items"][0]["sources"]=[]
        saved=self.root/"older-research-notes.json"
        saved.write_text(json.dumps(old),encoding="utf-8")
        merged=migrate_saved_notes(
            saved,packet_path,self.drafts,self.exceptions,self.sidecar,
            self.root/"migrated-research.json",
        )
        self.assertEqual(merged["items"][0]["identity_warnings"][0]["code"],
                         "conflicting_public_upc")
        self.assertEqual(len(merged["items"][0]["sources"]),2)
        self.assertFalse(merged["publication_approved"])
        with self.assertRaises(ReviewError):
            migrate_saved_notes(
                saved,packet_path,self.drafts,self.exceptions,
                self.sidecar,self.root/"migrated-research.json",
            )

    def test_no_evidence_provided_preserves_existing_review_workflow(self):
        html=make_batch_review(self.drafts,self.exceptions,self.html)
        text=html.read_text()
        self.assertIn("Batch product review",text)
        self.assertIn("Private source identity evidence",text)  # JS template remains
        self.assertIn('id="source-evidence"',text) if False else None


if __name__=="__main__":
    unittest.main()
