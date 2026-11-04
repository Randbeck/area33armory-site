import unittest
from datetime import date,timedelta
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from publish_public_directories import portfolio,ffl,build,PublicationError
def sample_portfolio():
    return {"published":True,"public_id":"portfolio_abc12345","industry":"construction",
            "business_name":"Sample workshop","title":"Test project","service":"Repair",
            "public_summary":"Approved test text","location_label":"Example city",
            "completed_period":"2026","verification_label":"Shop reported",
            "cover_image":None,"secret_customer":"PRIVATE","serial_number":"PRIVATE",
            "approvals":{"client":True,"professional":True,"publication":True,
                         "content_review":True,"reviewed_at":date.today().isoformat()}}
def sample_ffl():
    return {"published":True,"public_id":"transfer_abc12345","acceptance_confirmed":True,
            "public_listing_approved":True,"license_checked_at":date.today().isoformat(),
            "acceptance_checked_at":date.today().isoformat(),"business_name":"Example dealer",
            "city":"Example City","state":"MO","zip":"63640",
            "transfer_policy_summary":"Call for current terms","full_license":"SECRET"}
class Tests(unittest.TestCase):
    def test_portfolio_public_allowlist(self):
        out=portfolio(sample_portfolio())
        self.assertNotIn("secret_customer",out)
        self.assertNotIn("serial_number",out)
        self.assertNotIn("approvals",out)
    def test_unpublished_hidden(self):
        r=sample_portfolio();r["published"]=False
        self.assertEqual(build([r],"portfolio")["items"],[])
    def test_client_consent(self):
        r=sample_portfolio();r["approvals"]["client"]=False
        with self.assertRaises(PublicationError):portfolio(r)
    def test_photo_rights(self):
        r=sample_portfolio();r["cover_image"]="https://example.com/photo.jpg"
        with self.assertRaises(PublicationError):portfolio(r)
    def test_no_private_contact(self):
        r=sample_portfolio();r["public_summary"]="client@example.com"
        with self.assertRaises(PublicationError):portfolio(r)
    def test_valid_partner_allowlist(self):
        out=ffl(sample_ffl())
        self.assertNotIn("full_license",out)
        self.assertNotIn("license_checked_at",out)
    def test_stale_license(self):
        r=sample_ffl();r["license_checked_at"]=(date.today()-timedelta(days=31)).isoformat()
        with self.assertRaises(PublicationError):ffl(r)
    def test_stale_acceptance(self):
        r=sample_ffl();r["acceptance_checked_at"]=(date.today()-timedelta(days=61)).isoformat()
        with self.assertRaises(PublicationError):ffl(r)
    def test_unconfirmed_transfer(self):
        r=sample_ffl();r["acceptance_confirmed"]=False
        with self.assertRaises(PublicationError):ffl(r)
    def test_duplicate(self):
        with self.assertRaises(PublicationError):build([sample_portfolio(),sample_portfolio()],"portfolio")
if __name__=="__main__":unittest.main()
