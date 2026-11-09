"use strict";
/* Integrated customer experience on the existing six-view product counter.
   This is static manufacturer research, not a conversational LLM or live
   sourcing. No telemetry, personal account, persistent preferences or checkout. */
import {REFERENCE_PRODUCTS,researchTitle} from "./product-room-research.mjs";
import {getViewsForProduct} from "./six-view-contract.mjs";
import {researchPhotoFor} from "./research-photo-license.mjs";
import {FIREARMS,ACCESSORIES,PUBLIC_COVERAGE,findResearchProducts,nextDiscovery,
 relatedReferences,variantDisclosure,makeComparison,interpretResearchQuestion,
 allInQuoteStatus,accessoryIntelligence} from "./customer-experience.mjs";
const $=id=>document.getElementById(id);
const el=(tag,cls,text)=>{const x=document.createElement(tag);if(cls)x.className=cls;if(text!==undefined)x.textContent=text;return x;};
const state={product:FIREARMS.find(x=>x.id==="ruger-precision-308-gen1")||FIREARMS[0],
 accessories:[],compare:[],saved:[],cursor:0,search:"",department:"all"};
function goToCounter(productId,{scroll=true}={}){
 const product=FIREARMS.find(x=>x.id===productId);if(!product)return;
 if(state.product?.id===productId){if(scroll)$("product-counter").scrollIntoView({behavior:"smooth",block:"start"});return;}
 const departmentButton=[...document.querySelectorAll("[data-department]")].find(x=>x.dataset.department===product.department);
 if(!departmentButton)return;
 departmentButton.click();
 const brand=$("product-brand");
 brand.value=product.brand;brand.dispatchEvent(new Event("change",{bubbles:true}));
 const model=$("product-model");
 model.value=productId;model.dispatchEvent(new Event("change",{bubbles:true}));
 // Product update arrives through area33:counter-update.
 if(scroll)$("product-counter").scrollIntoView({behavior:"smooth",block:"start"});
}
function inspectButton(product,label="Bring to counter"){
 const button=el("button","inspect-action",label);
 button.type="button";button.addEventListener("click",()=>goToCounter(product.id));
 return button;
}
function renderDiscover(){
 const results=findResearchProducts(state.search,state.department),wrap=$("discovery-results");
 wrap.replaceChildren();
 $("discovery-result-count").textContent=results.length+" documented research models";
 $("discovery-coverage").textContent=PUBLIC_COVERAGE+" Not a full count of all distributor offerings.";
 if(!results.length){wrap.append(el("p","discovery-none","No matches in this small research set. Try a broader term or browse the approved catalog."));return;}
 for(const item of results){
  const article=el("article","research-tile");if(item.id===state.product.id)article.classList.add("current");
  const photo=researchPhotoFor(item);
  const media=el("div","research-tile-media");
  if(photo){
   const img=el("img");img.alt=photo.caption;img.src=photo.src;img.loading="lazy";img.referrerPolicy="no-referrer";
   img.addEventListener("error",()=>{img.hidden=true;media.append(el("span","missing-thumb","Image unavailable"));});
   media.append(img);
  }else media.append(el("span","missing-thumb","Exact photo not cleared"));
  const title=el("strong","",researchTitle(item)),subtitle=el("p","",item.subtitle);
  const origin=el("small","",item.department.toUpperCase()+" · RESEARCH REFERENCE");
  const copy=el("div","tile-copy");copy.append(origin,title,subtitle,inspectButton(item,item.id===state.product.id?"At your counter":"Explore this model"));
  article.append(media,copy);wrap.append(article);
 }
}
function renderVariants(){
 const disclosure=variantDisclosure(state.product),list=$("variant-results");
 list.replaceChildren();
 $("variant-coverage").textContent=disclosure.description;
 if(!disclosure.related.length){list.append(el("p","variant-none","No reviewed related models to display for this product. All actual finishes and sellable variants need a verified catalog identity."));return;}
 for(const item of disclosure.related){
  const card=el("div","variant-item");
  const texts=el("div");texts.append(el("strong","",researchTitle(item)),el("small","",item.subtitle||"Different research reference"));
  card.append(texts,inspectButton(item,"Inspect model"));list.append(card);
 }
}
function renderCompare(){
 const box=$("compare-cards");box.replaceChildren();
 const entries=makeComparison(state.compare);
 $("compare-current").disabled=state.compare.some(x=>x.id===state.product.id)||state.compare.length>=3;
 $("compare-current").textContent=state.compare.some(x=>x.id===state.product.id)?"Already comparing":state.compare.length>=3?"Three-item comparison full":"+ Compare current product";
 if(!entries.length){box.append(el("p","compare-empty","Add a research product from the counter. You can compare up to three models without losing your selection."));return;}
 for(const item of entries){
  const card=el("article","comparison-tile");
  const upper=el("div","compare-tile-head");
  upper.append(el("span","eyebrow",item.type.toUpperCase()),el("strong","",item.title));
  const facts=el("ul");
  for(const f of item.facts)facts.append(el("li","",f));
  const note=el("p","comparison-caution",item.variantCaution);
  const line=el("p","comparison-unknown","Availability: "+item.availability+" · Price: "+item.pricing);
  const bottom=el("div","comparison-buttons");
  const open=inspectButton(FIREARMS.find(x=>x.id===item.id),"Inspect");
  const remove=el("button","remove-action","Remove");remove.type="button";
  remove.addEventListener("click",()=>{state.compare=state.compare.filter(x=>x.id!==item.id);renderCompare();});
  bottom.append(open,remove);card.append(upper,el("p","comparison-description",item.description),facts,note,line,bottom);
  box.append(card);
 }
}
function renderSaved(){
 const wrap=$("saved-discoveries");wrap.replaceChildren();
 $("save-current").textContent=state.saved.some(x=>x.id===state.product.id)?"★ Saved for this visit":"☆ Save this discovery";
 if(!state.saved.length){wrap.append(el("p","saved-empty","No products saved this visit. Save something interesting, then keep exploring."));return;}
 for(const item of state.saved){
  const row=el("div","saved-item");
  row.append(el("strong","",researchTitle(item)),inspectButton(item,"Inspect"));
  const remove=el("button","remove-action","×");
  remove.type="button";remove.setAttribute("aria-label","Remove "+researchTitle(item)+" from saved discoveries");
  remove.addEventListener("click",()=>{state.saved=state.saved.filter(x=>x.id!==item.id);renderSaved();});
  row.append(remove);wrap.append(row);
 }
}
const PROMPTS=[
 "What makes this model interesting?",
 "Show every related model and finish we actually know.",
 "Which selected accessories have documented fit?",
 "What does the Area 33 delivered price include?",
 "Can you compare this with another model?"
];
function renderThinkingContext(){
 $("thinking-product-context").textContent=researchTitle(state.product);
}
function renderThinkingSuggestions(){
 const wrap=$("thinking-suggestions");wrap.replaceChildren();
 for(const text of PROMPTS){
  const btn=el("button","question-pill",text);btn.type="button";
  btn.addEventListener("click",()=>ask(text));
  wrap.append(btn);
 }
}
function addMessage(kind,heading,text,sources=[]){
 const log=$("thinking-conversation");
 const message=el("div","thinking-message "+(kind==="user"?"from-visitor":"from-randbeck"));
 if(heading)message.append(el("strong","",heading));
 message.append(el("p","",text));
 if(sources.length){
  const links=el("div","thinking-sources");
  for(const source of sources){
   if(!source.url?.startsWith("https://"))continue;
   const a=el("a","",source.label+" ↗");a.href=source.url;a.target="_blank";a.rel="noopener noreferrer";links.append(a);
  }message.append(links);
 }
 log.append(message);while(log.children.length>11)log.firstChild.remove();
 log.scrollTop=log.scrollHeight;
}
function ask(text){
 const query=String(text||"").trim();if(!query)return;
 addMessage("user",null,query);
 const answer=interpretResearchQuestion(state.product,query,
  {selectedAccessories:state.accessories,comparison:state.compare});
 addMessage("assistant",answer.heading,answer.text,answer.sources);
 $("thinking-query").value="";
}
function resetThinking(){
 $("thinking-conversation").replaceChildren();
 addMessage("assistant","Hi, I’m EVA — your Area 33 firearms expert (research preview)",
  "You're exploring "+researchTitle(state.product)+". Ask me about documented facts, related models and compatibility evidence. This is an offline preview, not yet live EVA powered by Randbeck.");
 renderThinkingContext();
}
function renderAllIn(){
 const info=allInQuoteStatus({zip:$("delivery-zip").value,
  selectedProducts:[{id:state.product?.id,publicSkuVerified:false,stockVerified:false}],sourceQuote:null});
 $("all-in-label").textContent=info.label;
 $("all-in-caption").textContent=info.notice;
 $("quote-readiness-title").textContent=info.confirmed?"Verified Area 33 delivery quote":"Still needed before the Area 33 delivered price can be confirmed";
 const blockers=$("quote-blockers");blockers.replaceChildren();
 for(const issue of info.blockers)blockers.append(el("li","",issue));
}
function syncFromCounter(event){
 const id=event?.detail?.productId||$("product-model").value;
 const product=FIREARMS.find(x=>x.id===id);if(!product)return;
 const changed=state.product?.id!==product.id;
 state.product=product;
 const selected=event?.detail?.selectedAccessories;
 state.accessories=Array.isArray(selected)?
   selected.filter(id=>ACCESSORIES.some(a=>a.id===id)):
   [...document.querySelectorAll(".accessory-button[aria-pressed='true']")].map(b=>b.dataset.accessory).filter(Boolean);
 if(changed){renderVariants();renderCompare();renderSaved();resetThinking();}
 else renderThinkingContext();
 renderDiscover();renderAllIn();
}
function bind(){
 $("discovery-search").addEventListener("input",e=>{state.search=e.target.value;renderDiscover();});
 $("discovery-department").addEventListener("change",e=>{state.department=e.target.value;renderDiscover();});
 $("clear-discovery").addEventListener("click",()=>{
  state.search="";state.department="all";
  $("discovery-search").value="";$("discovery-department").value="all";renderDiscover();
 });
 $("surprise-discovery").addEventListener("click",()=>{
  state.cursor++;
  const item=nextDiscovery(FIREARMS,state.product.id,state.cursor);
  if(item)goToCounter(item.id);
 });
 $("compare-current").addEventListener("click",()=>{
  if(state.compare.length>=3||state.compare.some(x=>x.id===state.product.id))return;
  state.compare=[...state.compare,state.product];renderCompare();
 });
 $("clear-compare").addEventListener("click",()=>{state.compare=[];renderCompare();});
 $("save-current").addEventListener("click",()=>{
  if(state.saved.some(x=>x.id===state.product.id))state.saved=state.saved.filter(x=>x.id!==state.product.id);
  else state.saved=[...state.saved,state.product];renderSaved();
 });
 $("thinking-form").addEventListener("submit",e=>{e.preventDefault();ask($("thinking-query").value);});
 $("all-in-form").addEventListener("submit",e=>{e.preventDefault();renderAllIn();});
 $("delivery-zip").addEventListener("input",renderAllIn);
 window.addEventListener("area33:counter-update",syncFromCounter);
 window.addEventListener("area33:featured-open",e=>goToCounter(e.detail?.productId));
}
function init(){
 bind();
 const url=new URL(location.href);
 const first=FIREARMS.find(x=>x.id===url.searchParams.get("product"))||FIREARMS.find(x=>x.id===$("product-model").value);
 if(first)state.product=first;
 state.accessories=url.searchParams.getAll("accessory").filter(id=>ACCESSORIES.some(x=>x.id===id));
 renderDiscover();renderVariants();renderCompare();renderSaved();renderThinkingSuggestions();resetThinking();renderAllIn();
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});
else init();
