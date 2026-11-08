import assert from "node:assert/strict";
import fs from "node:fs";
import {REFERENCE_PRODUCTS,researchTitle} from "../assets/product-room-research.mjs";
import {getViewsForProduct} from "../assets/six-view-contract.mjs";
import {EXPERIENCE_SCHEMA,PUBLIC_COVERAGE,FIREARMS,ACCESSORIES,
 relatedReferences,variantDisclosure,findResearchProducts,nextDiscovery,
 makeComparison,accessoryIntelligence,allInQuoteStatus,interpretResearchQuestion} from "../assets/customer-experience.mjs";
const item=id=>REFERENCE_PRODUCTS.find(x=>x.id===id);
const glock=item("glock-g19-gen5-mos"),standard=item("glock-g19-gen5");
const rifle=item("ruger-precision-308-gen1"),scope=item("meopta-optika6-3-18x56-rd-sfp");
const optic=item("holosun-scs-m-gr"),holster=item("aliengear-photon");
assert.equal(EXPERIENCE_SCHEMA,"area33.customer-experience.v1");
assert.match(PUBLIC_COVERAGE,/not the integrated distributor catalog/i);
assert.ok(FIREARMS.length>=8&&ACCESSORIES.length>=5);
assert.ok(findResearchProducts("glock").some(x=>x.id===glock.id));
assert.ok(findResearchProducts("precision","rifles").some(x=>x.id===rifle.id));
assert.ok(!findResearchProducts("precision","pistols").length);
assert.ok(findResearchProducts("nonexistentexample").length===0);
assert.equal(findResearchProducts("","all").length,FIREARMS.length,"No 3-result shortlist limit");
assert.notEqual(nextDiscovery(FIREARMS,glock.id,0)?.id,null);
assert.notEqual(nextDiscovery([glock,standard],glock.id,0)?.id,glock.id);
assert.equal(nextDiscovery([],glock.id),null);
const related=relatedReferences(glock);
assert.deepEqual(related.map(x=>x.id),[standard.id],"GLOCK Gen5 vs MOS are research variants, not identical SKUs");
assert.ok(!relatedReferences(glock).some(x=>x.id==="glock-g43x-mos"),"Slimline MOS is not same family");
const variants=variantDisclosure(rifle);
assert.ok(variants.related.some(x=>x.id==="ruger-precision-6mm-2019-photo"));
assert.ok(variants.description.includes("NOT a complete list"));
assert.deepEqual(variantDisclosure(glock).verifiedColors,[],"Do not invent a finish catalog");
assert.equal(getViewsForProduct(rifle,[]).count,0,"One research image not a six-sided product spin");
const comp=makeComparison([glock,glock,standard,rifle,scope]);
assert.equal(comp.length,3);
assert.equal(comp[0].id,glock.id);assert.equal(comp[1].id,standard.id);
assert.ok(comp.every(x=>x.pricing==="Not quoted"&&x.availability==="Not verified"));
assert.equal(accessoryIntelligence(glock,optic).pairing.status,"manufacturer-listed");
assert.equal(accessoryIntelligence(glock,holster).pairing.status,"not-reviewed");
assert.equal(accessoryIntelligence(rifle,holster).relevance.tier,"not-applicable");
assert.equal(accessoryIntelligence(rifle,scope).relevance.tier,"explore");
assert.equal(accessoryIntelligence(rifle,scope).verifiedPhysicalFit,false);
const answer=interpretResearchQuestion(glock,"Which accessories fit?",{selectedAccessories:[optic.id,holster.id]});
assert.match(answer.text,/manufacturer-listed|Manufacturer-listed|Manufacturer family|direct mount/i);
assert.match(answer.text,/No exact pairing evidence/i);
assert.ok(answer.sources.some(x=>x.url.startsWith("https://")));
assert.equal(answer.isLiveAI,false);
assert.match(interpretResearchQuestion(glock,"Show every finish").text,/not a complete list/i);
assert.match(interpretResearchQuestion(rifle,"What is the total price?").text,/tax|shipping/i);
assert.match(interpretResearchQuestion(glock,"Is it available to buy?").text,/not a live inventory listing/i);
assert.match(interpretResearchQuestion(glock,"Quantum something unknown").text,/not live Thinking Room/i);
assert.match(interpretResearchQuestion(glock,"How does it differ?",{comparison:[standard]}).text,/G19 Gen5/);
const notReady=allInQuoteStatus();
assert.equal(notReady.confirmed,false);assert.equal(notReady.totalMinor,null);
assert.ok(notReady.blockers.length>=4);
assert.equal(allInQuoteStatus({zip:"abcde",receivingDealerName:"A",dealerFeeKnown:true}).confirmed,false);
const items=[{id:glock.id,publicSkuVerified:true,stockVerified:true}];
const goodQuote={verified:true,isPublicCustomerQuote:true,totalMinor:158735,
 includesTax:true,includesShipping:true,includesTransferFee:true,includesAllOtherFees:true,
 expiresAt:"2099-01-01T00:00:00Z"};
