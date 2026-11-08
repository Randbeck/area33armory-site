"use strict";
import {REFERENCE_PRODUCTS,REFERENCE_CHECKED,DEPARTMENTS,ACCESSORY_CATEGORIES,researchTitle,chooseDiscovery} from "./product-room-research.mjs";
import {sanitizeCatalogManifest} from "./catalog-static-contract.mjs";
import {createApprovedGallery,galleryAllowed} from "./catalog-gallery.mjs";
import {createResearchPhotoViewer} from "./research-photo-viewer.mjs";
import {PAIRING_REVIEWED,evaluatePairing,manufacturerListedSuggestions} from "./pairing-evidence.mjs";
import {createExperienceBench} from "./experience-bench.mjs";

const $=id=>document.getElementById(id);
const research=REFERENCE_PRODUCTS;
const cleanText=v=>typeof v==="string"?v.trim().slice(0,200):"";
const title=item=>researchTitle(item);
let approved=[];
let dept="pistols",accessoryCategory="optics";
let current=null,accessory=null,compare=[],discoverSeed=1;
const researchPhotoViewer=createResearchPhotoViewer();
const experienceBench=createExperienceBench({
 getKnownItems:()=>[...research,...approved],
 onChooseAccessory:item=>selectAccessoryCategory(item.accessoryType,item.brand,item.id),
 onClearAccessory:()=>selectAccessoryCategory(accessoryCategory,$("accessory-brand").value)
});
function element(tag,className,copy){
 const n=document.createElement(tag);
 if(className)n.className=className;
 if(copy!==undefined)n.textContent=copy;
 return n;
}
function categoryFromApproved(item){
 const label=(item.category||"").toLowerCase();
 if(item.type==="complete"){
  if(/\b(handguns?|pistols?)\b/.test(label))return {kind:"firearm",department:"pistols"};
  if(/\bshotguns?\b/.test(label))return {kind:"firearm",department:"shotguns"};
  if(/\brifles?\b/.test(label))return {kind:"firearm",department:"rifles"};
  return null; // "Long Guns" cannot safely be assumed to mean rifle.
 }
 if(item.type!=="accessory")return null;
 if(/\b(optics?|sights?|scopes?)\b/.test(label))return {kind:"accessory",accessoryType:"optics"};
 if(/\b(lights?|flashlights?)\b/.test(label))return {kind:"accessory",accessoryType:"lights"};
 if(/\b(holsters?)\b/.test(label))return {kind:"accessory",accessoryType:"holsters"};
 if(/\b(cases?|bags?)\b/.test(label))return {kind:"accessory",accessoryType:"cases"};
 return null;
}
function addApproved(item){
 const type=categoryFromApproved(item);
 if(!type)return null;
 return {id:item.id,brand:item.manufacturer,model:[item.model,item.variant].filter(Boolean).join(" · "),
  subtitle:item.category+" · Approved Area 33 public record",facts:[item.description||"Approved product research record"],
  note:"Published product record only. Does not establish stock, price, accessory pairing or physical compatibility.",
  source:null,approvedItem:item,kind:type.kind,department:type.department,accessoryType:type.accessoryType};
}
function listItems(kind,filter){
 return [...research,...approved].filter(item=>item.kind===kind&&
  (kind==="firearm"?item.department===filter:item.accessoryType===filter));
}
function uniqueBrands(items){return [...new Set(items.map(x=>x.brand))].sort((a,b)=>a.localeCompare(b));}
function option(value,label){return new Option(label,value);}
function fillSelect(node,values,selected){
 node.replaceChildren(...values.map(v=>option(v,v)));
 node.disabled=!values.length;
 if(values.length)node.value=values.includes(selected)?selected:values[0];
}
function selectCurrent(id){
 const all=listItems("firearm",dept);
 const picked=all.find(item=>item.id===id)||all[0]||null;
 current=picked;
 if(picked){
  $("brand").value=picked.brand;
  $("model").value=picked.id;
 }
 render();
}
function fillModelOptions(prefer){
 const models=listItems("firearm",dept).filter(x=>x.brand===$("brand").value);
 $("model").replaceChildren(...models.map(x=>option(x.id,x.model+(x.approvedItem?" · APPROVED":" · RESEARCH"))));
 $("model").disabled=!models.length;
 const chosen=models.find(x=>x.id===prefer)||models[0]||null;
 if(chosen) $("model").value=chosen.id;
 current=chosen;
 render();
}
function fillBrandOptions(prefer,modelId){
 const brands=uniqueBrands(listItems("firearm",dept));
 fillSelect($("brand"),brands,prefer);
 fillModelOptions(modelId);
}
function selectDepartment(next,brand,modelId){
 if(!DEPARTMENTS.includes(next))return;
 dept=next;
 document.querySelectorAll("[data-department]").forEach(btn=>btn.setAttribute("aria-pressed",String(btn.dataset.department===dept)));
 fillBrandOptions(brand,modelId);
}
function fillAccessoryBrand(prefer,accessoryId){
 const brands=uniqueBrands(listItems("accessory",accessoryCategory));
 fillSelect($("accessory-brand"),brands,prefer);
 drawAccessoryChoices(accessoryId);
}
function selectAccessoryCategory(next,brand,id){
 if(!ACCESSORY_CATEGORIES.includes(next))return;
 accessoryCategory=next;
 document.querySelectorAll("[data-accessory-category]").forEach(btn=>btn.setAttribute("aria-pressed",String(btn.dataset.accessoryCategory===next)));
 fillAccessoryBrand(brand,id);
}
function drawAccessoryChoices(preferId){
 const list=listItems("accessory",accessoryCategory).filter(x=>x.brand===$("accessory-brand").value);
 const shelf=$("accessory-items");
 shelf.replaceChildren();
 if(!list.length){
  accessory=null;
  shelf.append(element("p","room-small-status","No manufacturer reference in this category yet. Approved Area 33 products can appear here when their category is verified."));
  render();
  return;
 }
 accessory=list.find(x=>x.id===preferId)||null;
 for(const product of list){
  const btn=element("button","room-accessory-item");
  btn.type="button";
  btn.dataset.accessoryId=product.id;
  btn.setAttribute("aria-pressed",String(product.id===accessory?.id));
  const name=element("span");name.append(element("strong","",title(product)),element("small","",product.subtitle));
  btn.append(name,element("span","","›"));
  btn.addEventListener("click",()=>{accessory=product;drawAccessoryChoices(product.id);});
  shelf.append(btn);
 }
 render();
}
function presentApprovedMedia(item){
 const slot=$("approved-gallery-slot"),missing=$("media-unavailable");
 slot.replaceChildren();
 const approvedItem=item?.approvedItem;
 const gallery=approvedItem&&galleryAllowed(approvedItem)?createApprovedGallery(approvedItem):null;
 if(gallery){
  researchPhotoViewer.hide();
  slot.append(gallery);
  slot.hidden=false;missing.hidden=true;
  $("stage-approval").textContent="OWNER-APPROVED PRODUCT PHOTOS";
  $("media-tag").textContent="EXACT-PRODUCT APPROVED IMAGERY";
 }else if(researchPhotoViewer.show(item)){
  slot.hidden=true;missing.hidden=true;
  $("stage-approval").textContent="CREATIVE COMMONS / RESEARCH PHOTO";
  $("media-tag").textContent="ONE REAL PHOTOGRAPH · NOT AN AREA 33 LISTING";
 }else{
  slot.hidden=true;missing.hidden=false;
  $("stage-approval").textContent=approvedItem?"APPROVED TEXT PROFILE / NO PHOTOS":"PHOTO APPROVAL PENDING";
  $("media-tag").textContent="REAL PRODUCT IDENTITY · MEDIA PENDING";
  missing.querySelector("strong").textContent=approvedItem?"This product is text-only.":"Real product. Official product photos.";
  missing.querySelector("p").textContent=approvedItem?
   "This Area 33 public product record does not have an approved photo set. We won't replace it with an unrelated image.":
   "Area 33 hasn't approved an image set for this exact model yet. Open the manufacturer's page to see real photos and documentation.";
 }
}

