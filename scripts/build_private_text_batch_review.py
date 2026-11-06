#!/usr/bin/env python3
"""Build an OFFLINE PRIVATE focused reviewer for text-only Area 33 drafts.

The review page is deliberately local; no URLs, images, supplier descriptions,
live inventory or approval flags are generated. The reviewer individually
confirms each record, then explicitly downloads private progress or approvals.
Identity exceptions are read-only and never become product drafts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from build_private_catalog_review import validate_source, ReviewError, HERE

EXCEPTION_SCHEMA="randbeck.area33.private_catalog_bridge_report.v1"
MAX_HTML_BYTES=12_000_000
CHECKS={"exact_identity","content_review","offered_for_sale","owner_publication"}


def _private_file(path:Path)->Path:
    original=Path(path).expanduser()
    value=original.resolve()
    if (original.is_symlink() or not value.is_file()
            or value.stat().st_size > 8_000_000 or
            value==HERE or value.is_relative_to(HERE)
            or any((p/".git").exists() for p in (value,*value.parents))):
        raise ReviewError("Review inputs must be ordinary small PRIVATE files outside Git")
    return value


def source_batch(draft_file:Path,exceptions_file:Path)->tuple[list[dict],list[dict]]:
    draft_file=_private_file(draft_file)
    exceptions_file=_private_file(exceptions_file)
    rows,previews=validate_source(draft_file)
    for row,images in zip(rows,previews):
        if (row.get("listing_mode")!="text_only" or row.get("photos")!=[]
                or images or row.get("rights_source","")!=""
                or row["approvals"]["media_rights"] is not False
                or row.get("status") not in ("draft","published")):
            raise ReviewError("Batch reviewer accepts only zero-image text-only drafts")
    report=json.loads(exceptions_file.read_text(encoding="utf-8"))
    if (not isinstance(report,dict) or report.get("schema")!=EXCEPTION_SCHEMA
            or report.get("publication_enabled") is not False
            or type(report.get("review_drafts_generated")) is not int
            or type(report.get("quarantined_identity_or_media_groups")) is not int
            or not isinstance(report.get("exceptions"),list)
            or len(report["exceptions"])>200):
        raise ReviewError("Unrecognized private bridge identity exception report")
    if report["review_drafts_generated"]!=len(rows):
        raise ReviewError("Draft count and identity exception report do not agree")
    if report["quarantined_identity_or_media_groups"]!=len(report["exceptions"]):
        raise ReviewError("Exception count and identity report disagree")
    exceptions=[]
    for entry in report["exceptions"]:
        if (not isinstance(entry,dict)
                or entry.get("owner_review_required") is not True
                or entry.get("publication_approved") is not False
                or not isinstance(entry.get("reasons"),list)
                or not entry["reasons"]
                or not isinstance(entry.get("source_skus"),list)):
            raise ReviewError("An identity exception has unexpected approval state")
        exceptions.append({
            "manufacturer":str(entry.get("manufacturer") or "")[:100],
            "model":str(entry.get("model") or "")[:120],
            "reasons":[str(x)[:150] for x in entry["reasons"]][:20],
            "source_skus":[str(x)[:64] for x in entry["source_skus"]][:20],
        })
    return rows,exceptions


def validated_private_evidence(
    evidence_file:Path, draft_file:Path, exception_file:Path, rows:list[dict],
)->list[dict]:
    evidence_file=_private_file(evidence_file)
    payload=json.loads(evidence_file.read_text(encoding="utf-8"))
    expected={
        "schema","source","source_staging_sha256","source_drafts_sha256",
        "source_exceptions_sha256","candidate_count",
        "held_identity_exception_count","evidence","publication_approved",
        "media_rights_approved","source_offer_verified","note",
    }
    if (not isinstance(payload,dict) or set(payload)!=expected
            or payload["schema"]!="area33.catalog.private_identity_evidence.v1"
            or payload["source"]!="RSR"
            or payload["publication_approved"] is not False
            or payload["media_rights_approved"] is not False
            or payload["source_offer_verified"] is not False
            or type(payload["candidate_count"]) is not int
            or payload["candidate_count"]!=len(rows)
            or payload["source_drafts_sha256"]!=hashlib.sha256(
                _private_file(draft_file).read_bytes()
            ).hexdigest()
            or payload["source_exceptions_sha256"]!=hashlib.sha256(
                _private_file(exception_file).read_bytes()
            ).hexdigest()
            or not isinstance(payload["evidence"],list)
            or len(payload["evidence"])!=len(rows)):
        raise ReviewError("Private source evidence does not match unchanged owner-review drafts")
    expected_ids={item["id"] for item in rows}
    matched={}
    by_id={item["id"]:item for item in rows}
    for entry in payload["evidence"]:
        if (not isinstance(entry,dict) or set(entry)!={
                "id","recorded_upc","recorded_manufacturer_part_number",
                "recorded_source_skus","recorded_category","recorded_manufacturer",
                "recorded_model","neutral_draft_suggestion","evidence_status"
            } or entry.get("id") not in expected_ids
                or entry["id"] in matched):
            raise ReviewError("Unrecognized or duplicated private evidence identity")
        item=by_id[entry["id"]]
        if (entry["recorded_manufacturer"]!=item["manufacturer"]
                or entry["recorded_model"]!=item["model"]
                or entry["recorded_category"]!=item["category"]
                or not isinstance(entry["recorded_upc"],str)
                or not re.fullmatch(r"\d{12,14}",entry["recorded_upc"])
                or not isinstance(entry["recorded_manufacturer_part_number"],str)
                or not 1<=len(entry["recorded_manufacturer_part_number"])<=120
                or not isinstance(entry["recorded_source_skus"],list)
                or not entry["recorded_source_skus"]
                or not all(isinstance(k,str) and 1<=len(k)<=64
                           for k in entry["recorded_source_skus"])
                or not isinstance(entry["neutral_draft_suggestion"],str)
                or len(entry["neutral_draft_suggestion"])>200
                or entry["evidence_status"]!=
                    "RSR source identity only — not independently verified"):
            raise ReviewError("Private source evidence conflicts with approved-only draft identity")
        matched[entry["id"]]=entry
    if set(matched)!=expected_ids:
        raise ReviewError("Missing or extra private evidence entries")
    return [matched[row["id"]] for row in rows]


def inline(value)->str:
    return (json.dumps(value,ensure_ascii=True)
            .replace("<",r"\u003c").replace(">",r"\u003e")
            .replace("&",r"\u0026").replace("\u2028",r"\u2028")
            .replace("\u2029",r"\u2029"))


HTML=r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Area 33 | Private batch product review</title>
<style>
:root{--ink:#161616;--muted:#666;--line:#dedede;--bg:#f5f5f5}
*{box-sizing:border-box}body{margin:0;font:14px/1.5 system-ui,"Segoe UI",sans-serif;color:var(--ink);background:var(--bg)}
header{background:#111;color:white;padding:22px max(20px,calc((100vw - 1350px)/2))}
header .eyebrow{font-size:11px;letter-spacing:.15em;color:#bdbdbd;font-weight:800}
h1{font-size:26px;margin:4px 0;letter-spacing:-.04em}header p{color:#ddd;margin:0}
button,input,select,textarea{font:inherit}button{cursor:pointer;border:1px solid #bbb;border-radius:8px;padding:9px 12px;background:white;color:var(--ink)}
button.primary{background:#151515;color:white;border-color:#151515}
button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:3px solid #333;outline-offset:2px}
.top{width:min(1350px,calc(100% - 32px));margin:18px auto;display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between}
.counts{display:flex;gap:10px;flex-wrap:wrap}.stat{background:white;border:1px solid var(--line);border-radius:10px;padding:10px 15px;min-width:130px}
.stat strong{font-size:20px;display:block}.stat span{color:var(--muted);font-size:12px}
.tools{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.tools label{cursor:pointer;background:white;border:1px solid #bbb;border-radius:8px;padding:9px 12px}
#resume{position:absolute;width:1px;height:1px;opacity:0;overflow:hidden}
.notice{width:min(1350px,calc(100% - 32px));margin:10px auto 17px;background:#fff;padding:13px 16px;border-left:3px solid #333}
.shell{display:grid;grid-template-columns:minmax(245px,310px) minmax(0,1fr);gap:16px;width:min(1350px,calc(100% - 32px));margin:0 auto 40px}
nav,.workspace{background:white;border:1px solid var(--line);border-radius:14px;min-width:0}
nav{padding:14px;position:sticky;top:10px;align-self:start;max-height:calc(100vh - 24px);display:flex;flex-direction:column}
nav h2{font-size:16px;margin:0 0 10px}
nav input,nav select{width:100%;margin:0 0 8px;border:1px solid #aaa;border-radius:7px;padding:9px}
#items{overflow-y:auto;min-height:140px}
.product{display:block;text-align:left;width:100%;margin:4px 0;padding:10px;border-color:transparent;background:#f7f7f7}
.product.active{border-color:#151515;background:white}
.product strong{display:block;overflow-wrap:anywhere}
.product small{color:var(--muted);display:block;line-height:1.45;margin-top:3px;overflow-wrap:anywhere}
.workspace{padding:clamp(16px,3vw,30px)}
.source-evidence{border:1px solid #bbb;border-radius:12px;padding:16px;background:#fafafa;margin:18px 0}
.source-evidence h3{font-size:16px;margin:0 0 12px}
.evidence-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.evidence-item{display:grid;gap:4px;min-width:0;overflow-wrap:anywhere}
.evidence-item strong{font-size:12px}.evidence-item span{font-size:13px}
.suggestion{padding:14px;background:white;border:1px solid #ddd;border-radius:10px;margin:14px 0}
.suggestion p{margin:8px 0}
.research{border:1px solid #ddd;border-radius:12px;padding:16px;margin:18px 0}
.research h3{font-size:16px;margin:0 0 10px}
.research p{overflow-wrap:anywhere}
.research a{color:inherit;text-decoration:underline;overflow-wrap:anywhere}
.research-source{padding:12px 0;border-top:1px solid #e3e3e3}
.research-source strong{display:block}
.research-fields{display:grid;grid-template-columns:minmax(170px,1fr) minmax(200px,2fr);gap:8px;margin:12px 0}
.research-fields input,.research-fields select{min-width:0;width:100%;padding:9px;border:1px solid #aaa;border-radius:7px}
.research-source label{display:flex;align-items:flex-start;gap:8px;margin-top:6px}
.research-actions{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
@media(max-width:700px){.research-fields{grid-template-columns:1fr}}
@media(max-width:700px){.evidence-grid{grid-template-columns:1fr}}.heading{display:flex;align-items:start;justify-content:space-between;gap:15px;flex-wrap:wrap}
.heading h2{font-size:24px;line-height:1.2;letter-spacing:-.035em;margin:0}.muted{color:var(--muted)}.badge{border:1px solid #bbb;padding:4px 10px;border-radius:99px;font-size:12px;white-space:nowrap}
.mini{font-size:12px;color:var(--muted)}
.fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:20px 0}
.field{display:grid;gap:5px;min-width:0;font-weight:650}
.field input,.field select,.field textarea{width:100%;padding:10px 11px;border:1px solid #b5b5b5;border-radius:8px;background:white;font-weight:400}
.field.full{grid-column:1/-1}.field textarea{min-height:96px;resize:vertical}
.review{border:1px solid #ddd;border-radius:10px;padding:14px;margin:15px 0}
.review legend{font-weight:750;padding:0 8px}.check{display:flex;align-items:flex-start;gap:9px;margin:10px 0;cursor:pointer}
.check input{margin-top:4px;accent-color:#111}.actionbar{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:center;margin-top:18px}
.actionbar div{display:flex;flex-wrap:wrap;gap:8px}.missing{margin:10px 0;padding:10px;background:#f5f5f5;border-radius:8px;font-size:13px}
.exceptions{margin-top:30px;border-top:1px solid #ddd;padding-top:24px}.exceptions h3{font-size:17px}
.exception{padding:12px 0;border-top:1px solid #e6e6e6}.exception p{margin:4px 0}.exception code{font-size:12px;overflow-wrap:anywhere}
footer{color:var(--muted);width:min(1350px,calc(100% - 32px));margin:12px auto 40px;font-size:12px}
@media(max-width:820px){.shell{grid-template-columns:1fr}nav{position:static;max-height:300px}.fields{grid-template-columns:1fr}}
</style></head><body>
<header><span class="eyebrow">AREA 33 / OFFLINE PRIVATE WORKSPACE</span><h1>Batch product review</h1>
<p>Review one exact product at a time. No photos, supplier copy, price, stock claims or publishing.</p></header>
<div class="top"><div class="counts"><div class="stat"><strong id="total">0</strong><span>Candidates</span></div>
<div class="stat"><strong id="finished">0</strong><span>Individually reviewed</span></div>
<div class="stat"><strong id="held">0</strong><span>Held / in progress</span></div>
<div class="stat"><strong id="exceptions-count">0</strong><span>Identity exceptions</span></div></div>
<div class="tools"><button id="save" type="button">Save private progress</button>
<label for="resume">Resume saved progress</label><input type="file" accept=".json,application/json" id="resume">
<button id="research-save" type="button">Save research notes</button>
<label for="research-resume">Load research notes</label><input type="file" accept=".json,application/json" id="research-resume">
<button class="primary" id="export" type="button">Export approved-only JSON</button></div></div>
<p class="notice">This is a private review tool, not a sales authorization. Manufacturer identity, owner-written copy, legal/channel restrictions, and an actual offer for sale must each be confirmed. <strong>There is no bulk-approval button.</strong> Identity exceptions remain quarantined below. Edits are held in browser memory until you save a private JSON file.</p>
<div class="shell"><nav aria-label="Candidate list"><h2>Product queue</h2><input id="search" type="search" placeholder="Search manufacturer or model">
<select id="filter"><option value="all">All candidates</option><option value="draft">Held / not approved</option><option value="ready">Reviewed and approved</option></select>
<div id="items" role="list"></div></nav>
<main class="workspace"><div id="detail"></div>
<section class="exceptions"><div class="heading"><h3>Quarantined identity exceptions</h3>
<button id="exceptions-toggle" type="button">Show exception details</button></div>
<p class="muted">These records are informational only. They cannot be approved here, and no UPC, model or manufacturer number is invented.</p>
<div id="exceptions" hidden></div></section></main></div>
<footer>Runs locally without fetching or sending data. Keep exported JSON, source records and this generated page outside GitHub and public website folders.</footer>
<script id="review-data" type="application/json">__REVIEW_DATA__</script>
<script id="exception-data" type="application/json">__EXCEPTION_DATA__</script>
<script id="source-evidence" type="application/json">__PRIVATE_EVIDENCE__</script>
<script id="research-data" type="application/json">__PRIVATE_RESEARCH__</script>
<script>
"use strict";
let data=JSON.parse(document.getElementById("review-data").textContent);
const exceptions=JSON.parse(document.getElementById("exception-data").textContent);
const evidenceRows=JSON.parse(document.getElementById("source-evidence").textContent);
const evidenceById=new Map(evidenceRows.map(x=>[x.id,x]));
let research=JSON.parse(document.getElementById("research-data").textContent);
let researchById=new Map((research?research.items:[]).map(x=>[x.id,x]));
const researchLabels=["Magazine configuration","Carry options","Finish/color","Material",
"Compatibility","Product dimensions","Other verified attribute"];
const duplicateCounts=new Map();
for(const item of data){
 const key=[item.manufacturer,item.model].join("\x1f").toLowerCase();
 duplicateCounts.set(key,(duplicateCounts.get(key)||0)+1);
}
function isDuplicateName(item){
 return duplicateCounts.get([item.manufacturer,item.model].join("\x1f").toLowerCase())>1;
}
const byId=id=>document.getElementById(id);
const CHECKS=[
 ["exact_identity","Exact manufacturer/model/variant and identity evidence independently verified"],
 ["content_review","Original description and all product claims independently written and checked"],
 ["offered_for_sale","Area 33 can actually offer this exact product under applicable policies"],
 ["owner_publication","I individually authorize this product for a separate private publication handoff"]
];
let selected=data.length?data[0].id:null;
function node(tag,text){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;return el;}
function isReady(item){
 const approvals=item.approvals||{},date=String(item.source_checked_at||"");
 const parsed=new Date(date+"T00:00:00Z");
 return item.status==="published" && contentComplete(item) && CHECKS.every(pair=>approvals[pair[0]]===true);
}
function contentComplete(item){
 const date=String(item.source_checked_at||"");
 const parsed=new Date(date+"T00:00:00Z");
 const today=new Date().toISOString().slice(0,10);
 return item.listing_mode==="text_only" && Array.isArray(item.photos) && item.photos.length===0 &&
  item.rights_source==="" && item.approvals.media_rights===false &&
  item.content_origin==="owner_written" &&
  ["manufacturer","model","category","identity_evidence_label"].every(k=>String(item[k]||"").trim()) &&
  String(item.description||"").trim().length>=18 &&
  String(item.description||"").length<=200 &&
  ["complete","part","accessory","ammunition","other"].includes(item.product_type) &&
  /^\d{4}-\d{2}-\d{2}$/.test(date) && Number.isFinite(parsed.getTime()) &&
  parsed.toISOString().slice(0,10)===date && date<=today;
}
function missing(item){
 const parts=[];
 if(!String(item.manufacturer||"").trim()||!String(item.model||"").trim())parts.push("Exact model/manufacturer");
 if(!String(item.identity_evidence_label||"").trim())parts.push("Identity evidence");
 if(!item.source_checked_at)parts.push("Evidence review date");
 if(!String(item.category||"").trim()||!item.product_type)parts.push("Category and type");
 if(String(item.description||"").trim().length<18)parts.push("18+ characters of original description");
 if(item.content_origin!=="owner_written")parts.push("Original writing confirmation");
 for(const [k] of CHECKS)if(item.approvals[k]!==true)parts.push(k.replace(/_/g," "));
 return parts;
}
function filtered(){
 const search=byId("search").value.trim().toLowerCase(),filter=byId("filter").value;
 return data.filter(item=>
  (filter==="all"||(filter==="ready"?isReady(item):!isReady(item))) &&
  [item.manufacturer,item.model,item.variant,item.category,item.id,
   (evidenceById.get(item.id)||{}).recorded_upc||"",
   (evidenceById.get(item.id)||{}).recorded_manufacturer_part_number||"",
   ((evidenceById.get(item.id)||{}).recorded_source_skus||[]).join(" ")
  ].join(" ").toLowerCase().includes(search));
}
function updateSummary(){
 const approved=data.filter(isReady).length;
 byId("total").textContent=data.length;
 byId("finished").textContent=approved;
 byId("held").textContent=data.length-approved;
 byId("exceptions-count").textContent=exceptions.length;
}
function renderList(){
 const items=byId("items");items.replaceChildren();
 const matching=filtered();
 for(const item of matching){
  const button=node("button");
  button.type="button";button.className="product"+(item.id===selected?" active":"");
  button.append(node("strong",item.manufacturer+" "+item.model),
    node("small",(isReady(item)?"Reviewed":"Draft")+" · "+(item.variant||item.product_type||"No variant")+
      ((evidenceById.get(item.id)||{}).recorded_manufacturer_part_number?
       " · MPN "+evidenceById.get(item.id).recorded_manufacturer_part_number:"")),
    ...(isDuplicateName(item)&&evidenceById.has(item.id)?[
      node("small","Recorded UPC "+evidenceById.get(item.id).recorded_upc)
    ]:[]));
  button.addEventListener("click",()=>{selected=item.id;renderList();renderDetail();});
  items.append(button);
 }
 if(!matching.length)items.append(node("p","No products match this view."));
 updateSummary();
}
function asField(label,key,opts={}){
 const outer=node("label");outer.className="field"+(opts.full?" full":"");
 outer.append(node("span",label));
 let element;
 if(opts.select){
  element=node("select");
  for(const [value,title] of opts.select){const option=node("option",title);option.value=value;element.append(option);}
  element.value=opts.value||"";
 }else if(opts.textarea){
  element=node("textarea");element.maxLength=opts.max||200;element.value=opts.value||"";
 }else{
  element=node("input");element.type=opts.date?"date":"text";
  element.maxLength=opts.max||160;element.value=opts.value||"";
 }
 if(opts.readonly)element.readOnly=true;
 element.addEventListener(opts.select?"change":"input",()=>{
  const item=data.find(x=>x.id===selected);
  item[key]=element.value;
  invalidate(item,true);
 });
 outer.append(element);return outer;
}
function invalidate(item,changedFields){
 item.status="draft";
 if(changedFields){
  for(const [key] of CHECKS)item.approvals[key]=false;
  document.querySelectorAll('[data-review-check]').forEach(cb=>{cb.checked=false;});
 }
 updateSummary();renderList();
 const badge=byId("item-status");if(badge)badge.textContent="Draft — not approved";
 const reason=byId("missing");if(reason)reason.textContent=missing(item).join(" · ")||"All fields complete. Confirm this record individually.";
}
function reviewFields(item){
 const fields=node("div");fields.className="fields";
 fields.append(
  asField("Manufacturer — verify; hold if incorrect","manufacturer",{value:item.manufacturer,max:100,readonly:true}),
  asField("Exact model/part number — verify; hold if incorrect","model",{value:item.model,max:120,readonly:true}),
  asField("Verified variant or fit (optional)","variant",{value:item.variant,max:100}),
  asField("Product category","category",{value:item.category,max:100}),
  asField("Product type","product_type",{value:item.product_type,select:[
   ["","Choose a type"],["accessory","Accessory"],["complete","Complete product"],
   ["part","Part"],["ammunition","Ammunition"],["other","Other"]]}),
  asField("Date independent identity evidence was checked","source_checked_at",{date:true,value:item.source_checked_at}),
  asField("Specific identity evidence/reference","identity_evidence_label",{full:true,value:item.identity_evidence_label,max:160}),
  asField("Your original, fact-checked product description (18–200 characters)","description",{full:true,textarea:true,value:item.description,max:200}),
  asField("Copy origin","content_origin",{full:true,value:item.content_origin,select:[
    ["","Choose after writing"],["owner_written","Independently owner-written and fact-checked"]]}),
 );
 return fields;
}
function renderDetail(){
 const place=byId("detail");place.replaceChildren();
 const item=data.find(x=>x.id===selected);
 if(!item){place.append(node("p","Select a product from the queue."));return;}
 const head=node("div");head.className="heading";
 const group=node("div");group.append(node("div","TEXT-ONLY / PRIVATE CANDIDATE"));
 group.append(node("h2",item.manufacturer+" "+item.model));
 group.append(node("p","Public identity: "+item.id));head.append(group);
 const badge=node("span",isReady(item)?"Reviewed — PRIVATE only":"Draft — not approved");
 badge.className="badge";badge.id="item-status";head.append(badge);place.append(head);
 place.append(node("p","All supplier image use remains disabled. Review the product and write original copy. No inventory, prices, photos or publication are implied."));
 const ev=evidenceById.get(item.id);
 if(ev){
  const evidence=node("section");evidence.className="source-evidence";
  const heading=node("h3","Private source identity evidence — not yet independently verified");
  evidence.append(heading);
  const line=node("div");line.className="evidence-grid";
  for(const [label,value] of [
    ["Recorded UPC (check-digit valid only)",ev.recorded_upc],
    ["Manufacturer part number",ev.recorded_manufacturer_part_number],
    ["Source SKU(s), PRIVATE",ev.recorded_source_skus.join(", ")],
    ["RSR category",ev.recorded_category]
  ]){
    const pair=node("div");pair.className="evidence-item";
    pair.append(node("strong",label),node("span",value));line.append(pair);
  }
  evidence.append(line);
  evidence.append(node("p","These values come from a previously saved distributor record. Matching numbers do NOT prove the correct variant, current stock, dealer terms, fit, or sale eligibility."));
  if(isDuplicateName(item))evidence.append(node("p","Look-alike model names are kept separate by exact source UPC and manufacturer part number. Compare before approving."));
  if(ev.neutral_draft_suggestion){
    const suggestion=node("div");suggestion.className="suggestion";
    suggestion.append(node("strong","Neutral wording suggestion from recorded labels only"));
    suggestion.append(node("p",ev.neutral_draft_suggestion));
    const insert=node("button","Use as editable starting text");insert.type="button";
    insert.addEventListener("click",()=>{
      if(item.description && !window.confirm("Replace your existing description with the unverified neutral starting text?"))return;
      item.description=ev.neutral_draft_suggestion;
      item.content_origin="";
      for(const [key] of CHECKS)item.approvals[key]=false;
      item.status="draft";
      renderList();renderDetail();
    });
    suggestion.append(insert);
    suggestion.append(node("p","Edit and independently verify every claim. Inserting never confirms owner-written origin, identity, or sale authorization."));
    evidence.append(suggestion);
  }else{
    evidence.append(node("p","No safe short description suggestion fits this identity. Write and verify your own copy."));
  }
  place.append(evidence);
 }else{
  place.append(node("p","No matched private UPC/MPN evidence was supplied. Independent research remains required."));
 }
 const r=researchById.get(item.id);
 if(r){
  const panel=node("section");panel.className="research";
  panel.append(node("h3","Independent product research — owner verification required"));
  panel.append(node("p","Exact lookup: "+r.research_query));
  const lookup=node("a","Search public sources for this UPC / manufacturer part number");
  lookup.href="https://www.google.com/search?q="+encodeURIComponent(r.research_query);
  lookup.target="_blank";lookup.rel="noopener noreferrer";
  panel.append(lookup);
  panel.append(node("p","This link opens an external search only when clicked; the recorded UPC and part number are sent to that search provider. No private distributor SKU is included."));
  for(let i=0;i<r.sources.length;i++){
   const source=r.sources[i];
   const sect=node("div");sect.className="research-source";
   const link=node("a",source.title);link.href=source.url;link.target="_blank";
   link.rel="noopener noreferrer";sect.append(link);
   sect.append(node("p",source.source_kind.replace(/_/g," ")+" · Observed "+source.observed_on+" · Not a manufacturer permission grant"));
   for(const fact of r.facts.filter(x=>x.source_index===i)){
    const label=node("label"),check=node("input");
    check.type="checkbox";check.checked=fact.owner_checked===true;
    check.addEventListener("change",()=>{
      fact.owner_checked=check.checked;
      // A fact losing support should also withdraw previous item approval.
      if(!check.checked && item.status==="published")invalidate(item,true);
    });
    label.append(check,node("span",fact.label+": "+fact.value+
      " — I personally checked this exact claim against the linked source"));
    sect.append(label);
   }
   const addFact=node("button","Add specific fact from this source");addFact.type="button";
   addFact.addEventListener("click",()=>{
    if(r.facts.length>=12){alert("Maximum 12 source-linked facts per product");return;}
    const label=window.prompt("Fact category (choose one): "+researchLabels.join(" | "),"Other verified attribute");
    if(label===null)return;
    if(!researchLabels.includes(label)){alert("Choose one of the listed categories exactly.");return;}
    const value=window.prompt("Short factual specification (4–130 characters). No source marketing prose, prices or stock claims:");
    if(value===null)return;
    const clean=value.trim();
    if(clean.length<4||clean.length>130){alert("Fact must be 4–130 characters");return;}
    r.facts.push({label,value:clean,source_index:i,owner_checked:false});
    if(item.status==="published")invalidate(item,true);
    renderDetail();
   });
   sect.append(addFact);
   panel.append(sect);
  }
  const action=node("div");action.className="research-actions";
  const add=node("button","Add independently found reference");add.type="button";
  add.addEventListener("click",()=>{
    if(r.sources.length>=8){alert("Maximum eight source links per item");return;}
    const title=window.prompt("Reference title (4–160 characters):");
    if(title===null)return;
    if(title.trim().length<4||title.trim().length>160){alert("Invalid source title");return;}
    const uri=window.prompt("Paste exact HTTPS product/specification URL:");
    if(uri===null)return;
    let u;
    try{u=new URL(uri);}catch(_){alert("URL is invalid");return;}
    if(u.protocol!=="https:"||!u.hostname.includes(".")||u.username||
       u.password||u.hash||u.hostname==="localhost"){
      alert("Use a public HTTPS reference without login credentials or fragment.");return;
    }
    r.sources.push({title:title.trim(),url:uri.trim(),
      source_kind:"other_public_reference",observed_on:new Date().toISOString().slice(0,10)});
    if(item.status==="published")invalidate(item,true);
    renderDetail();
  });
  const draft=node("button","Use checked facts in editable draft");draft.type="button";
  draft.addEventListener("click",()=>{
    const facts=r.facts.filter(x=>x.owner_checked===true);
    if(!facts.length){alert("Independently check at least one exact claim first.");return;}
    let suggestion=item.manufacturer+" "+item.model+".";
    for(const fact of facts){
      const next=suggestion+" "+fact.label+": "+fact.value+".";
      if(next.length>200)break;
      suggestion=next;
    }
    if(suggestion===item.manufacturer+" "+item.model+"."){
      alert("Checked facts do not fit the 200-character limit.");return;
    }
    if(item.description && !window.confirm("Replace existing copy with this editorial starting point?"))return;
    item.description=suggestion;
    item.content_origin="";
    for(const [key] of CHECKS)item.approvals[key]=false;
    item.status="draft";
    renderList();renderDetail();
  });
  action.append(add,draft);panel.append(action);
  panel.append(node("p","Research sources and source-linked facts stay PRIVATE. Checking a fact is your own review assertion, not certification. Inserting text NEVER marks it owner-written or approves the product."));
  place.append(panel);
 }
 place.append(reviewFields(item));
 const section=node("fieldset");section.className="review";
 section.append(node("legend","Independent item-by-item confirmations"));
 for(const [key,label] of CHECKS){
  const row=node("label");row.className="check";
  const cb=node("input");cb.type="checkbox";cb.checked=item.approvals[key]===true;
  cb.setAttribute("data-review-check",key);
  cb.addEventListener("change",()=>{
   item.approvals[key]=cb.checked;
   invalidate(item,false);
  });
  row.append(cb,node("span",label));section.append(row);
 }
 const media=node("p","Image rights: NOT CLAIMED. Zero images will be included in text-only listings.");
 media.className="mini";section.append(media);place.append(section);
 const errors=node("p",missing(item).join(" · ")||"All fields complete. Confirm this record individually.");
 errors.className="missing";errors.id="missing";place.append(errors);
 const actions=node("div");actions.className="actionbar";
 const left=node("div"),right=node("div");
 const previous=node("button","Previous");previous.type="button";
 previous.addEventListener("click",()=>move(-1));
 const next=node("button","Next");next.type="button";next.addEventListener("click",()=>move(1));
 const nextHeld=node("button","Next unfinished");nextHeld.type="button";
 nextHeld.addEventListener("click",()=>{
  const index=data.findIndex(x=>x.id===selected);
  for(let off=1;off<=data.length;off++){
   const match=data[(index+off)%data.length];
   if(!isReady(match)){selected=match.id;renderList();renderDetail();return;}
  }
  alert("All candidates in this session have completed review.");
 });
 left.append(previous,next,nextHeld);
 const hold=node("button","Keep as draft");hold.type="button";
 hold.addEventListener("click",()=>{item.status="draft";updateSummary();renderList();renderDetail();});
 const confirm=node("button","Confirm this product");confirm.type="button";confirm.className="primary";
 confirm.addEventListener("click",()=>{
  if(!contentComplete(item)||!CHECKS.every(x=>item.approvals[x[0]]===true)){
   alert("Complete original copy, identity evidence, date and all four independent confirmations first.");
   return;
  }
  if(!window.confirm("Individually approve this exact text-only product for a PRIVATE approved-only export? This does NOT publish a website or authorize photos."))return;
  item.status="published";updateSummary();renderList();renderDetail();
 });
 right.append(hold,confirm);actions.append(left,right);place.append(actions);
}
function move(direction){
 const index=data.findIndex(x=>x.id===selected);
 if(index<0)return;
 selected=data[(index+direction+data.length)%data.length].id;
 renderList();renderDetail();
}
function download(name,contents){
 const blob=new Blob([JSON.stringify(contents,null,2)+"\n"],{type:"application/json"});
 const url=URL.createObjectURL(blob),anchor=node("a");
 anchor.href=url;anchor.download=name;anchor.click();
 setTimeout(()=>URL.revokeObjectURL(url),1500);
}
byId("search").addEventListener("input",renderList);
byId("filter").addEventListener("change",renderList);
byId("save").addEventListener("click",()=>download("area33-private-text-batch-progress.json",data));
byId("research-save").addEventListener("click",()=>{
 if(!research){alert("Run the private research-packet generator first.");return;}
 download("area33-private-product-research-progress.json",research);
});
byId("research-resume").addEventListener("change",async ev=>{
 const file=ev.target.files&&ev.target.files[0];if(!file)return;
 try{
  if(!research)throw Error("Generate the original private research packet first");
  if(file.size>8_000_000)throw Error("Research file too large");
  const incoming=JSON.parse(await file.text());
  if(!incoming||incoming.schema!==research.schema||
      incoming.candidate_count!==research.candidate_count||
      incoming.source_drafts_sha256!==research.source_drafts_sha256||
      incoming.private_identity_evidence_sha256!==research.private_identity_evidence_sha256||
      incoming.publication_approved!==false||
      incoming.source_research_is_owner_verified!==false||
      !Array.isArray(incoming.items)||incoming.items.length!==data.length)
   throw Error("Private research provenance or candidate count differs");
  const old=new Map(research.items.map(x=>[x.id,x])),found=new Set();
  for(const row of incoming.items){
   const prior=old.get(row.id);
   if(!prior||found.has(row.id)||row.recorded_upc!==prior.recorded_upc||
      row.recorded_mpn!==prior.recorded_mpn||row.research_query!==prior.research_query||
      !Array.isArray(row.sources)||row.sources.length>8||
      !Array.isArray(row.facts)||row.facts.length>12)
    throw Error("Research identity mismatch");
   found.add(row.id);
   for(const s of row.sources){
    let uri;try{uri=new URL(s.url);}catch(_){throw Error("Invalid source link");}
    if(!["manufacturer","independent_retailer","other_public_reference"].includes(s.source_kind)||
       typeof s.title!=="string"||s.title.length<4||s.title.length>160||
       uri.protocol!=="https:"||!uri.hostname.includes(".")||uri.username||
       uri.password||uri.hash||!/^\d{4}-\d{2}-\d{2}$/.test(s.observed_on))
      throw Error("Malformed research source");
   }
   for(const fact of row.facts){
    if(!researchLabels.includes(fact.label)||typeof fact.value!=="string"||
       fact.value.length<4||fact.value.length>130||
       !Number.isInteger(fact.source_index)||fact.source_index<0||
       fact.source_index>=row.sources.length||typeof fact.owner_checked!=="boolean")
      throw Error("Malformed referenced fact");
   }
  }
  if(!window.confirm("Load this private source research file? It does NOT approve products."))return;
  research=incoming;researchById=new Map(research.items.map(x=>[x.id,x]));
  renderList();renderDetail();
 }catch(err){alert("Research notes were not loaded: "+err.message);}
 finally{ev.target.value="";}
});
byId("export").addEventListener("click",()=>{
 const invalid=data.filter(item=>item.status==="published"&&!isReady(item));
 if(invalid.length){alert("Some published-status records have incomplete reviews. Correct them first.");return;}
 const approved=data.filter(isReady);
 if(!approved.length){alert("No individually approved products yet. Save progress instead.");return;}
 if(!window.confirm("Export "+approved.length+" individually approved text-only records to a PRIVATE JSON file? Nothing is published."))return;
 download("area33-owner-approved-text-only-private.json",approved);
});
byId("resume").addEventListener("change",async ev=>{
 const file=ev.target.files&&ev.target.files[0];if(!file)return;
 try{
  if(file.size>8_000_000)throw Error("Progress file is too large");
  const incoming=JSON.parse(await file.text());
  if(!Array.isArray(incoming)||incoming.length!==data.length)throw Error("Wrong candidate count");
  const originals=new Map(data.map(x=>[x.id,x]));
  const currentIds=new Set(data.map(x=>x.id)),found=new Set();
  for(const item of incoming){
   if(!item||typeof item!=="object"||!currentIds.has(item.id)||found.has(item.id)||
      item.listing_mode!=="text_only"||item.rights_source!==""||
      item.manufacturer!==originals.get(item.id).manufacturer||
      item.model!==originals.get(item.id).model||
      !Array.isArray(item.photos)||item.photos.length!==0||
      !item.approvals||item.approvals.media_rights!==false||
      !["draft","published"].includes(item.status)||
      CHECKS.some(x=>typeof item.approvals[x[0]]!=="boolean")||
      (item.status==="published"&&!isReady(item)))throw Error("Invalid or mismatched review progress");
   found.add(item.id);
  }
  if(!window.confirm("Replace this browser session with "+incoming.length+" records from your local private progress file?"))return;
  const lookup=new Map(incoming.map(x=>[x.id,x]));
  data=data.map(item=>lookup.get(item.id));
  selected=data[0].id;renderList();renderDetail();
 }catch(err){alert("Could not resume: "+err.message);}
 finally{ev.target.value="";}
});
const list=byId("exceptions");
for(const entry of exceptions){
 const e=node("div");e.className="exception";
 e.append(node("strong",(entry.manufacturer||"Unknown manufacturer")+" · "+(entry.model||"Model missing")));
 e.append(node("p","Reason(s): "+entry.reasons.join(", ")));
 const source=node("p","Private source SKU(s) for identity research only: "+entry.source_skus.join(", "));
 source.className="mini";e.append(source);list.append(e);
}
byId("exceptions-toggle").addEventListener("click",()=>{
 list.hidden=!list.hidden;
 byId("exceptions-toggle").textContent=list.hidden?"Show exception details":"Hide exception details";
});
renderList();renderDetail();
</script></body></html>
"""