const ready={zip:"63640",receivingDealerName:"Example FFL",dealerFeeKnown:true,selectedProducts:items,sourceQuote:goodQuote};
assert.equal(allInQuoteStatus(ready).confirmed,true);
assert.equal(allInQuoteStatus(ready).totalMinor,158735);
for(const change of [{dealerFeeKnown:false},{zip:"1234"},{selectedProducts:[{id:glock.id,publicSkuVerified:false,stockVerified:true}]},
 {sourceQuote:{...goodQuote,includesTax:false}},{sourceQuote:{...goodQuote,expiresAt:"2000-01-01T00:00:00Z"}}]){
 assert.equal(allInQuoteStatus({...ready,...change}).confirmed,false,"Do not guarantee a price with missing fee, identity, tax or freshness");
}
const html=fs.readFileSync(new URL("../six-view-counter.html",import.meta.url),"utf8");
const js=fs.readFileSync(new URL("../assets/customer-experience-ui.js",import.meta.url),"utf8");
const css=fs.readFileSync(new URL("../assets/customer-experience.css",import.meta.url),"utf8");
const main=fs.readFileSync(new URL("../assets/six-view-counter.js",import.meta.url),"utf8");
for(const id of ["discover-counter","surprise-discovery","discovery-search","discovery-department","clear-discovery",
 "discovery-results","variant-results","thinking-room","thinking-conversation","thinking-query","thinking-form",
 "thinking-suggestions","thinking-product-context","compare-current","clear-compare","compare-cards",
 "save-current","saved-discoveries","all-in-form","delivery-zip","ffl-name","ffl-fee-known",
 "all-in-label","quote-blockers","all-in-caption"]){
 assert.ok(html.includes('id="'+id+'"'),"Missing integrated storefront node "+id);
 assert.ok(js.includes('$("'+id+'")'),"Missing interaction handler "+id);
}
assert.match(html,/Full conversational Randbeck AI is <strong>not yet connected/);
assert.match(html,/No total can be promised yet/);
assert.match(js,/interpretResearchQuestion\(state\.product/);
assert.match(js,/goToCounter\(item\.id\)/);
assert.match(js,/renderVariants\(\)/);
assert.match(js,/allInQuoteStatus\(/);
assert.match(main,/new CustomEvent\("area33:counter-update"/);
assert.match(js,/window\.addEventListener\("area33:counter-update",syncFromCounter\)/);
assert.match(js,/new Event\("change",\{bubbles:true\}\)/);
assert.match(js,/state\.saved=/);
assert.doesNotMatch(js,/localStorage|sessionStorage|credentials|private_supplier|dealer_cost|Authorization|fetch\(/);
assert.doesNotMatch(html,/<script\b(?![^>]*\bsrc=)[^>]*>[\s\S]*<\/script>/i);
assert.equal([...html.matchAll(/\bid="([^"]+)"/g)].length,new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1])).size);
assert.match(css,/\.discovery-hub/);assert.match(css,/\.thinking-panel/);assert.match(css,/\.all-in-workspace/);
console.log("Area 33 integrated discovery: catalog exploration without shortlist truncation, accurate variants, evidence Q&A, comparisons, session saves, and strict all-in quote readiness verified.");
