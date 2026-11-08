"use strict";
import {REFERENCE_PRODUCTS,researchTitle} from "./product-room-research.mjs";
import {researchPhotoFor} from "./research-photo-license.mjs";
import {validateFeaturedPublic,visibleFeatured} from "./featured-opportunities.mjs";
/* Public approval manifest only. Internal Randbeck candidate lists, dealer
 * cost, ROI, margins and private supplier records never enter this page. */
const root=document.getElementById("featured-products");
const status=document.getElementById("featured-coverage");
const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;};
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
 draw(visibleFeatured([]));
 try{
  const response=await fetch("assets/featured-public.json",{credentials:"omit",cache:"no-store"});
  if(!response.ok)return;
  const parsed=validateFeaturedPublic(await response.json());
  if(parsed)draw(visibleFeatured(parsed));
 }catch{/* Retain explicitly labeled research highlights. */}
}
init();
