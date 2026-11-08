import assert from "node:assert/strict";
import fs from "node:fs";
import {REFERENCE_PRODUCTS} from "../assets/product-room-research.mjs";
import {researchPhotoFor} from "../assets/research-photo-license.mjs";
import {FIREARMS,findResearchProducts,variantDisclosure,interpretResearchQuestion} from "../assets/customer-experience.mjs";

const home=fs.readFileSync(new URL("../index.html",import.meta.url),"utf8");
const js=fs.readFileSync(new URL("../assets/side-counter-ui.js",import.meta.url),"utf8");
const css=fs.readFileSync(new URL("../assets/side-counter.css",import.meta.url),"utf8");
const featured=fs.readFileSync(new URL("../assets/featured-opportunities-ui.js",import.meta.url),"utf8");
const testIds=["home-firearms-gallery","home-firearms-query","home-firearms-category","home-firearms-count",
 "area33-side-counter","area33-side-backdrop","area33-reopen-counter","side-counter-close",
 "side-counter-product-name","side-counter-product-meta","side-counter-body",
 "side-tab-inspect","side-tab-models","side-tab-accessories","side-tab-eva","side-save",
 "side-compare","side-saved-status","side-comparison-list","side-full-counter"];
for(const id of testIds){
 assert.ok(home.includes('id="'+id+'"'),"Missing side-counter element "+id);
 assert.ok(js.includes('$("'+id+'")')||id.startsWith("side-tab-")&&js.includes('"side-tab-"+tab')||
  id==="area33-side-backdrop"||id==="area33-side-counter"||id==="area33-reopen-counter",
  "Missing side-counter behavior "+id);
}
assert.equal([...home.matchAll(/\bid="([^"]+)"/g)].length,
 new Set([...home.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1])).size,"Unique DOM IDs");
const hero=home.indexOf('<div class="hero"'),browse=home.indexOf('id="home-firearms"'),
 featuredSection=home.indexOf('id="featured-opportunities"');
assert.ok(hero>=0&&browse>hero&&featuredSection>browse,"Firearms browse must appear immediately after hero and before featured");
assert.match(home,/Ruger_Precision_Rifle_308_Gen_1\.jpg/,"An actual license-reviewed firearm visible above fold");
assert.match(home,/Coati077 \/ CC BY-SA 4\.0/,"Image licensing visible");
assert.match(home,/data-side-counter-product="ruger-precision-308-gen1"/);
assert.match(home,/Ask EVA — Your Firearms Expert/);
assert.match(home,/receiving FFL fee separate/i);
assert.match(home,/Not live inventory|No live inventory/i);
assert.match(home,/assets\/side-counter-ui\.js/);
assert.match(home,/assets\/side-counter\.css/);
assert.match(js,/window\.addEventListener\("area33:side-counter-open"/);
assert.match(js,/window\.matchMedia\("\(max-width: 900px\)"\)/);
assert.match(js,/document\.addEventListener\("keydown"/);
assert.match(js,/if\(e\.key==="Escape"/);
assert.match(js,/previousFocus/);
assert.match(js,/state\.compare\.size>=3/);
assert.match(js,/state\.saved=new Set|saved:new Set/);
assert.match(js,/interpretResearchQuestion\(p,query\)/);
assert.match(js,/accessoryIntelligence\(p,a\)/);
assert.match(js,/variantDisclosure\(p\)/);
assert.match(js,/researchPhotoFor\(product\)/);
assert.match(js,/document\.querySelectorAll\("\[data-shop-department\]"\)/);
assert.match(featured,/area33:side-counter-open/);
assert.match(featured,/area33:featured-open/,"Existing full-sized counter still supported");
assert.match(css,/\.area33-side-counter\{/);
assert.match(css,/body\.area33-side-open\{padding-right/,"Desktop store stays alongside panel");
assert.match(css,/@media\(max-width:900px\)/,"Mobile counter layout");
assert.match(css,/\.area33-side-counter\[hidden\]/);
assert.doesNotMatch(js,/localStorage|sessionStorage|indexedDB|navigator\.sendBeacon|credentials\s*:|private_supplier|dealerCost/,"No session tracking or private data");
const research=FIREARMS.filter(p=>p.kind==="firearm");
assert.ok(research.length>=10,"Browsing real manufacturer references");
assert.equal(findResearchProducts("","all").length,research.length,"Full visible research set not a short three-item list");
assert.equal(findResearchProducts("","pistols").every(p=>p.department==="pistols"),true);
assert.equal(variantDisclosure(REFERENCE_PRODUCTS.find(x=>x.id==="glock-g19-gen5-mos")).verifiedColors.length,0,"No made-up finish availability");
assert.equal(researchPhotoFor(REFERENCE_PRODUCTS.find(x=>x.id==="glock-g19-gen5-mos")),null,"Missing approved photo stays missing");
assert.match(interpretResearchQuestion(research[0],"what is the price").text,/receiving FFL/i);
console.log("Area 33 side-counter: merchandise-first homepage, right-side product sheet, mobile overlay, source-labeled media, product-aware EVA, in-session comparisons and separate FFL fee validated.");
