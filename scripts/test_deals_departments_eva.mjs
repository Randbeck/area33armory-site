import assert from "node:assert/strict";
import fs from "node:fs";
import {DEALS_SCHEMA,validatePublicDeals} from "../assets/deals-public-contract.mjs";
const home=fs.readFileSync(new URL("../index.html",import.meta.url),"utf8");
const ui=fs.readFileSync(new URL("../assets/featured-opportunities-ui.js",import.meta.url),"utf8");
const side=fs.readFileSync(new URL("../assets/side-counter-ui.js",import.meta.url),"utf8");
const css=fs.readFileSync(new URL("../assets/side-counter.css",import.meta.url),"utf8");
const blank=JSON.parse(fs.readFileSync(new URL("../assets/deals-public.json",import.meta.url),"utf8"));
const now=Date.parse("2026-11-08T17:00:00Z");
assert.equal(blank.schema,DEALS_SCHEMA);
assert.deepEqual(blank.items,[],"Do not advertise fabricated or unverified live deals");
assert.deepEqual(validatePublicDeals(blank,{now}),[]);
const approved={
 publicId:"deal-ruger-research-demo",productId:"ruger-precision-308-gen1",
 headline:"Verified Area 33 promotion",
 description:"Sample approved editorial offer, with a sourceable exact-model listing.",
 label:"Area 33 Special",offerTerms:"Destination-based Area 33 delivered price required; receiving FFL fee separately charged.",
 ownerApproved:true,exactProductReviewed:true,mediaRightsReviewed:true,
 publicOfferReviewed:true,inventoryVerified:true,termsVerified:true,
 reviewedAt:"2026-11-08T16:00:00Z",expiresAt:"2026-11-09T16:00:00Z"};
const manifest=items=>({schema:DEALS_SCHEMA,items});
assert.equal(validatePublicDeals(manifest([approved]),{now})?.[0].productId,approved.productId);
for(const change of [
 {ownerApproved:false},{exactProductReviewed:false},{mediaRightsReviewed:false},
 {publicOfferReviewed:false},{inventoryVerified:false},{termsVerified:false},
 {productId:"internal-sku-not-public"},{headline:"Supplier wholesale cost"},
 {offerTerms:"Private source, gross margin 50%"},{expiresAt:"2026-11-07T00:00:00Z"},
 {reviewedAt:"not-a-date"},{unreviewedDiscount:49}
]){
 assert.equal(validatePublicDeals(manifest([{...approved,...change}]),{now}),null,"Reject unverifiable or private deals");
}
assert.equal(validatePublicDeals(manifest([approved,approved]),{now}),null,"Duplicate offer forbidden");
assert.equal(validatePublicDeals({schema:DEALS_SCHEMA,items:[],supplierCosts:[]},{now}),null);
assert.match(home,/id="featured-opportunities" data-featured-mode="deals"/);
assert.match(home,/Just Landed\./);
assert.match(home,/id="lz33"/);
assert.match(home,/Where the best deals land\./);
assert.doesNotMatch(home,/hero-feature-photo|Deals &amp; Specials ↗/);
assert.match(home,/Shop by Department/);
assert.doesNotMatch(home,/Firearms worth exploring\.|Something worth a closer look\./);
assert.ok(home.indexOf('id="featured-opportunities"')<home.indexOf('id="shop-departments"'));
assert.ok(home.indexOf('id="shop-departments"')<home.indexOf('id="home-firearms"'));
assert.match(home,/id="home-firearms"[^>]*hidden/);
for(const category of ["pistols","rifles","shotguns","suppressors","optics","accessories"])
 assert.match(home,new RegExp('data-department-pick="'+category+'"'));
assert.equal((home.match(/data-department-pick="/g)||[]).length,6);
assert.match(ui,/validatePublicDeals\(await response\.json\(\)\)/);
assert.match(ui,/No current specials have passed our public price, inventory and offer review/);
assert.match(ui,/featured-public\.json/,"Separate editorial discovery remains available for full product counter");
assert.match(side,/revealDepartment\(card\.dataset\.departmentPick\)/);
assert.match(side,/state\.department=department/);
assert.match(side,/section\.hidden=false/);
assert.match(side,/group==="suppressors"\?\[\]/);
assert.match(side,/p\.kind==="firearm"/);
assert.match(side,/MEET EVA \/ YOUR FIREARMS EXPERT/);
assert.match(side,/not a live AI conversation/i);
const meet=side.indexOf('MEET EVA / YOUR FIREARMS EXPERT');
const ask=side.indexOf('const form=make("form","side-eva-form")');
assert.ok(meet>=0&&ask>meet,"Introduce EVA before asking a question");
assert.match(css,/\.department-grid/);
assert.match(css,/\.home-firearms-section\[hidden\]\{display:none!important/);
assert.match(css,/\.deal-empty/);
assert.doesNotMatch(ui,/localStorage|sessionStorage|Authorization:|dealer_cost/);
console.log("Area 33 deals, category cards and Meet EVA: no invented offers, six responsive departments, progressive search and clear assistant introduction verified.");
