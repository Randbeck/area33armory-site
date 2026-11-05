#!/usr/bin/env python3
"""Generate a PRIVATE local owner-review page; never publish catalog records.

The page runs offline in a browser. Edits exist only in browser memory until
the owner explicitly downloads a private JSON progress/export file.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parents[1]
ID = re.compile(r"^catalog_[a-f0-9]{20}$")
HASH = re.compile(r"^[a-f0-9]{64}$")
CHECKS = ("exact_identity", "media_rights", "content_review",
          "offered_for_sale", "owner_publication")


class ReviewError(ValueError):
    pass


def validate_source(data_file: Path) -> tuple[list[dict], list[list[str]]]:
    data_file = data_file.expanduser().resolve()
    if data_file == HERE or data_file.is_relative_to(HERE):
        raise ReviewError("Private approval file must be outside website checkout")
    if any((p / ".git").exists() for p in (data_file, *data_file.parents)):
        raise ReviewError("Private approval file must be outside Git repositories")
    rows = json.loads(data_file.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        raise ReviewError("Expected 1-100 owner review records")
    seen, previews = set(), []
    for item in rows:
        if not isinstance(item, dict) or not ID.fullmatch(str(item.get("id") or "")):
            raise ReviewError("Invalid private candidate ID")
        if item["id"] in seen:
            raise ReviewError("Duplicate public item ID")
        seen.add(item["id"])
        if item.get("status") not in ("draft", "published"):
            raise ReviewError("Unrecognized review status")
        checks = item.get("approvals")
        if not isinstance(checks, dict) or set(checks) != set(CHECKS):
            raise ReviewError("Incomplete approval checklist")
        if any(type(v) is not bool for v in checks.values()):
            raise ReviewError("Invalid approval values")
        frames = item.get("photos")
        if not isinstance(frames, list) or not 1 <= len(frames) <= 8:
            raise ReviewError("Expected 1-8 original JPEGs per item")
        photos = []
        for frame in frames:
            if not isinstance(frame, dict):
                raise ReviewError("Invalid photo metadata")
            original = frame.get("source_path")
            if not isinstance(original, str) or not original:
                raise ReviewError("Missing local private photo")
            source = Path(original).expanduser().resolve()
            if Path(original).is_symlink() or source.is_symlink() or not source.is_file():
                raise ReviewError("Missing or symlinked local photo")
            if source == HERE or source.is_relative_to(HERE) or source.suffix.lower() not in (".jpg", ".jpeg"):
                raise ReviewError("Photo must be a private original JPEG")
            digest = frame.get("source_sha256")
            if (not isinstance(digest, str) or not HASH.fullmatch(digest)
                    or source.stat().st_size > 12000000
                    or hashlib.sha256(source.read_bytes()).hexdigest() != digest):
                raise ReviewError("Source photograph changed since review")
            photos.append(source.as_uri())
        previews.append(photos)
    return rows, previews


HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Area 33 | PRIVATE product approvals</title>
<style>
:root{--ink:#171717;--line:#ddd;--muted:#5d5d5d}
*{box-sizing:border-box}body{margin:0;background:#f4f4f4;color:var(--ink);font:15px/1.5 "Segoe UI",system-ui,sans-serif}
header{background:#111;color:white;padding:32px 0}main,header .inner{width:min(1120px,calc(100% - 36px));margin:auto}
header small{color:#ff8289;letter-spacing:.12em;font-weight:700}h1{margin:5px 0;font-size:33px;letter-spacing:-.04em}
header p{color:#ddd;margin:0}.toolbar{display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;margin:23px 0}
button{border:1px solid #222;border-radius:8px;padding:11px 14px;font:inherit;cursor:pointer;background:#181818;color:white}
button.secondary{background:white;color:#222;border-color:#aaa}
button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #b82734;outline-offset:2px}
.warning{padding:14px;border-left:3px solid #bc343a;background:#fff6f3;margin:18px 0}
.card{background:white;border:1px solid var(--line);padding:22px;border-radius:16px;margin:20px 0}
.head{display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;align-items:start}.head h2{margin:0;font-size:22px}
.status{border:1px solid #bbb;border-radius:99px;padding:5px 12px;font-size:12px}
.muted,.caption{color:var(--muted);font-size:13px}
.photos{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:14px 0 20px}
figure{margin:0;border-radius:10px;background:#f7f7f7;padding:10px}
figure img{width:100%;height:190px;object-fit:contain;display:block}
.fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px}
label{font-size:13px;font-weight:650;display:grid;gap:5px}
input:not([type=checkbox]),select{font:inherit;width:100%;border:1px solid #aaa;border-radius:7px;padding:9px;background:white}
fieldset{border:1px solid #ddd;border-radius:9px;margin:18px 0;padding:14px}legend{font-weight:700}
.check{display:flex;align-items:start;gap:10px;font-weight:500;margin:10px 0}
.check input{margin-top:4px;accent-color:#222}.actions{display:flex;gap:9px;align-items:center;flex-wrap:wrap}
footer{max-width:1120px;margin:40px auto;color:var(--muted);padding:0 20px 30px}
@media(max-width:700px){.fields{grid-template-columns:1fr}}
</style></head><body>
<header><div class="inner"><small>AREA 33 / PRIVATE OWNER REVIEW</small>
<h1>Product approval workspace</h1>
<p>Review exact source models, photographs, image rights and actual products offered for sale.</p></div></header>
<main><div class="toolbar"><div><strong id="count">Loading…</strong>
<p class="muted">Changes are not saved unless you explicitly export a private JSON file.</p></div>
<div><button class="secondary" id="save">Save private progress</button>
<button id="export">Export approved items only</button></div></div>
<p class="warning">SKU/UPC matching alone does not approve a listing. Keep the five owner confirmations unchecked until you've verified each fact. No products or photos are published by this page.</p>
<div id="records"></div></main>
<footer>This page runs offline and does not make network requests. Keep private JSON and source photographs out of GitHub.</footer>
<script id="data" type="application/json">__PRIVATE_DATA__</script>
<script id="previews" type="application/json">__PRIVATE_PREVIEWS__</script>
<script>
"use strict";
const data=JSON.parse(document.getElementById("data").textContent);
const previews=JSON.parse(document.getElementById("previews").textContent);
const CHECKS=[
 ["exact_identity","I independently verified the exact model, variant and any claimed fit."],
 ["media_rights","I confirmed the image rights permit this product-for-sale display."],
 ["content_review","I visually reviewed every image and its description."],
 ["offered_for_sale","Area 33 is actually offering this exact product for sale."],
 ["owner_publication","I explicitly authorize this item for a separate publication review."]
];
const required=["manufacturer","model","category","rights_source","identity_evidence_label","source_checked_at"];
function node(tag,text){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;}
function ready(item){
 const date=String(item.source_checked_at||"");
 return required.every(k=>String(item[k]||"").trim()) &&
  ["complete","part","accessory","ammunition","other"].includes(item.product_type) &&
  /^\d{4}-\d\d-\d\d$/.test(date)&&Number.isFinite(Date.parse(date+"T00:00:00Z")) &&
  item.photos.every(p=>String(p.alt||"").trim())&&
  CHECKS.every(([k])=>item.approvals[k]===true);
}
function refresh(){
 const approved=data.filter(item=>item.status==="published"&&ready(item)).length;
 document.getElementById("count").textContent=approved+" of "+data.length+" ready for PRIVATE handoff";
}
function download(filename,rows){
 const object=new Blob([JSON.stringify(rows,null,2)+"\n"],{type:"application/json"});
 const url=URL.createObjectURL(object),a=node("a");
 a.download=filename;a.href=url;a.click();
 setTimeout(()=>URL.revokeObjectURL(url),1000);
}
document.getElementById("save").addEventListener("click",()=>download("catalog-private-progress.json",data));
document.getElementById("export").addEventListener("click",()=>{
 const approved=data.filter(item=>item.status==="published"&&ready(item));
 if(!approved.length){alert("No fully reviewed items. Save private progress instead.");return;}
 if(!confirm("Export "+approved.length+" reviewed items to a private JSON file? This does NOT publish any site listing."))return;
 download("catalog-owner-approved-private.json",approved);
});
for(let i=0;i<data.length;i++){
 const item=data[i],section=node("section");section.className="card";
 const head=node("div");head.className="head";
 const title=node("h2",[item.manufacturer,item.model,item.variant].filter(Boolean).join(" "));
 const status=node("span",(item.status==="published"&&ready(item))?"Review complete — PRIVATE only":"Draft — not approved");status.className="status";
 head.append(title,status);section.append(head);
 section.append(node("p","Product "+(i+1)+" of "+data.length+" — source title must be verified."));
 const gallery=node("div");gallery.className="photos";
 function edited(){item.status="draft";status.textContent="Draft — not approved";refresh();}
 for(let j=0;j<item.photos.length;j++){
  const photo=item.photos[j],fig=node("figure"),img=node("img");
  img.src=previews[i][j];img.alt="Original source photo "+(j+1);
  img.loading="lazy";img.referrerPolicy="no-referrer";fig.append(img);
  fig.append(node("p","Original source photo "+(j+1)));
  const label=node("label","Describe this exact view");
  const input=node("input");input.type="text";input.maxLength=160;
  input.value=photo.alt||"";input.placeholder="Actual visible details";
  input.addEventListener("input",()=>{photo.alt=input.value;edited();});
  label.append(input);fig.append(label);gallery.append(fig);
 }
 section.append(gallery);
 const fields=node("div");fields.className="fields";
 function field(key,text,type="text"){
  const label=node("label",text),input=node("input");
  input.type=type;input.value=item[key]||"";input.maxLength=160;
  input.addEventListener("input",()=>{item[key]=input.value;edited();});
  label.append(input);fields.append(label);
 }
 field("manufacturer","Manufacturer — independently verify");
 field("model","Exact model — independently verify");
 field("variant","Variant and fit (only if verified)");
 field("description","Proposed public description — verify source claims");
 field("category","Public category");
 const typeLabel=node("label","Product type"),select=node("select");
 for(const [value,label] of [["","Choose type"],["accessory","Accessory"],["complete","Complete product"],["part","Part"],["ammunition","Ammunition"],["other","Other"]]){
  const option=node("option",label);option.value=value;select.append(option);
 }
 select.value=item.product_type||"";
 select.addEventListener("change",()=>{item.product_type=select.value;edited();});
 typeLabel.append(select);fields.append(typeLabel);
 field("source_checked_at","Date evidence verified","date");
 field("identity_evidence_label","Exact identity evidence and reference");
 field("rights_source","Specific image-rights source or authorization");
 section.append(fields);
 const fieldset=node("fieldset");fieldset.append(node("legend","Five independent owner confirmations"));
 for(const [key,desc] of CHECKS){
  const label=node("label");label.className="check";
  const cb=node("input");cb.type="checkbox";cb.checked=item.approvals[key]===true;
  cb.addEventListener("change",()=>{item.approvals[key]=cb.checked;edited();});
  label.append(cb,node("span",desc));fieldset.append(label);
 }
 section.append(fieldset);
 const actions=node("div");actions.className="actions";
 const approve=node("button","Confirm product review");approve.type="button";
 approve.addEventListener("click",()=>{
  if(!ready(item)){alert("Complete the evidence, photo descriptions and all five owner confirmations first.");return;}
  if(!confirm("Confirm that you personally reviewed this exact product, photo rights and sale listing?"))return;
  item.status="published";status.textContent="Review complete — PRIVATE only";refresh();
 });
 const hold=node("button","Hold as draft");hold.className="secondary";hold.type="button";
 hold.addEventListener("click",edited);
 actions.append(approve,hold);section.append(actions);
 document.getElementById("records").append(section);
}
refresh();
</script></body></html>"""


def make_review(input_file: Path) -> Path:
    rows, previews = validate_source(input_file)
    dest = input_file.expanduser().resolve().parent / "catalog-owner-review.html"
    if dest.exists():
        raise ReviewError("Local review page already exists; refusing overwrite")
    def as_inline_json(value):
        return (json.dumps(value, ensure_ascii=True)
                .replace("<", "\\u003c").replace(">", "\\u003e")
                .replace("&", "\\u0026"))
    html = HTML.replace("__PRIVATE_DATA__", as_inline_json(rows)).replace(
        "__PRIVATE_PREVIEWS__", as_inline_json(previews))
    dest.write_text(html, encoding="utf-8")
    return dest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path,
                        help="Private catalog approval JSON outside GitHub")
    args = parser.parse_args()
    try:
        dest = make_review(args.input)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print("PRIVATE owner review page created: " + str(dest))
    print("All records retain their initial approval state; nothing is published.")


if __name__ == "__main__":
    main()
