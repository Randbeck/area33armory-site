"use strict";
import {REFERENCE_PRODUCTS,researchTitle} from "./product-room-research.mjs";
import {researchPhotoFor} from "./research-photo-license.mjs";
import {validateFeaturedPublic,visibleFeatured} from "./featured-opportunities.mjs";
import {validatePublicDeals} from "./deals-public-contract.mjs";
/* Public approval manifest only. Internal Randbeck candidate lists, dealer
 * cost, ROI, margins and private supplier records never enter this page. */
const root=document.getElementById("featured-products");
const status=document.getElementById("featured-coverage");
const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;};
const dealsMode=!!document.querySelector('[data-featured-mode="deals"]');
function drawDeals(deals){
 if(!root)return;
 root.replaceChildren();
 if(!deals.length){
   const state=el("div","deal-empty");
   const copy=el("div","deal-empty-copy");
   copy.append(el("span","deal-empty-eyebrow","AREA 33 · DEALS UNDER REVIEW"),
     el("h3","","The right deal is worth finding."),
     el("p","","No current specials have passed our public price, inventory and offer review. Randbeck-powered picks and sale items will appear here when verified—not as made-up bargains."));
   const link=el("a","deal-shop-link","Shop by Department ↗");
   link.href="#shop-departments";copy.append(link);
   state.append(copy);root.append(state);
   if(status)status.textContent="No live deals published. A verified Area 33 delivered price will include merchandise, applicable tax, shipping and Area 33 charges; receiving FFL transfer fees are separate.";
   return;
 }
 for(const deal of deals){
  const product=REFERENCE_PRODUCTS.find(x=>x.kind==="firearm"&&x.id===deal.productId);
  if(!product)continue;
  const card=el("article","featured-tile deal-tile");
  const picture=el("div","featured-media");
  const photo=researchPhotoFor(product);
  if(photo){
   const img=el("img");img.src=photo.src;img.alt=photo.caption;img.referrerPolicy="no-referrer";img.loading="lazy";
   img.addEventListener("error",()=>{img.hidden=true;picture.append(el("span","featured-no-photo","Approved photo unavailable"));});
   picture.append(img);
  }else picture.append(el("span","featured-no-photo","Exact-product image not publication-cleared"));
  const copy=el("div","featured-copy");
  copy.append(el("small","featured-tag",deal.label),el("h3","",deal.headline),
    el("p","",deal.description),el("p","deal-terms",deal.offerTerms),
    el("span","featured-product-name",researchTitle(product)),
    el("strong","deal-price-note","Area 33 delivered quote required · receiving FFL fee separate"));
  const button=el("a","featured-link","Inspect this offer ↗");
  button.href="six-view-counter.html?product="+encodeURIComponent(product.id)+"#product-counter";
  if(document.getElementById("area33-side-counter"))
   button.addEventListener("click",e=>{
    e.preventDefault();
    window.dispatchEvent(new CustomEvent("area33:side-counter-open",{detail:{productId:product.id}}));
   });
  copy.append(button);card.append(picture,copy);root.append(card);
 }
 if(status)status.textContent="Verified public promotional entries, not universal checkout prices. Confirm the final Area 33 delivered quote for your destination. Receiving FFL transfer fees are excluded.";
}

function draw(rows){
 if(!root)return;
 root.replaceChildren();
 const isPublic=rows.some(x=>x.published===true);
 for(const featured of rows){
  const product=REFERENCE_PRODUCTS.find(x=>x.kind==="firearm"&&x.id===featured.productId);
  if(!product)continue;
  const article=el("article","featured-tile");
  const media=el("div","featured-media");
  const photo=researchPhotoFor(product);
  if(photo){
   const img=el("img");
   img.src=photo.src;img.alt=photo.caption;img.loading="lazy";img.referrerPolicy="no-referrer";
   img.addEventListener("error",()=>{img.hidden=true;media.append(el("span","featured-no-photo","Exact image unavailable"));});
   media.append(img);
  }else media.append(el("span","featured-no-photo","No approved exact-product image"));
  const details=el("div","featured-copy");
  details.append(el("small","featured-tag",featured.label),
   el("h3","",featured.headline),el("p","",featured.description),
   el("span","featured-product-name",researchTitle(product)));
  const a=el("a","featured-link","Bring to the counter ↗");
  a.href="six-view-counter.html?product="+encodeURIComponent(product.id)+"#product-counter";
  if(document.getElementById("area33-side-counter")){
   a.textContent="Inspect beside the shop ↗";
   a.addEventListener("click",e=>{
    e.preventDefault();
    window.dispatchEvent(new CustomEvent("area33:side-counter-open",{detail:{productId:product.id}}));
   });
  }else if(document.getElementById("product-counter")){
   a.addEventListener("click",e=>{
    e.preventDefault();
    window.dispatchEvent(new CustomEvent("area33:featured-open",{detail:{productId:product.id}}));
   });
  }
  details.append(a);article.append(media,details);root.append(article);
 }
 if(status)status.textContent=isPublic?
  "These entries were approved for public editorial featuring. Their price and availability still require a separate verified quote.":
  "Editorial research highlights only — not live Randbeck deals, stock confirmations or price offers. No opportunities have been approved for public featuring yet.";
}
async function init(){
 if(!root)return;
 if(dealsMode){
  drawDeals([]);
  try{
   const response=await fetch("assets/deals-public.json",{credentials:"omit",cache:"no-store"});
   if(!response.ok)return;
   const approved=validatePublicDeals(await response.json());
   if(approved)drawDeals(approved);
  }catch{/* Keep honest no-deals empty state. */}
  return;
 }
 draw(visibleFeatured([]));
 try{
  const response=await fetch("assets/featured-public.json",{credentials:"omit",cache:"no-store"});
  if(!response.ok)return;
  const parsed=validateFeaturedPublic(await response.json());
  if(parsed)draw(visibleFeatured(parsed));
 }catch{/* Retain explicitly labeled research highlights. */}
}
init();
