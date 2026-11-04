#!/usr/bin/env python3
"""Create public-only manifests after deliberate, individual approval. No automatic publishing."""
import argparse
from datetime import date, datetime, timezone, timedelta
import json
from pathlib import Path
import re

class PublicationError(ValueError): pass

INDUSTRIES={"firearm-services","automotive","construction","fabrication","other"}
ID=re.compile(r"^[A-Za-z0-9_-]{12,64}$")
IMAGE=re.compile(r"^assets/approved/[A-Za-z0-9/_-]+\.(png|jpg|jpeg|webp)$")
EMAIL=re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE=re.compile(r"\b(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")

def field(obj,key,limit=150):
    value=obj.get(key)
    if not isinstance(value,str) or not value.strip() or len(value.strip())>limit:
        raise PublicationError("Missing/invalid public field: "+key)
    value=" ".join(value.split())
    if EMAIL.search(value) or PHONE.search(value):
        raise PublicationError("Contact information not permitted in "+key)
    return value

def date_field(obj,key):
    try:
        return date.fromisoformat(field(obj,key,10))
    except ValueError as exc:
        raise PublicationError("Invalid date: "+key) from exc

def public_id(obj):
    value=field(obj,"public_id",64)
    if not ID.fullmatch(value):
        raise PublicationError("Use a separately assigned opaque public_id")
    return value

def portfolio(r):
    if r.get("published") is not True:return None
    a=r.get("approvals",{})
    if not isinstance(a,dict) or not all(a.get(k) is True for k in ("client","professional","publication","content_review")):
        raise PublicationError("Portfolio requires separate client, professional and publication approvals")
    if date_field(a,"reviewed_at")>date.today():
        raise PublicationError("Future approval")
    if r.get("industry") not in INDUSTRIES:
        raise PublicationError("Industry must be supported")
    image=r.get("cover_image")
    if image is not None:
        if a.get("media_rights") is not True or not isinstance(image,str) or not IMAGE.fullmatch(image) or ".." in image:
            raise PublicationError("Image must be rights-approved and on-site under assets/approved/")
    before=r.get("before_image")
    after=r.get("after_image")
    if before is not None or after is not None:
        if not isinstance(before,str) or not isinstance(after,str):
            raise PublicationError("Before/after requires two approved images")
        if a.get("media_rights") is not True or a.get("before_after_publication") is not True or a.get("before_after_alignment") is not True:
            raise PublicationError("Before/after requires rights, specific client consent and alignment review")
        if any((not IMAGE.fullmatch(p) or ".." in p) for p in (before,after)):
            raise PublicationError("Before/after images must reside under assets/approved")
    return {
        "public_id":public_id(r),"published":True,"industry":r["industry"],
        "business_name":field(r,"business_name",100),"title":field(r,"title",150),
        "service":field(r,"service",90),"summary":field(r,"public_summary",900),
        "location_label":field(r,"location_label",100),
        "completed_period":field(r,"completed_period",50),
        "verification_label":field(r,"verification_label",90),"cover_image":image,
        "before_image":before,"after_image":after,
    }

def ffl(r,today=None):
    if r.get("published") is not True:return None
    today=today or date.today()
    if r.get("acceptance_confirmed") is not True or r.get("public_listing_approved") is not True:
        raise PublicationError("Dealer must confirm acceptance and approve public listing")
    accepted=date_field(r,"acceptance_checked_at")
    verified=date_field(r,"license_checked_at")
    if any((d>today or today-d>timedelta(days=maxdays)) for d,maxdays in ((accepted,60),(verified,30))):
        raise PublicationError("Dealer confirmation/license check expired or future-dated")
    state=field(r,"state",2).upper()
    zip_code=field(r,"zip",5)
    if not re.fullmatch(r"[A-Z]{2}",state) or not re.fullmatch(r"\d{5}",zip_code):
        raise PublicationError("State/ZIP invalid")
    return {
        "public_id":public_id(r),"published":True,"acceptance_confirmed":True,
        "business_name":field(r,"business_name",100),
        "city":field(r,"city",100),"state":state,"zip":zip_code,
        "acceptance_checked_at":accepted.isoformat(),
        "transfer_policy_summary":field(r,"transfer_policy_summary",400),
    }

def build(source,mode):
    if not isinstance(source,list):raise PublicationError("Input must be a JSON array")
    fn=portfolio if mode=="portfolio" else ffl
    items=[];seen=set()
    for number,row in enumerate(source,1):
        if not isinstance(row,dict):raise PublicationError("Invalid record "+str(number))
        try:item=fn(row)
        except PublicationError as err:raise PublicationError("Record "+str(number)+": "+str(err)) from err
        if item is None:continue
        if item["public_id"] in seen:raise PublicationError("Duplicate public ID")
        seen.add(item["public_id"]);items.append(item)
    items.sort(key=lambda r:(r["business_name"].casefold(),r["public_id"]))
    return {
        "schema":"passport.public.v1" if mode=="portfolio" else "ffl.partners.public.v1",
        "as_of":datetime.now(timezone.utc).isoformat(),
        "coverage":"Only independently approved public entries. Dealer transfers require reconfirmation.",
        "items":items
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode",choices=["portfolio","ffl"],required=True)
    parser.add_argument("--input",required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--publish",action="store_true")
    args=parser.parse_args()
    if not args.publish:parser.error("Explicit --publish required after human review")
    src=Path(args.input).resolve();dst=Path(args.output).resolve()
    if src==dst:parser.error("Input and output must be different")
    try:result=build(json.loads(src.read_text(encoding="utf-8")),args.mode)
    except (OSError,ValueError) as err:parser.error(str(err))
    dst.parent.mkdir(parents=True,exist_ok=True)
    temp=dst.with_suffix(dst.suffix+".tmp")
    temp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    temp.replace(dst)
    print("Sanitized public records:",len(result["items"]))
    print("Review the output before any separate GitHub commit/deployment.")

if __name__=="__main__":main()