function render(){
 if(!current){$("product-name").textContent="No research models available";return;}
 const item=current;
 $("stage-breadcrumb").textContent=dept.toUpperCase()+" / "+item.brand.toUpperCase();
 $("product-name").textContent=title(item);
 $("product-subtitle").textContent=item.subtitle;
 $("source-type").textContent=item.approvedItem?"AREA 33 APPROVED PUBLIC PRODUCT RECORD":"MANUFACTURER RESEARCH REFERENCE";
 $("identity-status").textContent=item.approvedItem?"Area 33 published record":"Maker reference only";
 $("intel-title").textContent="Exploring "+item.model;
 $("intel-answer").textContent=item.note;
 $("fit-status").textContent="Not verified";
 const facts=$("product-facts");facts.replaceChildren(...item.facts.map(f=>element("span","room-fact",cleanText(f))));
 const link=$("official-link"),photoLink=$("manufacturer-photos");
 const hasManufacturerUrl=!!item.source;
 link.hidden=!hasManufacturerUrl;photoLink.hidden=!hasManufacturerUrl;
 if(hasManufacturerUrl){link.href=item.source;photoLink.href=item.source;}
 $("reference-note").textContent=item.approvedItem?"Approved public record; not current stock.":"Official model research checked "+REFERENCE_CHECKED+".";
 presentApprovedMedia(item);
 renderPairing();
 experienceBench.render(current,accessory);
 const hasCompare=compare.some(x=>x.id===item.id);
 $("compare-add").disabled=hasCompare||compare.length>=3;
 $("compare-add").textContent=hasCompare?"Already on comparison shelf":"Save firearm to compare";
}
function presentPairingEvidence(record){
 const panel=$("pairing-evidence"),sources=$("pairing-sources");
 sources.replaceChildren();
 if(!record){
  panel.hidden=true;
  $("fit-status").textContent="Not assessed";
  return;
 }
 panel.hidden=false;
 $("pairing-status").textContent=record.short;
 $("pairing-status").dataset.status=record.status;
 $("pairing-reviewed").textContent="Maker sources checked "+PAIRING_REVIEWED;
 $("pairing-summary").textContent=record.summary;
 $("pairing-why").textContent=record.why;
 $("fit-status").textContent=record.status==="manufacturer-listed"?
  "Manufacturer-listed (not independently tested)":
  record.status==="factory-interface-differs"?"Not a factory direct match":
  record.status==="family-guidance"?"Family guidance only":"Exact fit not assessed";
 if(record.evidence.length===0){
  sources.append(element("li","","No exact manufacturer fit evidence recorded for this combination."));
 }else for(const citation of record.evidence){
  const li=element("li"),link=element("a","",citation.label+" ↗");
  link.href=citation.url;link.target="_blank";link.rel="noopener noreferrer";
  li.append(link,element("small","",citation.checkedAt));
  sources.append(li);
 }
}
function updateSuggestion(){
 const area=$("smart-suggestion-area");
 const listed=manufacturerListedSuggestions(current,listItems("accessory","optics"));
 const candidate=listed.find(x=>x.id!==accessory?.id);
 area.hidden=!candidate;
 if(candidate){
  $("smart-suggestion-caption").textContent=title(candidate)+". A manufacturer names this firearm model in its fitment list. No image overlay or physical fit test has been performed.";
  $("smart-suggestion").dataset.accessoryId=candidate.id;
 }else delete $("smart-suggestion").dataset.accessoryId;
}
function renderPairing(){
 if(!current)return;
 updateSuggestion();
 if(!accessory){
  $("pairing-title").textContent="Select an accessory to explore.";
  $("pairing-copy").textContent="Products are kept separate until you explicitly select an exact accessory. The system will then look for available manufacturer fitment evidence.";
  $("pairing-warning").textContent="No accessory has been selected, and no fitment or visual pairing is implied.";
  $("accessory-official-link").hidden=true;
  presentPairingEvidence(null);
  return;
 }
 $("pairing-title").textContent=title(current)+" + "+title(accessory);
 $("pairing-copy").textContent=accessory.subtitle+". "+accessory.facts.join(". ")+".";
 const result=evaluatePairing(current,accessory);
 presentPairingEvidence(result);
 $("pairing-warning").textContent=result.caution;
 const a=$("accessory-official-link");a.hidden=!accessory.source;
 if(accessory.source)a.href=accessory.source;
}

