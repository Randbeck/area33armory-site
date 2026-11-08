"use strict";
/* A customer-first right-hand browsing counter on the real Area 33 homepage.
 * Only curated public research identities and licensed reference photographs.
 * Future public catalog/EVA adapters must be server-side, reviewed and scoped.
 * Nothing collected, posted or retained after this page reloads. */
import {researchTitle} from "./product-room-research.mjs";
import {researchPhotoFor} from "./research-photo-license.mjs";
import {FIREARMS,ACCESSORIES,findResearchProducts,variantDisclosure,
  interpretResearchQuestion,accessoryIntelligence,allInQuoteStatus} from "./customer-experience.mjs";
import {reviewAccessoryContext} from "./accessory-context.mjs";

const $=id=>document.getElementById(id);
const make=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;};
const state={product:null,tab:"inspect",saved:new Set(),compare:new Set(),
 search:"",department:"all",showAllAccessories:false,previousFocus:null};
const panel=$("area33-side-counter");
const back=$("area33-side-backdrop");
const reopen=$("area33-reopen-counter");
if(!panel||!back||!reopen)throw new Error("Side counter markup missing");
const safeLink=(label,href)=>{
  const a=make("a","counter-source-link",label);
  if(typeof href==="string"&&href.startsWith("https://")){a.href=href;a.rel="noopener noreferrer";a.target="_blank";}
  else {a.textContent=label+" (source unavailable)";a.removeAttribute("href");}
  return a;
};
function current(){return FIREARMS.find(x=>x.id===state.product)||null;}
function showProductPhoto(parent,product,{hero=false}={}){
 const photo=researchPhotoFor(product);
 const media=make("div",hero?"side-product-photo":"browse-product-photo");
 if(photo){
  const img=make("img");img.src=photo.src;img.alt=photo.caption;img.loading=hero?"eager":"lazy";
  img.referrerPolicy="no-referrer";img.decoding="async";
  img.addEventListener("error",()=>{img.hidden=true;media.append(make("span","missing-photo","Approved photo unavailable"));});
  media.append(img);
  if(hero){
   const credit=make("p","side-photo-credit","Photo: "+photo.author+" · "+photo.license+" · Actual documented reference, not necessarily a current offer");
   media.append(credit);
  }
 }else media.append(make("span","missing-photo",hero?"No licensed exact-product photograph available for this research reference":"Image not publication-cleared"));
 parent.append(media);
}
function openCounter(id,tab="inspect"){
 const product=FIREARMS.find(p=>p.id===id);
 if(!product)return;
 const wasOpen=!panel.hidden;
 if(!wasOpen)state.previousFocus=document.activeElement;
 state.product=id;state.tab=tab;
 panel.hidden=false;back.hidden=false;reopen.hidden=true;
 document.body.classList.add("area33-side-open");
 panel.setAttribute("aria-hidden","false");
 renderPanel();
 if(window.matchMedia("(max-width: 900px)").matches)document.body.classList.add("area33-side-mobile");
 requestAnimationFrame(()=>{$("side-counter-close")?.focus({preventScroll:true});});
}
function closeCounter(){
 panel.hidden=true;back.hidden=true;document.body.classList.remove("area33-side-open","area33-side-mobile");
 panel.setAttribute("aria-hidden","true");
 if(state.product)reopen.hidden=false;
 const returnTo=state.previousFocus;
 if(returnTo instanceof HTMLElement&&returnTo.isConnected)returnTo.focus({preventScroll:true});
 else reopen.focus({preventScroll:true});
}
function chooseTab(tab){
 if(!["inspect","models","accessories","eva"].includes(tab))return;
 state.tab=tab;renderPanel();
}
const eBtn=(text,click,cls="side-action")=>{
 const b=make("button",cls,text);b.type="button";b.addEventListener("click",click);return b;
};
function renderPanel(){
 const p=current();if(!p)return;
 $("side-counter-product-name").textContent=researchTitle(p);
 $("side-counter-product-meta").textContent=(p.department||"").toUpperCase()+" · PUBLIC MANUFACTURER RESEARCH · NOT A VERIFIED OFFER";
 const body=$("side-counter-body");body.replaceChildren();
 for(const tab of ["inspect","models","accessories","eva"]){
  const button=$("side-tab-"+tab);
  button.setAttribute("aria-selected",String(tab===state.tab));
  button.tabIndex=tab===state.tab?0:-1;
 }
 if(state.tab==="inspect")renderInspect(body,p);
 if(state.tab==="models")renderModels(body,p);
 if(state.tab==="accessories")renderAccessories(body,p);
 if(state.tab==="eva")renderEva(body,p);
 const link=$("side-full-counter");
 link.href="six-view-counter.html?product="+encodeURIComponent(p.id)+"#product-counter";
 $("side-save").textContent=state.saved.has(p.id)?"★ Saved":"☆ Save";
 $("side-compare").textContent=state.compare.has(p.id)?"✓ Added to compare":state.compare.size>=3?"Comparison full":"+ Compare";
 $("side-compare").disabled=!state.compare.has(p.id)&&state.compare.size>=3;
 const selections=$("side-saved-status");
 selections.textContent=state.saved.size+" saved this visit · "+state.compare.size+"/3 for comparison";
 renderCompareStrip();
}
function renderInspect(parent,p){
 showProductPhoto(parent,p,{hero:true});
 const stack=make("div","side-stack");
 stack.append(make("h3","",researchTitle(p)));
 stack.append(make("p","side-subtitle",p.subtitle||"Research model"));
 const list=make("ul","side-facts");
 for(const f of p.facts||[])list.append(make("li","",f));
 stack.append(list);
 stack.append(make("p","side-evidence-note",p.note));
 stack.append(safeLink("Manufacturer reference ↗",p.source));
 const price=make("div","side-price");
 price.append(make("small","","AREA 33 DELIVERED PRICE"),make("strong","","Price pending"),make("p","","When verified, includes merchandise, applicable tax, shipping and all Area 33 charges. Receiving FFL transfer fee is charged separately by the chosen dealer and is not included."));
 stack.append(price);
 stack.append(eBtn("Ask EVA about this model →",()=>chooseTab("eva"),"side-primary"));
 parent.append(stack);
}
function renderModels(parent,p){
 const v=variantDisclosure(p);
 parent.append(make("h3","","Known models and variants"));
 parent.append(make("p","side-muted",v.description));
 if(!v.related.length)parent.append(make("p","side-no-results","No additional reviewed versions in this limited public research set; colors and all factory configurations are not yet indexed."));
 for(const other of v.related){
  const row=make("article","side-related");
  const d=make("div");d.append(make("strong","",researchTitle(other)),make("p","",other.subtitle||"Related reference"));
  row.append(d,eBtn("View",()=>openCounter(other.id,"models")));
  parent.append(row);
 }
 parent.append(make("p","side-evidence-note","Only exact manufacturer-catalog variants with approved source IDs will appear as selectable finishes once the public distributor feed is connected."));
}
function renderAccessories(parent,p){
 parent.append(make("h3","","Explore relevant accessories"));
 parent.append(make("p","side-muted","Explore product categories and documented manufacturer evidence. These suggestions are not confirmation that two items physically fit together or have been installed in a photo."));
 const accessoryList=ACCESSORIES.filter(x=>state.showAllAccessories||reviewAccessoryContext(p,x).tier==="explore");
 const chooser=make("div","side-accessory-list");
 if(!accessoryList.length)chooser.append(make("p","side-no-results","No reviewed category-level suggestions for this model yet. You can examine the full accessory research set."));
 for(const a of accessoryList){
  const info=accessoryIntelligence(p,a);
  const row=make("article","side-related");
  const content=make("div");content.append(make("strong","",researchTitle(a)),
    make("p","",info?.pairing?.status==="manufacturer-listed"?"Manufacturer-listed pairing; confirm exact configuration":info?.relevance?.label||"Needs further review"),
    make("small","side-evidence-note",info?.relevance?.reason||""));
  row.append(content,safeLink("Evidence ↗",a.source));chooser.append(row);
 }
 parent.append(chooser);
 parent.append(eBtn(state.showAllAccessories?"Show relevant only":"Show all research accessories",()=>{
  state.showAllAccessories=!state.showAllAccessories;renderPanel();
 }));
 parent.append(make("p","side-evidence-note","Actual accessory installation visualization is a separate, clearly labeled concept feature—not an exact fit guarantee."));
}
const samplePrompts=["What makes this model different?","Show me every related model.","What accessories should I explore?","What does the Area 33 price include?"];
function renderEva(parent,p){
 parent.append(make("h3","","Ask EVA, Your Firearms Expert"));
 parent.append(make("p","side-muted","EVA knows which model is at your counter. Right now this is a source-backed research preview, not live conversational Randbeck AI."));
 const log=make("div","side-eva-log");log.id="side-eva-log";log.setAttribute("aria-live","polite");log.setAttribute("role","log");
 const welcome=make("div","side-eva-answer");
 welcome.append(make("strong","","EVA · RESEARCH PREVIEW"),make("p","","You're looking at "+researchTitle(p)+". Ask about its documented specifications, related models, accessory evidence or the Area 33 delivered-price policy."));
 log.append(welcome);parent.append(log);
 const pills=make("div","side-eva-prompts");
 const ask=(query)=>{
  if(!query.trim())return;
  const user=make("p","side-eva-user",query);
  log.append(user);
  const a=interpretResearchQuestion(p,query);
  const reply=make("div","side-eva-answer");
  reply.append(make("strong","",a.heading),make("p","",a.text));
  const links=make("div","side-source-links");
  for(const source of a.sources||[])links.append(safeLink(source.label+" ↗",source.url));
  reply.append(links);log.append(reply);
  while(log.children.length>9)log.firstChild.remove();
  log.scrollTop=log.scrollHeight;
 };
 for(const prompt of samplePrompts)pills.append(eBtn(prompt,()=>ask(prompt),"side-prompt"));
 parent.append(pills);
 const form=make("form","side-eva-form");
 const input=make("input");input.type="text";input.maxLength=500;input.placeholder="Ask about this product…";input.setAttribute("aria-label","Ask EVA a product research question");
 const send=make("button","side-primary","Ask EVA →");send.type="submit";
 form.append(input,send);
 form.addEventListener("submit",e=>{e.preventDefault();ask(input.value);input.value="";});
 parent.append(form);
}
function renderCompareStrip(){
 const strip=$("side-comparison-list");strip.replaceChildren();
 if(!state.compare.size){strip.append(make("span","","Compare up to 3 products without leaving the store."));return;}
 for(const id of state.compare){
  const p=FIREARMS.find(x=>x.id===id);
  if(!p)continue;
  const chip=eBtn(researchTitle(p)+" ×",()=>{
   state.compare.delete(id);renderPanel();
  },"side-compare-chip");chip.setAttribute("aria-label","Remove "+researchTitle(p)+" from comparison");strip.append(chip);
 }
 if(state.compare.size>1)strip.append(safeLink("Open full comparison ↗","https://area33armory.com/six-view-counter.html#compare-area"));
}
function renderShop(){
 const gallery=$("home-firearms-gallery"),count=$("home-firearms-count");
 if(!gallery)return;
 const products=findResearchProducts(state.search,state.department);
 gallery.replaceChildren();
 count.textContent=products.length+" researched firearms · not the complete distributor catalog";
 if(!products.length){
  gallery.append(make("p","home-no-results","No matches in this research sample. Try a different model or explore the full catalog preview."));
  return;
 }
 for(const p of products){
  const card=make("article","home-firearm-card");
  showProductPhoto(card,p);
  const body=make("div","home-firearm-copy");
  body.append(make("span","home-product-category",p.department.toUpperCase()+" · "+p.brand),
    make("h3","",p.model),make("p","",p.subtitle||"Research model"),
    make("span","home-card-price","Area 33 price pending · receiving FFL fee separate"));
  const btn=eBtn("View at the side counter",()=>openCounter(p.id),"home-counter-button");
  body.append(btn);card.append(body);gallery.append(card);
 }
}
$("side-counter-close").addEventListener("click",closeCounter);
back.addEventListener("click",closeCounter);
reopen.addEventListener("click",()=>state.product&&openCounter(state.product,state.tab));
$("side-save").addEventListener("click",()=>{const p=current();if(!p)return;
 if(state.saved.has(p.id))state.saved.delete(p.id);else state.saved.add(p.id);renderPanel();
});
$("side-compare").addEventListener("click",()=>{const p=current();if(!p)return;
 if(state.compare.has(p.id))state.compare.delete(p.id);else if(state.compare.size<3)state.compare.add(p.id);renderPanel();
});
for(const tab of ["inspect","models","accessories","eva"])$("side-tab-"+tab).addEventListener("click",()=>chooseTab(tab));
$("home-firearms-query")?.addEventListener("input",e=>{state.search=e.target.value;renderShop();});
$("home-firearms-category")?.addEventListener("change",e=>{state.department=e.target.value;renderShop();});
document.addEventListener("keydown",e=>{
 if(e.key==="Escape"&&!panel.hidden)closeCounter();
 if(e.key==="Tab"&&!panel.hidden&&window.matchMedia("(max-width: 900px)").matches){
  const focusable=[...panel.querySelectorAll('a[href],button:not([disabled]),input:not([disabled])')].filter(x=>x.getClientRects().length);
  if(!focusable.length)return;
  const first=focusable[0],last=focusable[focusable.length-1];
  if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
  else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
 }
});
window.addEventListener("area33:side-counter-open",e=>openCounter(e.detail?.productId||"",e.detail?.tab||"inspect"));
document.querySelectorAll("[data-side-counter-product]").forEach(button=>{
 button.addEventListener("click",e=>{e.preventDefault();openCounter(button.dataset.sideCounterProduct);});
});
renderShop();
