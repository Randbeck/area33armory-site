import assert from "node:assert/strict";
import fs from "node:fs";
import {REFERENCE_PRODUCTS} from "../assets/product-room-research.mjs";
import {SIX_VIEW_SCHEMA,ANGLES,validateSixViewManifest,getViewsForProduct,pickFirstView,
 curatedAccessorySet,researchPackage,buildResearchShareUrl} from "../assets/six-view-contract.mjs";
import {researchPhotoFor} from "../assets/research-photo-license.mjs";
import {evaluatePairing} from "../assets/pairing-evidence.mjs";
const product=id=>REFERENCE_PRODUCTS.find(x=>x.id===id);
const rifle=product("ruger-precision-308-gen1"),other=product("ruger-precision-6mm-2019-photo");
const pistol=product("glock-g19-gen5-mos"),shotgun=product("beretta-a300-patrol");
const scope=product("meopta-optika6-3-18x56-rd-sfp"),holster=product("aliengear-photon");
const optic=product("holosun-scs-m-gr");
assert.equal(SIX_VIEW_SCHEMA,"area33.six-view.public.v1");
assert.deepEqual(ANGLES,["left","right","top","bottom","front","rear"]);
const empty=JSON.parse(fs.readFileSync(new URL("../assets/multiview-public.json",import.meta.url),"utf8"));
const accepted=validateSixViewManifest(empty,{origin:"https://area33armory.com"});
assert.deepEqual(accepted,[],"Draft must not publish directional photos without manual approval");
const views=getViewsForProduct(rifle,accepted);
assert.equal(views.count,0,"One real photo must not magically become six directions");
assert.equal(views.reference.src,researchPhotoFor(rifle).src);
assert.equal(views.reference.sourcePage,researchPhotoFor(rifle).sourcePage);
assert.equal(pickFirstView(views,"left").angle,"reference");
assert.equal(pickFirstView(views,"reference").angle,"reference");
assert.ok(views.angles.every(x=>!x.available&&x.mode==="pending"));
assert.notEqual(researchPhotoFor(rifle).src,researchPhotoFor(other).src);
assert.equal(getViewsForProduct(pistol,accepted).reference,null);
assert.equal(getViewsForProduct(shotgun,accepted).count,0);
assert.equal(getViewsForProduct(holster,accepted).count,0,"Accessory photos must never stand in for firearm angles");
const local={left:{src:"blob:test-left",alt:"Local left"},top:{src:"blob:test-top",alt:"Local top"}};
const withLocal=getViewsForProduct(rifle,accepted,local);
assert.equal(withLocal.count,2);
assert.equal(pickFirstView(withLocal,"left").photo.src,"blob:test-left");
assert.equal(pickFirstView(withLocal,"top").mode,"local-preview");
assert.equal(pickFirstView(withLocal,"bottom").angle,"left","Missing angles fall back to documented local view");
assert.equal(getViewsForProduct(other,accepted).count,0,"Never leak local photos across different SKUs or calibers");
const example={productId:rifle.id,angle:"left",src:"assets/approved/multiview/ruger-precision-308-gen1/left.jpg",
 alt:"Photographed left side of an exact Ruger Precision Rifle Gen 1 .308",credit:"Owner approved photographer",
 rights:"approved",verifiedExactItem:true,reviewedAt:"2026-11-08",
 sourcePage:"https://commons.wikimedia.org/wiki/File:Ruger_Precision_Rifle_308_Gen_1.jpg"};
