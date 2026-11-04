#!/usr/bin/env python3
"""Consent- and rights-gated publisher for exact-product public showroom media.

Curate input OFFLINE outside the public repository. This command never imports
private supplier feeds. It only exports allowlisted fields with explicit
publication approval; publication itself still requires a separate reviewed commit.
"""
import argparse
from datetime import date,datetime,timezone
import json
from pathlib import Path
import re

class PublicationError(ValueError):
    pass

ID=re.compile(r"^[a-zA-Z0-9_-]{12,64}$")
ASSET=re.compile(r"^assets/approved/showroom/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+\.(?:png|jpe?g|webp)$",re.I)
DATE=re.compile(r"^\d{4}-\d{2}-\d{2}$")
CONTACT=re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\b(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")
def txt(obj,key,limit=160):
    value=obj.get(key)
    if not isinstance(value,str) or not value.strip() or len(value.strip())>limit:
        raise PublicationError("Missing or invalid field: "+key)
    value=" ".join(value.split())
    if CONTACT.search(value):raise PublicationError("Contact/PII in public field: "+key)
    return value
def public_id(obj,key="id"):
    value=txt(obj,key,64)
    if not ID.fullmatch(value):raise PublicationError("Public ID must be an opaque 12-64 char identifier")
    return value
def approval(obj,*fields):
    a=obj.get("approvals")
    if not isinstance(a,dict) or any(a.get(f) is not True for f in fields):
        raise PublicationError("Missing required independent publication approval: "+", ".join(fields))
    return a
def asset(obj):
    path=txt(obj,"src",180)
    if ".." in path or not ASSET.fullmatch(path):
        raise PublicationError("Only local approved showroom PNG/JPEG/WebP images are allowed")
    return path
def frames(arr):
    if not isinstance(arr,list) or len(arr)<2 or len(arr)>48:
        raise PublicationError("Each configuration requires 2-48 approved image angles")
    out=[]
    for f in arr:
        if not isinstance(f,dict):raise PublicationError("Malformed media frame")
        out.append({"angle":txt(f,"angle",50),"src":asset(f),"alt":txt(f,"alt",200)})
    if len({x["angle"] for x in out})!=len(out):
        raise PublicationError("Duplicate angle")
    return out
def day(obj,key):
    value=txt(obj,key,10)
    if not DATE.fullmatch(value):raise PublicationError("Invalid ISO date")
    try:d=date.fromisoformat(value)
    except ValueError as e:raise PublicationError("Invalid calendar date") from e
    if d>date.today():raise PublicationError("Future review date")
    return value
def item(record):
    if not isinstance(record,dict):raise PublicationError("Record must be an object")
    if record.get("status")!="published":return None
    approval(record,"owner_publication","exact_identity","media_rights","content_review")
    base=frames(record.get("frames"))
    out={
      "id":public_id(record),"status":"published",
      "publication_approved":True,"exact_identity_verified":True,"rights":"approved",
      "manufacturer":txt(record,"manufacturer",100),
      "model":txt(record,"model",120),
      "variant":txt(record,"variant",100) if isinstance(record.get("variant"),str) and record.get("variant").strip() else "",
      "rights_source":txt(record,"rights_source",160),
      "identity_evidence_label":txt(record,"identity_evidence_label",160),
      "checked_at":day(record,"checked_at"),
      "frames":base,
      "configurations":[]
    }
    raw_configurations=record.get("configurations",[])
    if not isinstance(raw_configurations,list):raise PublicationError("Configurations must be an array")
    config_ids=set()
    for config in raw_configurations:
        if not isinstance(config,dict):raise PublicationError("Malformed configuration")
        if config.get("status")!="published":continue
        approval(config,"owner_publication","media_rights","exact_accessory","pairing_verified","image_alignment")
        cid=public_id(config)
        if cid in config_ids:raise PublicationError("Duplicate configuration ID")
        config_ids.add(cid)
        media=frames(config.get("frames"))
        if [f["angle"] for f in media]!=[f["angle"] for f in base]:
            raise PublicationError("Configuration images must match exact base angles and sequence")
        out["configurations"].append({
          "id":cid,"label":txt(config,"label",120),
          "publication_approved":True,"media_rights_approved":True,
          "exact_accessory_verified":True,"pairing_verified":True,
          "alignment_reviewed":True,
          "pairing_evidence_label":txt(config,"pairing_evidence_label",160),
          "frames":media
        })
    if len(out["configurations"])>24:raise PublicationError("Maximum 24 approved configurations")
    return out
def build(rows):
    if not isinstance(rows,list) or len(rows)>200:raise PublicationError("Source must be array of 0-200 curated records")
    out=[];ids=set()
    for row in rows:
        entry=item(row)
        if entry is None:continue
        if entry["id"] in ids:raise PublicationError("Duplicate product public ID")
        ids.add(entry["id"]);out.append(entry)
    return {"schema":"area33.showroom.v1",
            "as_of":datetime.now(timezone.utc).isoformat(),
            "coverage":"Only manually approved exact-product public media.",
            "items":out}

def check_media_files(payload,root):
    # Structural validity alone is not enough. All referenced files must exist.
    for item in payload["items"]:
        allframes=[item["frames"]]+[c["frames"] for c in item["configurations"]]
        for frameset in allframes:
            for frame in frameset:
                path=root / frame["src"]
                if not path.is_file():raise PublicationError("Referenced approved media file missing: "+frame["src"])
                if path.stat().st_size>18_000_000 or path.stat().st_size<12:raise PublicationError("Invalid media file size")
                sig=path.open("rb").read(16)
                ext=path.suffix.lower()
                if ext==".png" and sig[:8]!=b"\x89PNG\r\n\x1a\n":raise PublicationError("Media format mismatch")
                if ext in (".jpg",".jpeg") and sig[:3]!=b"\xff\xd8\xff":raise PublicationError("Media format mismatch")
                if ext==".webp" and not(sig[:4]==b"RIFF" and sig[8:12]==b"WEBP"):raise PublicationError("Media format mismatch")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",required=True,help="Privately curated input JSON, never in public GitHub")
    p.add_argument("--output",default="assets/showroom-public.json")
    p.add_argument("--publish",action="store_true")
    args=p.parse_args()
    if not args.publish:p.error("Manual --publish flag required")
    root=Path(__file__).resolve().parent.parent
    inp=Path(args.input).resolve()
    out=Path(args.output).resolve()
    if inp==out:p.error("Input and public output must differ")
    if root in inp.parents:p.error("Private approval input must be outside the public site repository")
    if out!=root/"assets/showroom-public.json":p.error("Public output must be assets/showroom-public.json")
    try:
        payload=build(json.loads(inp.read_text(encoding="utf-8")))
        check_media_files(payload,root)
    except (PublicationError,OSError,ValueError) as err:p.error(str(err))
    temp=out.with_suffix(".json.tmp")
    temp.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    temp.replace(out)
    print("Public showroom media sets prepared:",len(payload["items"]))
    print("IMPORTANT: Review sanitized output and image licensing before a separate Git commit.")

if __name__=="__main__":main()
