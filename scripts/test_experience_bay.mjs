import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
const html=fs.readFileSync(new URL("../experience-bay.html",import.meta.url),"utf8");
const home=fs.readFileSync(new URL("../index.html",import.meta.url),"utf8");
assert.match(html,/<!doctype html>/i);
assert.match(html,/Come in\./);
assert.match(html,/Get curious\./);
assert.match(html,/Surprise me/);
assert.match(html,/Experience Bay/);
assert.match(home,/href="experience-bay\.html"/);
assert.match(home,/Browse the catalog/,"New homepage prioritizes customer-facing product browsing");
assert.match(home,/id="lz33"/,"Hero real estate now hosts the LZ33 promotion, not a redundant product photo");
assert.match(home,/id="lz33-hero-inspect"/,"An approved landing can link to the product counter");
assert.match(home,/href="studio\.html"/);
assert.match(home,/href="showroom\.html"/);
assert.match(html,/No live supplier prices, inventory or checkout are connected/);
assert.match(html,/Original concept art/);
assert.match(html,/not a true 3D model/i);
assert.match(html,/scripted concept explanations, not live AI/i);
assert.doesNotMatch(html,/private_distributor|private_dealer|dealer_cost|source_sku|localStorage|sessionStorage/);
assert.doesNotMatch(html,/<iframe|<script[^>]+src=|<link[^>]+stylesheet[^>]+href=/);
const idList=[...html.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]);
const unique=new Set(idList);
assert.equal(unique.size,idList.length,"Duplicate ID attributes in experience bay");
for(const id of ["board","scene","optic-compact","optic-long","light-compact",
 "counter-answer","intel-heading","intel-story","selection-status",
 "view-status","view-label","angle-output","zoom-output","copy-summary",
 "compare","reset-scene","turn-left","turn-right","zoom-in","zoom-out",
 "copy","share","share-status","shelf-title","workbench"]){
 assert.ok(unique.has(id),"Missing interactive ID: "+id);
}
for(const choice of ["surprise","explore","customize","intelligence"]){
 assert.ok(html.includes('data-journey="'+choice+'"'),"Missing journey "+choice);
}
for(const kind of ["finish","optic","light"]){
 assert.ok(html.includes('data-part="'+kind+'"'),"Missing accessory category "+kind);
}
for(const question of ["difference","fit","value","discover"]){
 assert.ok(html.includes('data-question="'+question+'"'),"Missing explanation "+question);
}
const matches=[...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)];
assert.equal(matches.length,1,"One self-contained interactive script");
new vm.Script(matches[0][1],{filename:"experience-bay.inline.js"});
const context=vm.createContext({});
vm.runInContext(matches[0][1],context);
const evalIn=(str)=>vm.runInContext(str,context);
assert.equal(evalIn('cleanState({finish:"sand",optic:"compact",light:"compact"}).finish'),"sand");
assert.equal(evalIn('cleanState({finish:"CORRUPT",optic:"fake",light:"unknown"}).optic'),"none");
assert.equal(evalIn('cleanState(null).finish'),"graphite");
assert.equal(evalIn('nextTurn(26,13)'),26);
assert.equal(evalIn('nextTurn(-26,-13)'),-26);
assert.equal(evalIn('nextTurn(0,13)'),13);
assert.match(evalIn('conceptSummary({finish:"sand",optic:"long",light:"compact"})'),/sand finish/);
assert.match(evalIn('conceptSummary({finish:"sand",optic:"long",light:"compact"})'),/no exact product, compatibility, stock or price verified/i);
for(const id of ["clean","focus","unexpected"]){
 assert.equal(evalIn('Boolean(looks["'+id+'"].story)'),true);
}
assert.equal((html.match(/<svg\b/g)||[]).length,1);
assert.ok(html.includes("role=\"img\""));
console.log("Area 33 Experience Bay: functional state contract, original illustrative media, discovery paths, live-data disclaimers and home links verified.");