const manifest=views=>({schema:SIX_VIEW_SCHEMA,views});
const good=validateSixViewManifest(manifest([example]),{origin:"https://area33armory.com"});
assert.equal(good?.length,1);
assert.equal(good[0].src,"https://area33armory.com/assets/approved/multiview/ruger-precision-308-gen1/left.jpg");
assert.equal(getViewsForProduct(rifle,good).count,1);
assert.equal(validateSixViewManifest(manifest([example,example])),null,"Duplicate directions forbidden");
assert.equal(validateSixViewManifest(manifest([{...example,productId:other.id}])),null,"No cross-model file substitution");
assert.equal(validateSixViewManifest(manifest([{...example,angle:"right"}])),null,"No labeling same left photo as right view");
assert.equal(validateSixViewManifest(manifest([{...example,verifiedExactItem:false}])),null);
assert.equal(validateSixViewManifest(manifest([{...example,rights:"pending"}])),null);
assert.equal(validateSixViewManifest(manifest([{...example,src:"https://other.example/left.jpg"}])),null);
assert.equal(validateSixViewManifest(manifest([{...example,sourcePage:"javascript:alert(1)"}])),null);
assert.equal(validateSixViewManifest(manifest([{...example,unapprovedKey:"extra"}])),null);
assert.equal(validateSixViewManifest(manifest([{...example,reviewedAt:"bad"}])),null);
assert.equal(validateSixViewManifest({schema:SIX_VIEW_SCHEMA,views:"no"}),null);
const rifleMatches=curatedAccessorySet(rifle,REFERENCE_PRODUCTS.filter(x=>x.kind==="accessory"));
assert.deepEqual(rifleMatches.map(x=>x.item.id),[scope.id],"Precision rifle should prioritize magnified scope, not holsters or handgun optics");
assert.equal(rifleMatches[0].pairing.status,"not-reviewed","Sensible category is not confirmed exact mounting");
assert.equal(curatedAccessorySet(rifle,[holster]).length,0);
const pistolMatches=curatedAccessorySet(pistol,[optic,holster]);
assert.equal(pistolMatches.length,2);
assert.equal(pistolMatches.find(x=>x.item.id===optic.id).pairing.status,"manufacturer-listed");
assert.equal(evaluatePairing(pistol,holster).status,"not-reviewed");
assert.equal(curatedAccessorySet(shotgun,[optic,scope,holster]).length,0);
const pkg=researchPackage(rifle,[scope.id,scope.id,holster.id,"invalid"]);
assert.equal(pkg.lines.length,3);
assert.equal(pkg.total,null);assert.equal(pkg.quoteReady,false);
assert.ok(pkg.lines.every(x=>x.price===null));
assert.equal(pkg.lines[1].status,"No exact pairing evidence");
const url=buildResearchShareUrl("http://127.0.0.1:8766/six-view-counter.html?utm_source=chatgpt.com#junk",rifle,[scope.id,scope.id,holster.id,"garbage"],"top");
assert.ok(url.includes("product=ruger-precision-308-gen1"));
assert.ok(url.includes("view=top"));
assert.equal((url.match(/accessory=/g)||[]).length,2);
assert.ok(!url.includes("utm_source")&&!url.includes("#junk"));
assert.equal(buildResearchShareUrl("javascript:alert(1)",rifle,[]),null);
const html=fs.readFileSync(new URL("../six-view-counter.html",import.meta.url),"utf8");
const js=fs.readFileSync(new URL("../assets/six-view-counter.js",import.meta.url),"utf8");
const css=fs.readFileSync(new URL("../assets/six-view-counter.css",import.meta.url),"utf8");
for(const id of ["view-stage","main-photo","image-space","angles-grid","coverage-number","reference-view",
 "zoom-in","zoom-out","zoom-amount","reset-image","fullscreen","local-direction","local-photo","local-status","clear-local",
 "product-brand","product-model","manufacturer-link","browse-all","accessory-choices","accessory-detail","accessory-photo",
 "accessory-evidence","fit-label","package-lines","package-total","clear-package","copy-selection","copy-result"]){
 assert.ok(html.includes('id="'+id+'"'),"Missing six-view UI "+id);
 assert.ok(js.includes('$("'+id+'")'),"Missing UI handler "+id);
}
assert.equal([...html.matchAll(/\bid="([^"]+)"/g)].length,
 new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1])).size,"Unique DOM IDs required");
assert.ok(html.includes('content="Area 33 multi-angle product counter'));
assert.match(js,/URL\.createObjectURL\(file\)/);
assert.match(js,/URL\.revokeObjectURL\(existing\.src\)/);
assert.match(js,/window\.addEventListener\("beforeunload",cleanupLocal\)/);
assert.match(js,/getViewsForProduct\(selected,approvedViews,localFor\(selected\.id\)\)/);
assert.match(js,/validateSixViewManifest\(manifest/);
assert.match(js,/researchPhotoFor\(item\)/);
assert.match(js,/No sharable research selection/);
assert.doesNotMatch(js,/localStorage|sessionStorage|FormData|fetch\([^)]*POST|dealer_cost|private_supplier|checkout/);
assert.doesNotMatch(html,/three-dimensional|3D rotation|interactive 3D/i,"This batch is photo-only");
assert.match(css,/\.scene-shell/);
assert.match(html,/Quote pending/);
assert.match(html,/Files are never uploaded, saved or published/);
console.log("Six-view counter: exact photo rights, six unavailable angles, local preview isolation, contextual accessories, itemized unquoted package and share URL verified.");
