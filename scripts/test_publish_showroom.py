import sys,unittest
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).parent))
from publish_showroom import build,item,PublicationError

def good():
    frame=lambda angle: {"angle":angle,"src":"assets/approved/showroom/record_12345/"+angle+".webp","alt":"Actual licensed image at "+angle}
    config=lambda angle: {"angle":angle,"src":"assets/approved/showroom/record_12345/with-"+angle+".webp","alt":"Licensed approved configuration "+angle}
    return {
      "id":"record_123456789","status":"published",
      "manufacturer":"Test manufacturer","model":"Exact model","variant":"Exact variant",
      "rights_source":"Approved source agreement","identity_evidence_label":"Exact identifier independently checked",
      "checked_at":date.today().isoformat(),
      "frames":[frame("left"),frame("right")],
      "approvals":{"owner_publication":True,"exact_identity":True,"media_rights":True,"content_review":True},
      "configurations":[{
        "id":"option_123456789","status":"published","label":"Documented accessory combination",
        "pairing_evidence_label":"Reviewed manufacturer source",
        "frames":[config("left"),config("right")],
        "approvals":{"owner_publication":True,"media_rights":True,"exact_accessory":True,"pairing_verified":True,"image_alignment":True}
      }],
      "dealer_cost": 900,"customer_phone":"PRIVATE","internal_upc":"SECRET"
    }
class Tests(unittest.TestCase):
    def test_empty(self):self.assertEqual(build([])["items"],[])
    def test_draft_not_exposed(self):
        r=good();r["status"]="draft";self.assertEqual(build([r])["items"],[])
    def test_allowlist_no_private_data(self):
        x=item(good());self.assertNotIn("dealer_cost",x);self.assertNotIn("customer_phone",x);self.assertNotIn("internal_upc",x);self.assertNotIn("approvals",x)
        self.assertEqual(len(x["configurations"]),1)
    def test_owner_approval_required(self):
        r=good();r["approvals"]["owner_publication"]=False
        with self.assertRaises(PublicationError):item(r)
    def test_rights_required(self):
        r=good();r["approvals"]["media_rights"]=False
        with self.assertRaises(PublicationError):item(r)
    def test_invalid_url_rejected(self):
        r=good();r["frames"][0]["src"]="https://elsewhere.example/other.webp"
        with self.assertRaises(PublicationError):item(r)
    def test_path_traversal_rejected(self):
        r=good();r["frames"][0]["src"]="assets/approved/showroom/../private.jpg"
        with self.assertRaises(PublicationError):item(r)
    def test_exact_alignment_required(self):
        r=good();r["configurations"][0]["frames"][0]["angle"]="unmatched"
        with self.assertRaises(PublicationError):item(r)
    def test_pairing_approval_required(self):
        r=good();r["configurations"][0]["approvals"]["pairing_verified"]=False
        with self.assertRaises(PublicationError):item(r)
    def test_duplicate_id_rejected(self):
        with self.assertRaises(PublicationError):build([good(),good()])
    def test_sensitive_variant_rejected(self):
        r=good();r["variant"]="private@example.com"
        with self.assertRaises(PublicationError):item(r)
    def test_malformed_configurations_fail_clean(self):
        r=good();r["configurations"]=None
        with self.assertRaises(PublicationError):item(r)
    def test_sensitive_contact_rejected(self):
        r=good();r["model"]="customer@example.com"
        with self.assertRaises(PublicationError):item(r)
if __name__=="__main__":unittest.main()
