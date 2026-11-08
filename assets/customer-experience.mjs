/* Area 33 customer intelligence contract (offline research preview).
 * The public app NEVER receives Randbeck dealer prices, supplier secrets or
 * private reasoning. This is deterministic context evidence, NOT live AI.
 * Future Randbeck adapter must return sanitized, authorized public answers.
 */
import {REFERENCE_PRODUCTS,researchTitle} from "./product-room-research.mjs";
import {evaluatePairing} from "./pairing-evidence.mjs";
import {reviewAccessoryContext,firearmContext} from "./accessory-context.mjs";
export const EXPERIENCE_SCHEMA="area33.customer-experience.v1";
export const PUBLIC_COVERAGE="Curated manufacturer research references only — not the integrated distributor catalog or confirmed inventory.";
export const FIREARMS=Object.freeze(REFERENCE_PRODUCTS.filter(item=>item.kind==="firearm"));
export const ACCESSORIES=Object.freeze(REFERENCE_PRODUCTS.filter(item=>item.kind==="accessory"));
const FAMILY_MAP=Object.freeze({
 "glock-g19-gen5":"glock-g19-gen5-family",
 "glock-g19-gen5-mos":"glock-g19-gen5-family",
 "ruger-precision-308-gen1":"ruger-precision-family",
 "ruger-precision-6mm-2019-photo":"ruger-precision-family",
 "ruger-precision":"ruger-precision-family"
});
export function relatedReferences(product,all=FIREARMS){
 if(!product||product.kind!=="firearm")return [];
 const family=FAMILY_MAP[product.id];
 return family?all.filter(x=>x.id!==product.id&&FAMILY_MAP[x.id]===family):[];
}
/* Do not call family research references actual current color/SKU options. */
export function variantDisclosure(product,all=FIREARMS){
 const related=relatedReferences(product,all);
 return {related,verifiedColors:[],
  description:related.length?"Related research models and photographed examples only. These may differ in generation, caliber, finish, mounting interface and SKU; this is NOT a complete list of available finishes or model variants.":
  "No verified variants or finish inventory in this limited public research set. Do not invent colors or assume other configurations are available."};
}
export function findResearchProducts(query="",department="all",all=FIREARMS){
 const terms=String(query||"").toLowerCase().trim().split(/\s+/).filter(Boolean);
 return all.filter(item=>(department==="all"||item.department===department)&&
   terms.every(t=>[item.brand,item.model,item.subtitle,item.note,...(item.facts||[])].join(" ").toLowerCase().includes(t)))
  .sort((a,b)=>researchTitle(a).localeCompare(researchTitle(b)));
}
export function nextDiscovery(items,currentId,cursor=0){
 if(!Array.isArray(items)||!items.length)return null;
 const sorted=items.slice().sort((a,b)=>a.id.localeCompare(b.id));
 let i=((Math.floor(cursor)%sorted.length)+sorted.length)%sorted.length;
 if(sorted.length>1&&sorted[i].id===currentId)i=(i+1)%sorted.length;
 return sorted[i];
}
export function makeComparison(items=[]){
 const filtered=[],seen=new Set();
 for(const x of items){if(!x||x.kind!=="firearm"||seen.has(x.id))continue;
  seen.add(x.id);filtered.push(x);if(filtered.length===3)break;}
 return filtered.map(x=>({id:x.id,title:researchTitle(x),type:x.department,
  description:x.subtitle||"Manufacturer research reference",facts:x.facts||[],
  variantCaution:x.note||"Exact SKU must be independently verified",
  source:x.source,pricing:"Not quoted",availability:"Not verified"}));
}
/* Provenance is maintained per exact firearm/accessory identity, not category. */
export function accessoryIntelligence(firearm,accessory){
 if(!firearm||!accessory)return null;
 const relevance=reviewAccessoryContext(firearm,accessory),pairing=evaluatePairing(firearm,accessory);
 return {relevance,pairing,verifiedPhysicalFit:false,visualMountAuthorized:false,
  source:pairing.evidence?.[0]?.url||accessory.source};
}
const ZIP=/^\d{5}$/;
export function allInQuoteStatus({zip="",receivingDealerName="",dealerFeeKnown=false,selectedProducts=[],sourceQuote=null}={}){
 const inputs={
  destinationKnown:ZIP.test(String(zip).trim()),
  dealerSelected:typeof receivingDealerName==="string"&&receivingDealerName.trim().length>=2,
  dealerFeeConfirmed:dealerFeeKnown===true
 };
 const verifiedSource=sourceQuote?.verified===true&&sourceQuote?.isPublicCustomerQuote===true&&
  Number.isInteger(sourceQuote?.totalMinor)&&sourceQuote.totalMinor>=0&&
  sourceQuote?.includesTax===true&&sourceQuote?.includesShipping===true&&
  sourceQuote?.includesTransferFee===true&&sourceQuote?.includesAllOtherFees===true&&
  typeof sourceQuote?.expiresAt==="string"&&Number.isFinite(Date.parse(sourceQuote.expiresAt))&&
  Date.parse(sourceQuote.expiresAt)>Date.now();
 const completeItems=Array.isArray(selectedProducts)&&selectedProducts.length>0&&
  selectedProducts.every(item=>item&&item.publicSkuVerified===true&&item.stockVerified===true);
 const confirmed=inputs.destinationKnown&&inputs.dealerSelected&&inputs.dealerFeeConfirmed&&completeItems&&verifiedSource;
 const blockers=[];
 if(!inputs.destinationKnown)blockers.push("Enter a five-digit destination ZIP to determine the relevant tax and delivery region.");
 if(!inputs.dealerSelected)blockers.push("Select the receiving FFL dealer.");
 if(!inputs.dealerFeeConfirmed)blockers.push("Confirm the receiving dealer's transfer fee or Area 33's agreed coverage.");
 if(!completeItems)blockers.push("Exact sellable SKUs and current sourceable stock need verification.");
 if(!verifiedSource)blockers.push("Randbeck must supply a fresh all-in customer quote including tax, shipping, transfer and other applicable fees.");
 return {confirmed,totalMinor:confirmed?sourceQuote.totalMinor:null,blockers,
  label:confirmed?"Verified all-in customer quote":"ALL-IN PRICE PENDING",
  notice:confirmed?"Public quote verified. Honor the listed quote expiry and seller terms.":
  "No one-price guarantee can be made until destination, dealer fees, stock and source costs are confirmed.",
  inputs};
}
const safeText=s=>String(s||"").slice(0,500).trim();
export function interpretResearchQuestion(product,question,{selectedAccessories=[],comparison=[]}={}){
 if(!product||product.kind!=="firearm")return {heading:"Choose a product first",text:"Select a real manufacturer reference to explore its research notes.",sources:[],mode:"research-preview"};
 const q=safeText(question).toLowerCase(),title=researchTitle(product);
 const base={sources:[{label:"Official manufacturer or product reference",url:product.source}],mode:"research-preview",isLiveAI:false};
 if(!q)return {...base,heading:"Ask about "+title,text:"Ask about known details, related models, finishes, accessories, comparisons, availability or the all-in price."};
 if(/price|cost|shipping|tax|fee|transfer|total|cheap|deal/.test(q))return {...base,heading:"One price should mean everything",text:"There is no verified customer quote for this research reference. An Area 33 all-in price must cover the product, applicable tax, shipping, handling, receiving FFL transfer fee and any other applicable charges. We must first verify your location, receiving dealer, sellable SKU and current source. No amount is invented."};
 if(/stock|inventory|available|order|purchase|buy|deliver/.test(q))return {...base,heading:"Availability needs live verification",text:"This research card is not a live inventory listing. We cannot promise sourceable stock, delivery or purchase eligibility without an approved distributor quote and current public listing."};
 if(/color|finish|variant|version|model|caliber|option/.test(q)){
  const v=variantDisclosure(product);
  return {...base,heading:"Known related references for "+title,
    text:v.related.length?"Known research references: "+v.related.map(researchTitle).join("; ")+". "+v.description:v.description};
 }
 if(/fit|compatib|mount|optic|holster|accessor|light|scope|rail/.test(q)){
  const selected=ACCESSORIES.filter(x=>selectedAccessories.includes(x.id));
  const details=selected.length?selected.map(a=>{
    const match=accessoryIntelligence(product,a);
    return researchTitle(a)+": "+match.pairing.short+". "+match.relevance.reason;
  }).join(" "):"Nothing selected yet. "+firearmContext(product).message;
  return {...base,heading:"Accessory evidence — not assumed fit",text:details+" Manufacturer-listed fit is not an independent physical inspection. Exact variants and combined configurations require review.",
   sources:[...base.sources,...selected.flatMap(a=>evaluatePairing(product,a).evidence.map(e=>({label:e.label,url:e.url})))].slice(0,6)};
 }
 if(/compar|differ|better|versus|vs\b/.test(q)){
  const other=comparison.filter(x=>x.id!==product.id);
  return {...base,heading:"Comparison at the counter",
   text:other.length?"Compared with "+other.map(researchTitle).join(", ")+". Examine each product's documented facts and model caution in the comparison below. No inferred rankings or prices.":
    "Add another real research product to the comparison area. Randbeck will show documented model facts and limitations rather than making up a winner."};
 }
 if(/photo|view|side|angle|picture|zoom/.test(q))return {...base,heading:"Photo coverage for "+title,text:"The six angle controls show only documented exact-product directions. An original reference photo may be available without a verified camera direction. Missing views are unavailable—not synthesized from other firearms."};
 if(/what|tell|explain|feature|spec|about|why/.test(q))return {...base,heading:title+" — documented facts",
  text:product.facts.join(". ")+". "+product.note+" This is manufacturer research, not a verified individual catalog offer."};
 return {...base,heading:"Research preview, not live Thinking Room",
  text:"I can currently explain documented product facts, fitment evidence, related references, comparison limits and all-in pricing requirements. Open-ended Randbeck Thinking Room conversations require a secure public-only AI integration, which is not connected in this preview."};
}
