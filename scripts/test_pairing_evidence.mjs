import assert from "node:assert/strict";
import fs from "node:fs";
import {REFERENCE_PRODUCTS} from "../assets/product-room-research.mjs";
import {PAIRING_SCHEMA,PAIRING_REVIEWED,PAIRING_EVIDENCE,evaluatePairing,manufacturerListedSuggestions} from "../assets/pairing-evidence.mjs";
const get=id=>REFERENCE_PRODUCTS.find(x=>x.id===id);
const accessoryItems=REFERENCE_PRODUCTS.filter(x=>x.kind==="accessory");
const mos=get("glock-g19-gen5-mos");
const standard=get("glock-g19-gen5");
const slim=get("glock-g43x-mos");
const exact=get("holosun-scs-m-gr");
const k=get("holosun-hs507k-x2");
const light=get("streamlight-tlr7-x");
assert.equal(PAIRING_SCHEMA,"area33.pair-evidence.research.v1");
assert.match(PAIRING_REVIEWED,/^\d{4}-\d{2}-\d{2}$/);
for(const x of [mos,standard,slim,exact,k,light])assert.ok(x,"Missing expected actual manufacturer product");
assert.equal(PAIRING_EVIDENCE.length,5);
assert.equal(evaluatePairing(mos,exact).status,"manufacturer-listed");
assert.match(evaluatePairing(mos,exact).summary,/G19 Gen5 MOS/);
assert.match(evaluatePairing(mos,exact).summary,/SCS-M-GR/);
assert.match(evaluatePairing(mos,exact).caution,/not independent physical inspection/i);
assert.equal(evaluatePairing(standard,exact).status,"factory-interface-differs");
assert.equal(evaluatePairing(slim,exact).status,"factory-interface-differs");
assert.equal(evaluatePairing(mos,light).status,"family-guidance");
assert.equal(evaluatePairing(standard,light).status,"family-guidance");
for(const record of PAIRING_EVIDENCE){
 assert.ok(record.short&&record.why&&record.summary&&record.caution);
 assert.ok(!record.summary.includes("guaranteed fit"));
 for(const evidence of record.evidence){
  assert.match(evidence.url,/^https:\/\/(?:us\.glock\.com|www\.holosun\.com|www\.streamlight\.com)\//);
  assert.equal(evidence.checkedAt,PAIRING_REVIEWED);
  assert.ok(evidence.label);
 }
 assert.equal("price" in record,false);
 assert.equal("image" in record,false);
}
assert.equal(evaluatePairing(mos,k).status,"not-reviewed","Never infer similar optic mounts");
assert.equal(evaluatePairing(get("ruger-precision"),exact).status,"not-reviewed");
assert.equal(evaluatePairing(mos,get("aliengear-photon")).status,"not-reviewed");
assert.equal(evaluatePairing(null,exact),null);
assert.equal(evaluatePairing(mos,null),null);
assert.equal(evaluatePairing({...mos,approvedItem:{id:"catalog_00000000000000000000"}},exact).status,"not-reviewed","No private or approved catalog conflation");
assert.equal(evaluatePairing(mos,{...exact,approvedItem:{id:"catalog_00000000000000000000"}}).status,"not-reviewed");
assert.equal(evaluatePairing({...mos,id:"glock-g19-gen5-mos-extra"},exact).status,"not-reviewed","Only exact model IDs");
assert.equal(evaluatePairing(mos,{...exact,id:"holosun-scs-pdp-gr"}).status,"not-reviewed","Only exact optic SKU");
assert.deepEqual(manufacturerListedSuggestions(mos,accessoryItems).map(x=>x.id),["holosun-scs-m-gr"]);
assert.deepEqual(manufacturerListedSuggestions(standard,accessoryItems),[]);
assert.deepEqual(manufacturerListedSuggestions(slim,accessoryItems),[]);
assert.deepEqual(manufacturerListedSuggestions({...mos,approvedItem:{}},accessoryItems),[]);
assert.deepEqual(manufacturerListedSuggestions(mos,[]),[]);

const html=fs.readFileSync(new URL("../product-room.html",import.meta.url),"utf8");
const code=fs.readFileSync(new URL("../assets/product-room.js",import.meta.url),"utf8");
const style=fs.readFileSync(new URL("../assets/product-room.css",import.meta.url),"utf8");
for(const id of ["pairing-evidence","pairing-evidence","pairing-status","pairing-reviewed","pairing-summary","pairing-why","pairing-sources","smart-suggestion","smart-suggestion-caption","smart-suggestion-area"]){
 assert.match(html,new RegExp('id="'+id+'"'),"Missing markup "+id);
}
assert.match(html,/glock-g19-gen5-mos&amp;accessory=holosun-scs-m-gr/);
assert.match(html,/No composed product image is shown yet/);
assert.match(html,/The exact pairing may have a manufacturer fitment statement/);
assert.match(code,/evaluatePairing\(current,accessory\)/);
assert.match(code,/manufacturerListedSuggestions\(current,listItems\("accessory","optics"\)\)/);
assert.match(code,/citation\.url/);
assert.match(code,/link\.rel="noopener noreferrer"/);
assert.match(code,/presentPairingEvidence\(null\)/);
assert.match(code,/Not a factory direct match/);
assert.match(code,/Family guidance only/);
assert.doesNotMatch(code,/innerHTML|localStorage|sessionStorage|dealer_cost/);
assert.match(style,/\.room-pair-status/);
console.log("Exact manufacturer pair evidence: listed, different interface, family guidance and unknown variants all guarded; source-driven UI verified.");
