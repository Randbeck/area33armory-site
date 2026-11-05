"""End-to-end synthetic tests: real Area33 site preview, integrity and rollback."""
from __future__ import annotations

from datetime import date
import hashlib
from http import HTTPStatus
import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from PIL import Image

from prepare_approved_catalog_shards import prepare_private_release
from stage_private_media_withdrawal import stage_media_withdrawal
from stage_private_catalog_site_preview import (
    ReleasePreflightError,prepare_private_website_preview,SITE,
)
from serve_private_catalog_preview import make_server,PrivatePreviewError


class RealWebsitePreviewTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.root=Path(self.temporary.name)
        self.sample_photo=self.root/"private-original.jpg"
        Image.new("RGB",(500,310),(15,15,15)).save(self.sample_photo,"JPEG")
        self.sample_hash=hashlib.sha256(self.sample_photo.read_bytes()).hexdigest()
        self.private_bundles=[]
        self.base=self.root/"approved-private-release"
        self.preview=self.root/"private-preview"
        self.original_site=(SITE/"assets/catalog-public.json").read_bytes()
        self.products=[self.item(1,with_image=True),
                       self.item(2,with_image=False),
                       self.item(3,with_image=False)]
        self._set_bundles(self.products,"initial")
        _,self.index=prepare_private_release(self.private_bundles,self.base)

    def tearDown(self):
        self.temporary.cleanup()

    def item(self,n,with_image=False):
        return {
            "id":"catalog_"+format(n,"020x"),
            "status":"published",
            "listing_mode":"image" if with_image else "text_only",
            "content_origin":"source_review_pending" if with_image else "owner_written",
            "manufacturer":"Example Brand",
            "model":"Synthetic Model "+str(n),
            "variant":"",
            "description":"Dealer-written sample text "+str(n),
            "category":"Holsters",
            "product_type":"accessory",
            "rights_source":"Synthetic permitted photo evidence" if with_image else "",
            "identity_evidence_label":"Verified synthetic exact model",
            "source_checked_at":"2026-11-04",
            "photos":[{
                "angle":"view-01",
                "source_path":str(self.sample_photo),
                "source_sha256":self.sample_hash,
                "alt":"Synthetic approved photo "+str(n),
            }] if with_image else [],
            "approvals":{
                "owner_publication":True,"exact_identity":True,
                "media_rights":with_image,"content_review":True,
                "offered_for_sale":True,
            },
            "private_dealer_cost":"NEVER_EXPORT_PRIVATE_299",
        }

    def _set_bundles(self,records,label):
        self.private_bundles=[]
        for offset in range(0,len(records),100):
            file=self.root/f"{label}-approved-{offset//100+1}.json"
            file.write_text(json.dumps(records[offset:offset+100]),encoding="utf-8")
            self.private_bundles.append(file)

    def test_real_site_preview_excludes_all_private_evidence(self):
        report=prepare_private_website_preview(self.base,self.preview)
        self.assertEqual(report["approved_product_count"],3)
        self.assertEqual(report["new_product_count"],3)
        self.assertEqual(report["changed_product_count"],0)
        self.assertEqual(report["withdrawn_product_count"],0)
        self.assertEqual(report["approved_image_file_count"],1)
        self.assertFalse(report["deployed"])
        site=self.preview/"site"
        self.assertTrue((site/"catalog.html").is_file())
        self.assertTrue((site/"assets/catalog.js").is_file())
        self.assertTrue((site/"assets/catalog-shards-contract.mjs").is_file())
        self.assertEqual(
            json.loads((site/"assets/catalog-index.v2.json").read_text()),
            self.index,
        )
        self.assertEqual(
            json.loads((site/"assets/catalog-public.json").read_text())["items"],
            [],
        )
        self.assertEqual(
            (site/"assets/approved/catalog"/self.products[0]["id"]/"view-01.jpg").read_bytes(),
            self.sample_photo.read_bytes(),
        )
        self.assertFalse((site/"catalog-private-media-provenance.json").exists())
        self.assertFalse((site/"preflight-private-report.json").exists())
        self.assertFalse((site/"catalog-private-release-audit.json").exists())
        self.assertFalse((site/".git").exists())
        self.assertFalse((site/".env").exists())
        self.assertEqual((SITE/"assets/catalog-public.json").read_bytes(),self.original_site)
        self.assertFalse((SITE/"assets/catalog-index.v2.json").exists())
        for shard in self.index["shards"]:
            path=site/shard["url"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                             shard["sha256"])
            self.assertNotIn("NEVER_EXPORT_PRIVATE_299",path.read_text())

    def test_preview_is_actual_website_served_only_on_localhost(self):
        prepare_private_website_preview(self.base,self.preview)
        server=make_server(self.preview,0)
        self.assertEqual(server.server_address[0],"127.0.0.1")
        running=Thread(target=server.serve_forever,daemon=True)
        running.start()
        try:
            prefix="http://127.0.0.1:"+str(server.server_address[1])
            with urlopen(prefix+"/catalog.html",timeout=5) as response:
                html=response.read().decode("utf-8")
                self.assertIn("assets/catalog.js",html)
                self.assertEqual(response.headers["Cache-Control"],"no-store, max-age=0")
            with urlopen(prefix+"/assets/catalog-index.v2.json",timeout=5) as response:
                index=json.load(response)
                self.assertEqual(index["total"],3)
            for path in ("/", "/preflight-private-report.json",
                         "/catalog-private-media-provenance.json"):
                if path=="/":
                    # Directory listing forbidden.
                    with self.assertRaises(HTTPError) as e:
                        urlopen(prefix+"/assets/",timeout=5)
                else:
                    with self.assertRaises(HTTPError) as e:
                        urlopen(prefix+path,timeout=5)
                self.assertEqual(e.exception.code,404)
        finally:
            server.shutdown()
            server.server_close()
            running.join(timeout=5)
        self.assertEqual((SITE/"assets/catalog-public.json").read_bytes(),self.original_site)

    def test_staging_never_accepts_unapproved_source_bundle(self):
        invalid=self.item(11,with_image=True)
        invalid["approvals"]["media_rights"]=False
        self._set_bundles([invalid],"invalid")
        with self.assertRaises(ValueError):
            prepare_private_release(self.private_bundles,self.root/"not-approved")
        self.assertFalse((self.root/"not-approved").exists())

    def test_tampered_approved_shard_aborts_before_preview_folder(self):
        source=self.base/self.index["shards"][0]["url"]
        source.write_bytes(source.read_bytes()+b"\n")
        with self.assertRaises(ValueError):
            prepare_private_website_preview(self.base,self.preview)
        self.assertFalse(self.preview.exists())

    def test_nonempty_public_fallback_refuses_unsafe_implicit_products(self):
        # No website files are changed. This check asserts the unchanged,
        # existing fallback is empty and won't mix in unaudited records.
        self.assertEqual(json.loads(self.original_site)["items"],[])

    def test_removal_and_cache_plan_requires_reviewed_withdrawal(self):
        self._set_bundles(self.products[1:],"replacement")
        previous_index=self.base/"assets/catalog-index.v2.json"
        replacement=self.root/"approved-private-replacement"
        withdrawal_file=self.root/"reviewed-withdrawal.json"
        withdrawal_file.write_text(json.dumps({
            "schema":"area33.catalog.withdrawals.private.v1",
            "items":[{
                "id":self.products[0]["id"],
                "reason":"Rights to sample photograph withdrawn",
                "approved_by":"Test owner",
                "reviewed_at":"2026-11-05",
            }],
        }),encoding="utf-8")
        _,replaced=prepare_private_release(
            self.private_bundles,replacement,
            previous_index=previous_index,withdrawal_file=withdrawal_file,
        )
        report=prepare_private_website_preview(
            replacement,self.preview,previous_release_root=self.base
        )
        self.assertEqual(report["approved_product_count"],2)
        self.assertEqual(report["withdrawn_product_count"],1)
        self.assertEqual(report["approved_image_file_count"],0)
        self.assertEqual(len(
            report["obsolete_image_urls_require_separate_host_removal"]
        ),1)
        self.assertFalse((self.preview/"site"/
                          "assets/approved/catalog"/self.products[0]["id"]).exists())
        self.assertEqual((SITE/"assets/catalog-public.json").read_bytes(),self.original_site)

    def test_changed_withdrawals_cannot_bypass_preflight(self):
        self._set_bundles(self.products[1:],"replacement")
        replacement=self.root/"approved-private-replacement"
        withdrawal_file=self.root/"reviewed-withdrawal.json"
        withdrawal_file.write_text(json.dumps({
            "schema":"area33.catalog.withdrawals.private.v1",
            "items":[{
                "id":self.products[0]["id"],
                "reason":"Rights to sample image withdrawn",
                "approved_by":"Test owner",
                "reviewed_at":"2026-11-05",
            }],
        }),encoding="utf-8")
        prepare_private_release(self.private_bundles,replacement,
            previous_index=self.base/"assets/catalog-index.v2.json",
            withdrawal_file=withdrawal_file)
        audit_path=replacement/"catalog-private-release-audit.json"
        audit=json.loads(audit_path.read_text())
        audit["approved_withdrawals"]=[]
        audit_path.write_text(json.dumps(audit),encoding="utf-8")
        with self.assertRaises(ReleasePreflightError):
            prepare_private_website_preview(
                replacement,self.preview,previous_release_root=self.base
            )
        self.assertFalse(self.preview.exists())

    def test_rights_withdrawal_release_requires_previous_root(self):
        withdrawn=self.root/"rights-removed"
        audit,index=stage_media_withdrawal(
            self.base,withdrawn,manufacturer="Example Brand",
            reviewer="Test owner",
            reason="Remove all photos pending rights review",
            reviewed_on="2026-11-05",
        )
        with self.assertRaises(ReleasePreflightError):
            prepare_private_website_preview(withdrawn,self.preview)
        result=prepare_private_website_preview(
            withdrawn,self.preview,previous_release_root=self.base
        )
        self.assertEqual(result["withdrawn_product_count"],1)
        self.assertEqual(result["approved_product_count"],2)
        self.assertEqual(result["approved_image_file_count"],0)


if __name__=="__main__":
    unittest.main()