def make_batch_review(input_file:Path,exceptions_file:Path,out:Path|None=None,
                      *,evidence_file:Path|None=None,research_file:Path|None=None)->Path:
    rows,exceptions=source_batch(input_file,exceptions_file)
    evidence=(validated_private_evidence(evidence_file,input_file,exceptions_file,rows)
              if evidence_file is not None else [])
    research=None
    if research_file is not None:
        if evidence_file is None:
            raise ReviewError("Research packet requires matching original identity evidence")
        from prepare_private_product_research import validate_research_packet
        research=json.loads(_private_file(research_file).read_text(encoding="utf-8"))
        validate_research_packet(research,evidence,input_file,evidence_file)
    if out is None:
        out=Path(input_file).expanduser().resolve().parent/"catalog-batch-owner-review.html"
    else:
        out=Path(out).expanduser().resolve()
    if (out.exists() or out.parent!=Path(input_file).expanduser().resolve().parent
            or out.suffix.lower()!=".html"
            or out.is_relative_to(HERE)):
        raise ReviewError("Choose a new .html file in the same private draft directory")
    html=(HTML.replace("__REVIEW_DATA__",inline(rows))
          .replace("__EXCEPTION_DATA__",inline(exceptions))
          .replace("__PRIVATE_EVIDENCE__",inline(evidence))
          .replace("__PRIVATE_RESEARCH__",inline(research)))
    if len(html.encode("utf-8"))>MAX_HTML_BYTES:
        raise ReviewError("Private HTML review file would exceed safe offline limit")
    out.write_text(html,encoding="utf-8")
    return out


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--drafts",required=True,type=Path)
    p.add_argument("--exceptions",required=True,type=Path)
    p.add_argument("--evidence",type=Path,
                   help="Private RSR UPC/MPN/SKU sidecar from original staged source")
    p.add_argument("--research",type=Path,
                   help="Private, source-linked research packet; no approval inferred")
    p.add_argument("--out",type=Path)
    args=p.parse_args(argv)
    try:
        path=make_batch_review(args.drafts,args.exceptions,args.out,
                               evidence_file=args.evidence,
                               research_file=args.research)
    except (ValueError,OSError,KeyError,TypeError) as exc:
        p.error(str(exc))
    print("PRIVATE, OFFLINE, FOCUSED owner-review workspace:")
    print(" ",path)
    print("Only individually confirmed text-only items can be exported.")
    print("Identity exceptions remain quarantined and read-only; NO publication.")


if __name__=="__main__":
    main()