function renderCompare(){
 const list=$("compare-list");list.replaceChildren();
 if(!compare.length){list.append(element("p","room-small-status","Your comparison shelf is empty. Choose a real model above to start."));return;}
 for(const item of compare){
  const wrap=element("span");wrap.append(document.createTextNode(title(item)));
  const remove=element("button","","×");remove.type="button";remove.setAttribute("aria-label","Remove "+title(item)+" from comparison");
  remove.addEventListener("click",()=>{compare=compare.filter(x=>x.id!==item.id);renderCompare();render();});
  wrap.append(remove);list.append(wrap);
 }
}
function answerQuestion(q){
 if(!current)return;
 const prefix=title(current)+": ";
 const answers={
 differences:prefix+current.facts.join("; ")+". These are manufacturer research highlights, not a complete comparison of every variant. Use the official documentation for exact specs.",
 fit:accessory?((p)=>p.short+". "+p.summary+" "+p.caution)(evaluatePairing(current,accessory)):
 "Choose an exact accessory first. Even then, the showroom will not label it compatible without specific, reviewed pairing evidence.",
 value:"No current Area 33 customer quote is connected. Verified pricing will use exact distributor offers, recorded availability freshness, freight, fees, promotions and margin. No lowest-price promise is made."
 };
 $("intel-answer").textContent=answers[q]||current.note;
}
function copySelection(){
 const selected=title(current)+(accessory?" + research accessory: "+title(accessory):"");
 const proof=evaluatePairing(current,accessory);
 return "Area 33 product research: "+selected+". "+
   (proof?("Evidence status: "+proof.short+". "+proof.summary+" "):"")+
   "No independent physical inspection, verified stock, customer price or offer. "+(current.source||"")+" "+(accessory?.source||"");
}
async function copyText(text){
 if(!navigator.clipboard?.writeText)throw Error("Clipboard unavailable");
 await navigator.clipboard.writeText(text);
}
async function loadApproved(){
 try{
  const response=await fetch("assets/catalog-public.json",{credentials:"omit",cache:"no-store"});
  if(!response.ok)throw Error("No public manifest");
  const manifest=sanitizeCatalogManifest(await response.json(),{baseUrl:location.href});
  if(!manifest)throw Error("Invalid public manifest");
  approved=manifest.items.map(addApproved).filter(Boolean);
 }catch{approved=[];}
 const savedId=current?.id,savedAccessory=accessory?.id;
 selectDepartment(dept,current?.brand,savedId);
 selectAccessoryCategory(accessoryCategory,accessory?.brand,savedAccessory);
 $("research-coverage").textContent=
  research.filter(x=>x.kind==="firearm").length+" manufacturer-identified firearm references · "+
  research.filter(x=>x.kind==="accessory").length+" accessory references · "+
  approved.length+" published category-matched Area 33 records";
}
function init(){
 const qs=new URLSearchParams(location.search);
 const selectedResearch=research.find(x=>x.id===qs.get("product")&&x.kind==="firearm");
 selectDepartment(selectedResearch?.department||"pistols",selectedResearch?.brand,selectedResearch?.id);
 const selectedAccessory=research.find(x=>x.id===qs.get("accessory")&&x.kind==="accessory");
 selectAccessoryCategory(selectedAccessory?.accessoryType||"optics",selectedAccessory?.brand,selectedAccessory?.id);
 renderCompare();
 document.querySelectorAll("[data-department]").forEach(b=>b.addEventListener("click",()=>selectDepartment(b.dataset.department)));
 $("brand").addEventListener("change",()=>fillModelOptions());
 $("model").addEventListener("change",()=>selectCurrent($("model").value));
 document.querySelectorAll("[data-accessory-category]").forEach(b=>b.addEventListener("click",()=>selectAccessoryCategory(b.dataset.accessoryCategory)));
 $("accessory-brand").addEventListener("change",()=>drawAccessoryChoices());
 $("surprise").addEventListener("click",()=>{
  const item=chooseDiscovery(listItems("firearm","pistols").concat(listItems("firearm","rifles"),listItems("firearm","shotguns")),current?.id,discoverSeed++);
  if(!item)return;
  selectDepartment(item.department,item.brand,item.id);
  $("intel-answer").textContent="Here's a different real product to explore: "+title(item)+". "+item.note;
 });
 document.querySelectorAll("[data-question]").forEach(b=>b.addEventListener("click",()=>answerQuestion(b.dataset.question)));
 $("compare-add").addEventListener("click",()=>{
  if(!current||compare.some(x=>x.id===current.id)||compare.length>=3)return;
  compare.push(current);renderCompare();render();
 });
 $("smart-suggestion").addEventListener("click",()=>{
  const id=$("smart-suggestion").dataset.accessoryId;
  const suggested=listItems("accessory","optics").find(x=>x.id===id);
  if(!suggested)return;
  selectAccessoryCategory("optics",suggested.brand,suggested.id);
  $("intel-answer").textContent="One manufacturer-listed possibility to understand: "+title(suggested)+". See the exact fitment evidence below, including the limits of the claim.";
 });
 $("share-selection").addEventListener("click",async()=>{
  try{await copyText(copySelection());$("sharing-status").textContent="Research summary copied. No fit or price has been claimed.";}
  catch{$("sharing-status").textContent="Clipboard access is unavailable. The product and manufacturer source links remain visible above.";}
 });
 loadApproved();
}
init();
