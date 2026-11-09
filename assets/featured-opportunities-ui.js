"use strict";
import {REFERENCE_PRODUCTS,researchTitle} from "./product-room-research.mjs";
import {researchPhotoFor} from "./research-photo-license.mjs";
import {validateFeaturedPublic,visibleFeatured} from "./featured-opportunities.mjs";
import {validatePublicDeals} from "./deals-public-contract.mjs";
import {selectLz33,lz33CampaignDraft} from "./lz33-campaign.mjs";
/* Public approval manifest only. Internal Randbeck candidate lists, dealer
 * cost, ROI, margins and private supplier records never enter this page. */
const root=document.getElementById("featured-products");
const status=document.getElementById("featured-coverage");
const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;};
const dealsMode=!!document.querySelector('[data-featured-mode="deals"]');
let landingForEmail=null;
function syncLz33(primary){
 const hero=document.getElementById("lz33");
 landingForEmail=primary;
 if(!hero)return;
 const status=document.getElementById("lz33-hero-state");
 const headline=document.getElementById("lz33-hero-headline");
 const description=document.getElementById("lz33-hero-description");
 const terms=document.getElementById("lz33-hero-terms");
 const inspect=document.getElementById("lz33-hero-inspect");
 if(!primary){
  status.textContent="AWAITING APPROVED LANDING";
  headline.textContent="Something worth landing for.";
  description.textContent="No verified feature has landed yet. When an exceptional Area 33 offer passes product, pricing, availability and owner review, you'll find it here.";
  terms.textContent="An Area 33 delivered quote will include applicable tax, shipping and Area 33 charges. Receiving FFL transfer fee separate.";
  inspect.hidden=true;
  inspect.removeAttribute("data-side-counter-product");
  return;
 }
 status.textContent="VERIFIED PUBLIC OFFER";
 headline.textContent=primary.headline;
 description.textContent=primary.description;
 terms.textContent=primary.offerTerms+" · Area 33 delivered quote required for your destination; receiving FFL fee separate.";
 inspect.hidden=false;
 inspect.href="six-view-counter.html?product="+encodeURIComponent(primary.productId)+"#product-counter";
 inspect.setAttribute("data-side-counter-product",primary.productId);
}
function drawDeals(deals){
 if(!root)return;
 const {primary,justLanded}=selectLz33(deals);
 syncLz33(primary);
 root.replaceChildren();
 if(!justLanded.length){
  if(status)status.textContent=primary?
   "No additional landings are published. Today's Landing above is the only approved public feature.":
   "No current specials have passed our public price, inventory and offer review. No live LZ 33 landings are published yet.";
  return; // No giant repeated empty-deal card.
 }
 for(const deal of justLanded){
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
  copy.append(el("small","featured-tag","JUST LANDED · "+deal.label),el("h3","",deal.headline),
   el("p","",deal.description),el("p","deal-terms",deal.offerTerms),
   el("span","featured-product-name",researchTitle(product)),
   el("strong","deal-price-note","Area 33 delivered quote required · receiving FFL fee separate"));
  const button=el("a","featured-link","Inspect this landing ↗");
  button.href="six-view-counter.html?product="+encodeURIComponent(product.id)+"#product-counter";
  if(document.getElementById("area33-side-counter"))
   button.addEventListener("click",e=>{
    e.preventDefault();
    window.dispatchEvent(new CustomEvent("area33:side-counter-open",{detail:{productId:product.id}}));
   });
  copy.append(button);card.append(picture,copy);root.append(card);
 }
 if(status)status.textContent="Only owner-approved, current public promotions are shown. Verify the destination quote; receiving FFL transfer fees are separate.";
}
function initLz33EmailPreview(){
 // Internal design preview only; this contains no private data and never sends mail.
 // Server-side authentication will be required for any future campaign tooling.
 const ownerTools=document.querySelector(".lz33-owner-tools");
 const previewEnabled=new URLSearchParams(location.search).get("area33_lz33_owner_preview")==="1";
 if(ownerTools&&previewEnabled)ownerTools.hidden=false;
 const inspect=document.getElementById("lz33-hero-inspect");
 inspect?.addEventListener("click",event=>{
  if(!landingForEmail||!document.getElementById("area33-side-counter"))return;
  event.preventDefault();
  window.dispatchEvent(new CustomEvent("area33:side-counter-open",{detail:{productId:landingForEmail.productId}}));
 });
 const dialog=document.getElementById("lz33-email-preview");
 const open=document.getElementById("lz33-email-preview-open");
 const close=document.getElementById("lz33-email-preview-close");
 if(!dialog||!open||!close)return;
 open.addEventListener("click",()=>{
  const draft=lz33CampaignDraft(landingForEmail);
  document.getElementById("lz33-email-subject").textContent=draft.subject;
  document.getElementById("lz33-email-heading").textContent=draft.heading;
  document.getElementById("lz33-email-body").textContent=draft.body;
  document.getElementById("lz33-email-footer").textContent=draft.footer;
  dialog.showModal();
 });
 close.addEventListener("click",()=>dialog.close());
 dialog.addEventListener("click",event=>{if(event.target===dialog)dialog.close();});
}
initLz33EmailPreview();

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
