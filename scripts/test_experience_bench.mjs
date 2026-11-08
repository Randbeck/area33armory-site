import assert from "node:assert/strict";
import fs from "node:fs";
import {REFERENCE_PRODUCTS} from "../assets/product-room-research.mjs";
import {benchPhotoFor,benchEvidenceFor,shareBenchUrl} from "../assets/experience-bench.mjs";
import {INSPIRATION_MEDIA,verifyInspiration,inspirationForEditorial} from "../assets/showroom-inspiration.mjs";
const item=id=>REFERENCE_PRODUCTS.find(x=>x.id===id);
const mos=item("glock-g19-gen5-mos"),standard=item("glock-g19-gen5");
const scs=item("holosun-scs-m-gr"),tlr=item("streamlight-tlr7-x"),ruger=item("ruger-precision-308-gen1");
assert.ok(mos&&standard&&scs&&tlr&&ruger);
assert.equal(benchPhotoFor(mos),null,"No unapproved image for a real model");
assert.equal(benchPhotoFor(scs),null,"No unapproved accessory photo");
assert.equal(benchPhotoFor(standard),null);
assert.equal(benchPhotoFor(null),null);
const photo=benchPhotoFor(ruger);
assert.ok(photo);
assert.equal(photo.kind,"cc-research");
assert.match(photo.credit,/Coati077.*CC BY-SA 4\.0/);
assert.match(photo.src,/^https:\/\/upload\.wikimedia\.org\//);
assert.equal(benchPhotoFor({...ruger,approvedItem:{id:"catalog_fake"}}),null,
 "Research photo cannot replace a public catalog record");
assert.equal(benchEvidenceFor(mos,scs).status,"manufacturer-listed");
assert.equal(benchEvidenceFor(standard,scs).status,"factory-interface-differs");
assert.equal(benchEvidenceFor(mos,tlr).status,"family-guidance");
assert.equal(benchEvidenceFor(ruger,scs).status,"not-reviewed");
assert.equal(benchEvidenceFor(mos,null).status,"none");
const valid=shareBenchUrl(
 "https://area33armory.com/product-room.html?untrusted=1&product=wrong#bad",
 mos,scs
);
assert.equal(valid,"https://area33armory.com/product-room.html?product=glock-g19-gen5-mos&accessory=holosun-scs-m-gr");
assert.equal(shareBenchUrl("https://area33armory.com/product-room.html",mos,null),
 "https://area33armory.com/product-room.html?product=glock-g19-gen5-mos");
assert.equal(shareBenchUrl("file:///private/product-room.html",mos,scs),null);
assert.equal(shareBenchUrl("https://area33armory.com/product-room.html",{...mos,id:"made-up"},null),null);
assert.equal(shareBenchUrl("https://area33armory.com/product-room.html",mos,{...scs,id:"invented"}),null);
assert.equal(shareBenchUrl("javascript:alert(1)",mos,scs),null);
assert.equal(shareBenchUrl("https://name:pass@area33armory.com/product-room.html",mos,scs),null);
assert.equal(INSPIRATION_MEDIA.length,1);
const insp=inspirationForEditorial("real-world-customization-example");
assert.ok(insp&&verifyInspiration(insp));
assert.equal(insp.creator,"Tony Webster");
assert.equal(insp.license,"CC BY 2.0");
assert.equal(new URL(insp.src).hostname,"thumb.wikimedia.org");
assert.equal(new URL(insp.source).hostname,"commons.wikimedia.org");
assert.match(insp.caption,/not the product you selected/i);
assert.equal(inspirationForEditorial("invalid"),null);
assert.equal(verifyInspiration({...insp,src:"https://example.com/other.jpg"}),false);
assert.equal(verifyInspiration({...insp,license:"All rights reserved"}),false);
const html=fs.readFileSync(new URL("../product-room.html",import.meta.url),"utf8");
const script=fs.readFileSync(new URL("../assets/product-room.js",import.meta.url),"utf8");
const bench=fs.readFileSync(new URL("../assets/experience-bench.mjs",import.meta.url),"utf8");
const css=fs.readFileSync(new URL("../assets/product-room.css",import.meta.url),"utf8");
for(const id of ["hands-on-bench","bench-pair-pane","bench-inspiration-pane","bench-tab-selection","bench-tab-inspiration",
"bench-firearm-image","bench-accessory-image","bench-firearm-no-image","bench-accessory-no-image",
"bench-firearm-name","bench-accessory-name","bench-proof-summary","bench-proof-badge",
"bench-inspiration-photo","bench-inspiration-source","bench-inspiration-creator","bench-inspiration-license",
"bench-link-copy","bench-clear-accessory","bench-copy-status"]){
 assert.match(html,new RegExp('id="'+id+'"'),"Missing "+id);
}
assert.match(html,/role="tablist"/);
assert.match(html,/role="tabpanel"/);
for(const id of ["holosun-scs-m-gr","holosun-hs507k-x2","streamlight-tlr7-x","aliengear-photon"])
 assert.match(html,new RegExp('data-bench-try="'+id+'"'));
assert.match(script,/import \{createExperienceBench\} from "\.\/experience-bench\.mjs"/);
assert.match(script,/experienceBench\.render\(current,accessory\)/);
assert.match(script,/onClearAccessory:\(\)=>selectAccessoryCategory/);
assert.match(bench,/galleryAllowed\(item\.approvedItem\)/);
assert.match(bench,/researchPhotoFor\(item\)/);
assert.match(bench,/img\.hidden=!photo/);
assert.match(bench,/onChooseAccessory/);
assert.match(bench,/onClearAccessory/);
assert.match(bench,/shareBenchUrl\(location\.href/);
assert.match(bench,/navigator\.clipboard\?\.writeText/);
assert.match(bench,/shownInspiration=false/);
assert.doesNotMatch(bench,/innerHTML|localStorage|sessionStorage|dealer_cost|private_supplier/);
assert.doesNotMatch(html,/<iframe/);
assert.match(css,/\.room-bench-items/);
assert.match(css,/\.room-inspiration-photo/);
console.log("Area 33 hands-on bench: real identities, independent licensed photo gates, explicit swap, state restoring permalink, accessible editorial tab, uncertainty and no dealer data verified.");
