/* Area 33 hands-on product bench — published-approved and explicitly licensed
   images only. A separate editorial example NEVER stands in for a customer's
   selected product, accessory or fitment. No private dealer data or telemetry. */
import {REFERENCE_PRODUCTS,researchTitle} from "./product-room-research.mjs";
import {galleryAllowed} from "./catalog-gallery.mjs";
import {researchPhotoFor} from "./research-photo-license.mjs";
import {evaluatePairing} from "./pairing-evidence.mjs";
import {inspirationForEditorial} from "./showroom-inspiration.mjs";
const PHOTO_NONE=null;
export function benchPhotoFor(item){
 if(!item)return PHOTO_NONE;
 if(item.approvedItem){
  if(!galleryAllowed(item.approvedItem))return PHOTO_NONE;
  const frame=item.approvedItem.images[0];
  return {src:frame.url,alt:frame.alt,kind:"owner-approved",credit:"Owner-approved exact-product catalog photo."};
 }
 const media=researchPhotoFor(item);
 if(!media)return PHOTO_NONE;
 return {src:media.src,alt:media.caption,kind:"cc-research",
   credit:"Photo: "+media.author+" · "+media.license+". Full license and source are shown in the main viewer."};
}
export function benchEvidenceFor(firearm,accessory){
 if(!firearm||!accessory)return {status:"none",label:"CHOOSE AN ACCESSORY",
  summary:"Choose a real accessory to see whether a manufacturer has documented an exact match, broader guidance, or a differing mounting interface.",
  caution:"No visual fitment is implied."};
 const verdict=evaluatePairing(firearm,accessory);
 return {status:verdict.status,label:verdict.short,summary:verdict.summary,caution:verdict.caution};
}
export function shareBenchUrl(locationHref,firearm,accessory,knownItems=REFERENCE_PRODUCTS){
 if(!firearm||!Array.isArray(knownItems)||!knownItems.some(x=>x.id===firearm.id&&x.kind==="firearm"))return null;
 if(accessory&&!knownItems.some(x=>x.id===accessory.id&&x.kind==="accessory"))return null;
 let url;try{url=new URL(locationHref);}catch{return null;}
 if(!["https:","http:"].includes(url.protocol)||url.username||url.password)return null;
 url.hash="";url.search="";
 url.searchParams.set("product",firearm.id);
 if(accessory)url.searchParams.set("accessory",accessory.id);
 return url.href;
}
export function createExperienceBench({onChooseAccessory,onClearAccessory,getKnownItems}={}){
 if(typeof document==="undefined")return {render(){}};
 const $=id=>document.getElementById(id);
 const safeImg=(id,emptyId,photo)=>{
  const img=$(id),placeholder=$(emptyId);
  img.hidden=!photo;placeholder.hidden=!!photo;
  if(photo){img.alt=photo.alt;img.src=photo.src;}
  else {img.removeAttribute("src");img.alt="";}
 };
 const setLink=(id,url)=>{
  const node=$(id);node.hidden=!url;
  if(url)node.href=url;
  else node.removeAttribute("href");
 };
 const tabs=[["bench-tab-selection","bench-pair-pane"],["bench-tab-inspiration","bench-inspiration-pane"]];
 let shownInspiration=false,selection=null,selectedAccessory=null;
 function changeTab(index,focus=false){
  tabs.forEach(([tab,pane],i)=>{
   $(tab).setAttribute("aria-selected",String(i===index));
   $(tab).tabIndex=i===index?0:-1;
   $(pane).hidden=i!==index;
  });
  if(index===1)setupEditorial();
  if(focus)$(tabs[index][0]).focus();
 }
 function setupEditorial(){
  if(shownInspiration)return;shownInspiration=true;
  const media=inspirationForEditorial("real-world-customization-example");
  if(!media)return;
  const photo=$("bench-inspiration-photo");
  photo.alt=media.alt;
  photo.src=media.src;
  $("bench-inspiration-caption").textContent=media.caption;
  $("bench-inspiration-source").href=media.source;
  $("bench-inspiration-creator").textContent=media.creator;
  $("bench-inspiration-license").href=media.licenseUrl;
  $("bench-inspiration-license").textContent=media.license;
  $("bench-inspiration-modifications").textContent=media.modifications;
 }
 function render(firearm,accessory){
  selection=firearm;selectedAccessory=accessory;
  if(!firearm)return;
  $("bench-firearm-name").textContent=researchTitle(firearm);
  $("bench-firearm-subtitle").textContent=firearm.subtitle||"Exact real product reference";
  $("bench-firearm-tag").textContent=firearm.approvedItem?"APPROVED PUBLIC RECORD":"MAKER REFERENCE";
  $("bench-accessory-name").textContent=accessory?researchTitle(accessory):"Nothing selected yet";
  $("bench-accessory-subtitle").textContent=accessory?(accessory.subtitle||"Exact real accessory reference"):"Choose a real accessory from the wall";
  $("bench-accessory-tag").textContent=accessory?"SELECTED":"OPTIONAL";
  $("bench-accessory-empty-caption").textContent=accessory?
   "No rights-cleared photo for this exact accessory in Area 33. Open its maker's actual photographs.":
   "Choose a specific model below. No accessory is selected yet.";
  const photo=benchPhotoFor(firearm),accessoryPhoto=benchPhotoFor(accessory);
  safeImg("bench-firearm-image","bench-firearm-no-image",photo);
  safeImg("bench-accessory-image","bench-accessory-no-image",accessoryPhoto);
  $("bench-firearm-photo-credit").hidden=!photo;
  $("bench-firearm-photo-credit").textContent=photo?.credit||"";
  setLink("bench-firearm-link",firearm.source||null);
  setLink("bench-accessory-link",accessory?.source||null);
  const verdict=benchEvidenceFor(firearm,accessory);
  $("bench-proof-badge").textContent=verdict.label;
  $("bench-proof-badge").dataset.status=verdict.status;
  $("bench-proof-summary").textContent=verdict.summary;
  $("bench-proof-caution").textContent=verdict.caution;
  $("bench-clear-accessory").disabled=!accessory;
  $("bench-copy-status").textContent="";
  document.querySelectorAll("[data-bench-try]").forEach(btn=>{
    btn.setAttribute("aria-pressed",String(btn.dataset.benchTry===accessory?.id));
  });
 }
 $("bench-firearm-image").addEventListener("error",()=>safeImg("bench-firearm-image","bench-firearm-no-image",null));
 $("bench-accessory-image").addEventListener("error",()=>safeImg("bench-accessory-image","bench-accessory-no-image",null));
 $("bench-inspiration-photo").addEventListener("error",()=>{
  $("bench-inspiration-photo").hidden=true;
  $("bench-inspiration-error").hidden=false;
 });
 tabs.forEach(([tab],idx)=>{
  $(tab).addEventListener("click",()=>changeTab(idx));
  $(tab).addEventListener("keydown",e=>{
   if(!["ArrowLeft","ArrowRight","Home","End"].includes(e.key))return;
   e.preventDefault();
   const next=e.key==="Home"?0:e.key==="End"?tabs.length-1:(idx+(e.key==="ArrowRight"?1:tabs.length-1))%tabs.length;
   changeTab(next,true);
  });
 });
 document.querySelectorAll("[data-bench-try]").forEach(btn=>btn.addEventListener("click",()=>{
  const item=(getKnownItems?.()||REFERENCE_PRODUCTS).find(x=>x.id===btn.dataset.benchTry&&x.kind==="accessory");
  if(item)onChooseAccessory?.(item);
  changeTab(0);
  $("hands-on-bench").scrollIntoView({behavior:"smooth",block:"nearest"});
 }));
 $("bench-clear-accessory").addEventListener("click",()=>{onClearAccessory?.();changeTab(0);});
 $("bench-link-copy").addEventListener("click",async()=>{
  const url=shareBenchUrl(location.href,selection,selectedAccessory,getKnownItems?.()||REFERENCE_PRODUCTS);
  if(!url){$("bench-copy-status").textContent="No valid public product selection to share.";return;}
  try{
   if(!navigator.clipboard?.writeText)throw Error("Clipboard unavailable");
   await navigator.clipboard.writeText(url);
   $("bench-copy-status").textContent="Link copied. It restores this selection and its research evidence.";
  }catch{
   $("bench-copy-status").textContent="Copy this URL: "+url;
  }
 });
 return {render,changeTab};
}
