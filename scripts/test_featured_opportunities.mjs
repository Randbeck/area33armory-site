import assert from "node:assert/strict";
import fs from "node:fs";
import {FEATURED_SCHEMA,validateFeaturedPublic,visibleFeatured,
 EDITORIAL_RESEARCH_HIGHLIGHTS} from "../assets/featured-opportunities.mjs";
const home=fs.readFileSync(new URL("../index.html",import.meta.url),"utf8");
const counter=fs.readFileSync(new URL("../six-view-counter.html",import.meta.url),"utf8");
const ui=fs.readFileSync(new URL("../assets/featured-opportunities-ui.js",import.meta.url),"utf8");
const css=fs.readFileSync(new URL("../assets/featured-opportunities.css",import.meta.url),"utf8");
const publicManifest=JSON.parse(fs.readFileSync(new URL("../assets/featured-public.json",import.meta.url),"utf8"));
assert.equal(publicManifest.schema,FEATURED_SCHEMA);
assert.deepEqual(publicManifest.items,[],"No Randbeck business opportunity automatically becomes a public product promotion");
assert.deepEqual(validateFeaturedPublic(publicManifest),[]);
assert.equal(visibleFeatured([]).length,3);
assert.ok(EDITORIAL_RESEARCH_HIGHLIGHTS.every(x=>x.label==="Research discovery"&&x.published===false));
const sample={publicId:"feature-example-ruger",productId:"ruger-precision-308-gen1",
 headline:"Explore the precision rifle","description":"A real research reference with manufacturer context and a legally credited image.",
 label:"Featured discovery",ownerApproved:true,productIdentityReviewed:true,publicationRightsReviewed:true,
 reviewedAt:"2026-11-08T10:00:00Z",expiresAt:"2026-11-10T10:00:00Z"};
const manifest=items=>({schema:FEATURED_SCHEMA,items});
const time=Date.parse("2026-11-08T15:00:00Z");
const checked=validateFeaturedPublic(manifest([sample]),{now:time});
assert.equal(checked.length,1);
assert.equal(checked[0].productId,sample.productId);
assert.equal(visibleFeatured(checked).length,1,"Approved opportunities replace research fallback");
for(const change of [
 {ownerApproved:false},{productIdentityReviewed:false},{publicationRightsReviewed:false},
 {productId:"unverified-private-sku"},{description:"dealer cost $500, gross margin $200"},
 {headline:"internal opportunity dealer margin"},{reviewedAt:"INVALID"},
 {expiresAt:"2026-11-07T10:00:00Z"},{extraInternalProfit:99}
]){
 assert.equal(validateFeaturedPublic(manifest([{...sample,...change}]),{now:time}),null,
 "Invalid or unapproved opportunities must never appear publicly");
}
assert.equal(validateFeaturedPublic(manifest([sample,sample]),{now:time}),null,"Duplicate featured opportunity rejected");
assert.equal(validateFeaturedPublic(manifest([{...sample,expiresAt:"2026-11-08T14:00:00Z"}]),{now:time}),null,"Expired opportunities are never advertised");
assert.equal(validateFeaturedPublic({schema:FEATURED_SCHEMA,items:[],privateMargins:[12]}),null,"Private fields forbidden in public contract");
for(const html of [home,counter]){
 assert.match(html,/id="featured-products"/);
 assert.match(html,/id="featured-coverage"/);
 assert.match(html,/assets\/featured-opportunities\.css/);
 assert.match(html,/assets\/featured-opportunities-ui\.js/);
}
assert.match(home,/Meet EVA/);
assert.match(home,/Receiving FFL transfer fee is separate/i);
assert.match(counter,/id="ask-eva"/);
assert.doesNotMatch(counter,/id="ffl-name"|id="ffl-fee-known"/);
assert.match(ui,/validateFeaturedPublic\(await response\.json\(\)\)/);
assert.match(ui,/researchPhotoFor\(product\)/);
assert.match(ui,/window\.dispatchEvent\(new CustomEvent\("area33:featured-open"/);
assert.match(ui,/No opportunities have been approved for public featuring yet/);
assert.doesNotMatch(ui,/localStorage|sessionStorage|dealer_cost|wholesale|grossMargin|privateSupplier|Authorization/);
assert.match(css,/\.featured-products/);
console.log("Featured Area 33: reviewed public-only opportunity manifest, explicit no-deal fallback, evidence photo controls, EVA naming and receiving FFL fee exclusion validated.");
