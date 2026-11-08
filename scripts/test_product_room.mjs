import assert from "node:assert/strict";
import fs from "node:fs";
import {REFERENCE_PRODUCTS,REFERENCE_CHECKED,DEPARTMENTS,ACCESSORY_CATEGORIES,chooseDiscovery,researchByDepartment,researchAccessories} from "../assets/product-room-research.mjs";
import {sanitizeCatalogManifest} from "../assets/catalog-static-contract.mjs";
const html=fs.readFileSync(new URL("../product-room.html",import.meta.url),"utf8");
const script=fs.readFileSync(new URL("../assets/product-room.js",import.meta.url),"utf8");
const stylesheet=fs.readFileSync(new URL("../assets/product-room.css",import.meta.url),"utf8");
const homepage=fs.readFileSync(new URL("../index.html",import.meta.url),"utf8");
const catalog=fs.readFileSync(new URL("../catalog.html",import.meta.url),"utf8");
const publicCatalog=JSON.parse(fs.readFileSync(new URL("../assets/catalog-public.json",import.meta.url),"utf8"));
assert.match(REFERENCE_CHECKED,/^\d{4}-\d\d-\d\d$/);
assert.equal(REFERENCE_PRODUCTS.length,14);
assert.deepEqual(DEPARTMENTS,["pistols","rifles","shotguns"]);
assert.deepEqual(ACCESSORY_CATEGORIES,["optics","lights","holsters","cases"]);
assert.equal(new Set(REFERENCE_PRODUCTS.map(x=>x.id)).size,REFERENCE_PRODUCTS.length);
for(const department of DEPARTMENTS){
 assert.ok(researchByDepartment(department).length>=2,"Needs more than one model in "+department);
}
for(const category of ["optics","lights","holsters"])
 assert.ok(researchAccessories(category).length>=1,"Missing real accessory category "+category);
for(const item of REFERENCE_PRODUCTS){
 assert.ok(item.brand&&item.model&&item.note);
 assert.ok(item.source.startsWith("https://"));
 assert.equal("images" in item,false,"Never include unapproved media from public references");
 assert.equal("price" in item,false,"Manufacturer research references do not set a customer price");
 assert.equal("compatibleWith" in item,false,"Never infer exact fit from category/family");
}
const first=REFERENCE_PRODUCTS.filter(x=>x.kind==="firearm");
assert.notEqual(chooseDiscovery(first,first[0].id,0).id,first[0].id);
assert.ok(chooseDiscovery([],null,0)===null);
assert.equal(researchAccessories("cases").length,0,"A missing category must remain honestly unfilled");
assert.equal(publicCatalog.items.length,0,"No public approved listings yet (update only after approval)");
assert.ok(sanitizeCatalogManifest(publicCatalog)?.items.length===0);
const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]);
assert.equal(new Set(ids).size,ids.length,"Duplicate product room HTML ID");
for(const id of ["brand","model","surprise","product-name","approved-gallery-slot","media-unavailable",
 "manufacturer-photos","product-facts","official-link","accessory-items","accessory-brand",
 "pairing-title","pairing-warning","accessory-official-link","intel-answer","compare-list",
 "compare-add","share-selection","research-coverage"]){
 assert.ok(ids.includes(id),"Missing interactive element: "+id);
 assert.ok(script.includes('$("'+id+'")'),"Missing JS binding: "+id);
}
for(const department of DEPARTMENTS)assert.ok(html.includes('data-department="'+department+'"'));
for(const category of ACCESSORY_CATEGORIES)assert.ok(html.includes('data-accessory-category="'+category+'"'));
for(const question of ["differences","fit","value"])assert.ok(html.includes('data-question="'+question+'"'));
assert.match(script,/createApprovedGallery\(approvedItem\)/);
assert.match(script,/galleryAllowed\(approvedItem\)/);
assert.match(script,/sanitizeCatalogManifest/);
assert.match(script,/Compatibility not verified/);
assert.match(script,/accessory=list\.find\(x=>x\.id===preferId\)\|\|null/);
assert.match(script,/Long Guns.*cannot safely be assumed/);
assert.doesNotMatch(script,/dealer_cost|private_supplier|source_sku|localStorage|sessionStorage/);
assert.doesNotMatch(html,/<iframe|<script\b(?![^>]*\bsrc=)[^>]*>[\s\S]*<\/script>/i);
assert.match(homepage,/href="product-room\.html"/);
assert.match(catalog,/href="product-room\.html"/);
assert.match(stylesheet,/\.room-stage/);
console.log("Real product room: categories, manufacturer references, explicit accessory selection, image rights gate, source links, DOM contracts and safe statuses verified.");
