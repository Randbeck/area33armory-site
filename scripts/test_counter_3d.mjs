import assert from "node:assert/strict";
import fs from "node:fs";
import {COUNTER_SCENE_SCHEMA,FINISHES,buildConceptMesh,transformPoint,projectPoint,
 clampCamera,reticleScale,samplePackage} from "../assets/counter-3d-scene.mjs";
import {REFERENCE_PRODUCTS} from "../assets/product-room-research.mjs";
import {evaluatePairing} from "../assets/pairing-evidence.mjs";
const html=fs.readFileSync(new URL("../counter-3d.html",import.meta.url),"utf8");
const code=fs.readFileSync(new URL("../assets/counter-3d.js",import.meta.url),"utf8");
const css=fs.readFileSync(new URL("../assets/counter-3d.css",import.meta.url),"utf8");
assert.equal(COUNTER_SCENE_SCHEMA,"area33.counter.scene.v1");
assert.deepEqual(Object.keys(FINISHES),["graphite","sand","slate"]);
for(const finish of Object.keys(FINISHES)){
 const plain=buildConceptMesh({finish}),wOptic=buildConceptMesh({finish,optic:true});
 assert.ok(plain.faces.length>30&&plain.lines.length>10,"Must render actual 3D geometry");
 assert.ok(wOptic.faces.length>plain.faces.length,"Optic visibly represented as separate geometric volume");
 assert.equal(plain.conceptOnly,true);assert.equal(plain.exactProduct,false);
 for(const f of wOptic.faces){assert.ok(f.points.length>=3);for(const p of f.points)assert.ok(p.length===3&&p.every(Number.isFinite),"Every face must have 3D numeric coordinates");}
}
const p=[1,2,3];
assert.deepEqual(transformPoint(p,{yaw:0,pitch:0}),p);
const rotated=transformPoint(p,{yaw:Math.PI,pitch:0});
assert.ok(Math.abs(rotated[0]+1)<1e-9&&Math.abs(rotated[2]+3)<1e-9,"Orbit must change geometry's three-dimensional perspective");
assert.notDeepEqual(projectPoint(p,{yaw:0,pitch:0,zoom:1},600,400),projectPoint(p,{yaw:1,pitch:.3,zoom:1},600,400),"Camera orbit must change actual projected coordinates");
assert.equal(clampCamera({zoom:999,pitch:99}).zoom,2.1);
assert.equal(clampCamera({zoom:-10,pitch:-99}).pitch,-1.42);
assert.equal(reticleScale(2,"ffp"),.5);
assert.equal(reticleScale(8,"ffp"),2);
assert.equal(reticleScale(2,"sfp"),1);
assert.equal(reticleScale(8,"sfp"),1);
const empty=samplePackage(),all=samplePackage(["holosun-scs-m-gr","streamlight-tlr7-x","aliengear-photon"]);
assert.equal(empty.total,650);assert.equal(all.total,1195);
assert.equal(samplePackage(["holosun-scs-m-gr","holosun-scs-m-gr"]).total,975,"Do not double charge repeated selection");
assert.equal(all.isQuote,false);assert.equal(all.verified,false);
const firearm=REFERENCE_PRODUCTS.find(x=>x.id==="glock-g19-gen5-mos");
const optic=REFERENCE_PRODUCTS.find(x=>x.id==="holosun-scs-m-gr");
const light=REFERENCE_PRODUCTS.find(x=>x.id==="streamlight-tlr7-x");
const holster=REFERENCE_PRODUCTS.find(x=>x.id==="aliengear-photon");
assert.equal(evaluatePairing(firearm,optic).status,"manufacturer-listed");
assert.equal(evaluatePairing(firearm,light).status,"family-guidance");
assert.equal(evaluatePairing(firearm,holster).status,"not-reviewed");
for(const phrase of ["illustrative procedural pistol model","not a 3D scan","invented demonstration figures","not current prices","not sellable configurations"]){
 assert.ok(html.toLowerCase().includes(phrase.toLowerCase()),"Demo honesty must be prominent: "+phrase);
}
for(const id of ["model-canvas","mode-blueprint","mode-finish","mode-transition","view-left","view-right","view-top",
 "view-reset","spin-toggle","zoom-minus","zoom-plus","zoom-status","evidence-status","evidence-copy","evidence-source",
 "reticle-canvas","ffp","sfp","magnification","mag-label","focal-copy","receipt-lines","total","reset-selection","copy-summary","copy-status"]){
 assert.ok(html.includes('id="'+id+'"'),"Missing control "+id);
 assert.ok(code.includes('$("'+id+'")'),"Missing JS control "+id);
}
assert.equal([...html.matchAll(/\bid="([^"]+)"/g)].length,new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1])).size,"Unique DOM IDs");
assert.match(code,/paintConcept\(stageCtx/);
assert.match(code,/stage\.addEventListener\("pointermove"/);
assert.match(code,/stage\.addEventListener\("wheel"/);
assert.match(code,/mode-transition/);
assert.match(code,/evaluatePairing\(reference,products\.get\("holosun-scs-m-gr"\)\)\.status==="manufacturer-listed"/);
assert.match(code,/samplePackage\(\[\.\.\.chosen\]\)/);
assert.match(css,/\.viewport canvas/);
assert.doesNotMatch(code,/localStorage|sessionStorage|dealer_cost|private_supplier|checkout|fetch\(/);
assert.doesNotMatch(html,/<iframe|<script\b(?![^>]*\bsrc=)[^>]*>[\s\S]*<\/script>/i);
console.log("Area 33 3D pilot: real geometric orbit/projection, optic evidence gate, visual states, reticle focal-plane scaling and nonbinding package verified.");
