"use strict";
/* Area 33 public manufacturer research gallery. This is NOT the approved
 * distributor catalog. Every photo is from the exact license-reviewed
 * research manifest; never replace a missing photo with a similar SKU. */
import {REFERENCE_PRODUCTS,researchTitle} from "./product-room-research.mjs";
import {researchPhotoFor} from "./research-photo-license.mjs";
import {findResearchProducts} from "./customer-experience.mjs";
const $=id=>document.getElementById(id);
const make=(tag,className,text)=>{
 const n=document.createElement(tag);
 if(className)n.className=className;
 if(text!==undefined)n.textContent=text;
 return n;
};
const all=REFERENCE_PRODUCTS.filter(x=>x.kind==="firearm");
const gallery=$("research-catalog-grid"),search=$("research-catalog-search"),select=$("research-catalog-type"),
 total=$("research-catalog-total"),dialog=$("research-catalog-dialog"),body=$("research-catalog-detail");
const secureLink=(label,url)=>{
 const a=make("a","catalog-origin",label);
 if(typeof url==="string"&&/^https:\/\//.test(url)){
  a.href=url;a.target="_blank";a.rel="noopener noreferrer";
 }else{a.textContent=label+" (link unavailable)";}
 return a;
};
function photoFor(product,{large=false}={}){
 const photo=researchPhotoFor(product);
 const wrapper=make("div",large?"research-modal-image":"research-card-image");
 if(!photo){
  const empty=make("div","research-photo-unavailable");
  empty.append(make("span","research-photo-brand",product.brand),make("small","","Exact-product photo not yet approved."));
  wrapper.append(empty);
  return wrapper;
 }
 const img=make("img");
 img.src=photo.src;img.alt=photo.caption;img.loading=large?"eager":"lazy";
 img.referrerPolicy="no-referrer";img.decoding="async";
 img.addEventListener("error",()=>{
  img.remove();
  wrapper.replaceChildren(make("p","research-photo-unavailable","Photo unavailable; product reference still accessible."));
 });
 wrapper.append(img);
 if(large){
  const credit=make("p","research-photo-credit","Photograph: "+photo.author+" · "+photo.license);
  const a=secureLink("Image source and license ↗",photo.sourcePage);
  wrapper.append(credit,a);
 }
 return wrapper;
}
function inspect(product){
 if(!dialog?.showModal||!body)return;
 body.replaceChildren(photoFor(product,{large:true}));
 const info=make("div","research-modal-body");
 info.append(make("span","research-type-label",product.department.toUpperCase()+" / "+product.brand),
  make("h2","",researchTitle(product)),make("p","research-modal-subtitle",product.subtitle));
 const facts=make("ul","research-modal-facts");
 for(const f of product.facts||[])facts.append(make("li","",f));
 info.append(facts,make("p","research-limit",product.note));
 const note=make("div","research-modal-availability");
 note.append(make("strong","","Price and availability not verified"),
  make("p","","This is a manufacturer research reference, not a sellable listing. Area 33's eventual delivered price will include applicable tax, shipping and our charges; a receiving FFL transfer fee is separate."));
 info.append(note);
 const actions=make("div","research-modal-actions");
 const counter=make("a","research-primary-link","Open with EVA at the counter ↗");
 counter.href="index.html?inspect="+encodeURIComponent(product.id)+"&eva=1";
 actions.append(counter,secureLink("Manufacturer documentation ↗",product.source));
 info.append(actions);body.append(info);
 dialog.showModal();
}
function render(){
 if(!gallery)return;
 const query=search.value.trim(),category=select.value;
 const products=findResearchProducts(query,category,all);
 if(!query&&category==="all")products.sort((a,b)=>Number(!!researchPhotoFor(b))-Number(!!researchPhotoFor(a))||researchTitle(a).localeCompare(researchTitle(b)));
 gallery.replaceChildren();
 total.textContent=products.length+" documented manufacturer references · not live inventory";
 if(!products.length){
  gallery.append(make("p","research-none","No matches in the limited reference set. Try a manufacturer name or a broader category."));
  return;
 }
 for(const product of products){
  const card=make("article","research-listing");
  card.append(photoFor(product));
  const info=make("div","research-listing-content");
  info.append(make("span","research-type-label",product.department.toUpperCase()+" / "+product.brand),
   make("h3","",product.model),
   make("p","",product.subtitle),
   make("span","research-listing-status","RESEARCH ONLY · PRICE NOT QUOTED"));
  const btn=make("button","research-inspect","Inspect this model ↗");btn.type="button";
  btn.addEventListener("click",()=>inspect(product));
  info.append(btn);card.append(info);gallery.append(card);
 }
}
if(gallery){
 search.addEventListener("input",render);
 select.addEventListener("change",render);
 $("research-catalog-clear")?.addEventListener("click",()=>{search.value="";select.value="all";render();search.focus();});
 $("research-dialog-close")?.addEventListener("click",()=>dialog.close());
 dialog?.addEventListener("click",e=>{if(e.target===dialog)dialog.close();});
 render();
}
