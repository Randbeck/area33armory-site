"""Synthetic >100-product tests for private approved-only static release preparation."""
from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from prepare_approved_catalog_shards import (
    ShardedReleaseError,prepare_private_release,
)


class ShardedApprovedReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.photo=self.root/"synthetic-original.jpg"
        Image.new("RGB",(400,250),"white").save(self.photo,"JPEG")
        self.hash=hashlib.sha256(self.photo.read_bytes()).hexdigest()
        self.approvals={
            "owner_publication":True,"exact_identity":True,
            "media_rights":True,"content_review":True,"offered_for_sale":True,
        }
        self.entries=[self.make_approved(i) for i in range(205)]
        self.bundles=self.make_bundles(self.entries,tag="original")

    def tearDown(self):
        self.tmp.cleanup()

    def make_approved(self,i):
        return {
            "id":"catalog_"+format(i,"020x"),
            "status":"published",
            "manufacturer":"Example Manufacturer",
            "model":"Model "+str(i),
            "description":"Owner-reviewed catalog detail "+str(i),
            "variant":"", "category":"Holsters",
            "product_type":"accessory",
            "rights_source":"Owner-approved synthetic rights source",
            "identity_evidence_label":"Owner-reviewed synthetic exact identity",
            "source_checked_at":"2026-11-04",
            "photos":[{
                "angle":"view-01","source_path":str(self.photo),
                "source_sha256":self.hash,
                "alt":"Original synthetic photo for exact product "+str(i),
            }],
            "approvals":dict(self.approvals),
            "dealer_cost":"SENSITIVE_PRICE_NOT_FOR_PUBLIC",
        }

    def make_bundles(self,rows,tag):
        files=[]
        for n in range(0,len(rows),100):
            file=self.root/f"{tag}-{n//100+1:03d}.json"
            file.write_text(json.dumps(rows[n:n+100]),encoding="utf-8")
            files.append(file)
        return files

    def test_205_approved_records_create_three_private_searchable_shards(self):
        output=self.root/"private-v2-stage"
        audit,index=prepare_private_release(self.bundles,output)
        self.assertEqual(index["total"],205)
        self.assertEqual([x["count"] for x in index["shards"]],[100,100,5])
        self.assertEqual(index["products"][204]["description"],
                         "Owner-reviewed catalog detail 204")
        self.assertFalse(audit["published"])
        self.assertFalse(audit["website_modified"])
        self.assertEqual(audit["source_approved_bundle_count"],3)
        self.assertEqual(audit["private_source_media_file_count"],205)
        written=json.loads(
            (output/"assets/catalog-index.v2.json").read_text(encoding="utf-8")
        )
        self.assertEqual(written,index)
        for shard in index["shards"]:
            body=(output/shard["url"]).read_bytes()
            self.assertEqual(hashlib.sha256(body).hexdigest(),shard["sha256"])
            value=json.loads(body)
            self.assertEqual(value["schema"],"area33.catalog.shard.v2")
            self.assertEqual(len(value["items"]),shard["count"])
        sample=output/"assets/approved/catalog"/self.entries[200]["id"]/"view-01.jpg"
        self.assertEqual(sample.read_bytes(),self.photo.read_bytes())
        public_text=json.dumps(index)+"".join(
            (output/shard["url"]).read_text(encoding="utf-8")
            for shard in index["shards"]
        )
        self.assertNotIn("SENSITIVE_PRICE_NOT_FOR_PUBLIC",public_text)
        self.assertNotIn("source_path",public_text)
        self.assertNotIn("source_sha256",public_text)
        self.assertNotIn(str(self.photo),public_text)
        self.assertFalse((self.root/"assets/catalog-index.v2.json").exists())

    def test_unapproved_records_cannot_stage_public_catalog(self):
        item=self.make_approved(990)
        item["approvals"]["media_rights"]=False
        files=self.make_bundles([item],tag="unsafe")
        with self.assertRaises(ValueError):
            prepare_private_release(files,self.root/"should-not-exist")
        self.assertFalse((self.root/"should-not-exist").exists())

    def test_duplicates_across_approved_bundles_are_refused(self):
        records=[self.make_approved(9),self.make_approved(9)]
        files=self.make_bundles(records,tag="duplicates")
        with self.assertRaises(ShardedReleaseError):
            prepare_private_release(files,self.root/"duplicate-output")

    def test_previous_record_removal_requires_explicit_reviewed_withdrawal(self):
        prior=self.root/"initial"
        _,old=prepare_private_release(self.bundles,prior)
        prev=prior/"assets/catalog-index.v2.json"
        removed=self.entries[204]["id"]
        next_bundles=self.make_bundles(self.entries[:204],tag="next")
        with self.assertRaises(ShardedReleaseError):
            prepare_private_release(next_bundles,self.root/"no-withdrawal",
                                    previous_index=prev)
        self.assertFalse((self.root/"no-withdrawal").exists())
        private_file=self.root/"signed-withdrawal.json"
        private_file.write_text(json.dumps({
            "schema":"area33.catalog.withdrawals.private.v1",
            "items":[{
                "id":removed,"reason":"Owner reviewed discontinuation",
                "approved_by":"Private reviewer","reviewed_at":"2026-11-04",
            }],
        }))
        audit,index=prepare_private_release(
            next_bundles,self.root/"after-withdrawal",
            previous_index=prev,withdrawal_file=private_file,
        )
        self.assertEqual(index["total"],204)
        self.assertEqual(audit["approved_withdrawal_count"],1)
        self.assertEqual(audit["previous_catalog_record_count"],205)
        self.assertNotIn(removed,{x["id"] for x in index["products"]})
        self.assertFalse(audit["published"])

    def test_original_site_public_manifest_remains_unchanged(self):
        repo=Path(__file__).resolve().parents[1]
        manifest=repo/"assets/catalog-public.json"
        before=manifest.read_bytes()
        prepare_private_release(
            self.make_bundles([self.make_approved(4000)],tag="single"),
            self.root/"isolated",
        )
        self.assertEqual(manifest.read_bytes(),before)
        self.assertEqual(json.loads(before)["items"],[])


if __name__=="__main__":
    unittest.main()
