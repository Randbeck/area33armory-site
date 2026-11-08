/* Area 33 licensed image theater. Actual photographs are tied to an exact
   reference ID and never physically composited to suggest accessory fit. */
import {researchPhotoFor} from "./research-photo-license.mjs";
import {benchPhotoFor} from "./experience-bench.mjs";
import {evaluatePairing} from "./pairing-evidence.mjs";
import {researchTitle} from "./product-room-research.mjs";
export const theaterZoom=v=>Number.isFinite(v)?Math.max(1,Math.min(4,v)):1;
export function theaterPan(p,rect,zoom){
 const x=Math.max(0,(rect.width||0)*(zoom-1)/2),y=Math.max(0,(rect.height||0)*(zoom-1)/2);
 return {x:x===0?0:Math.max(-x,Math.min(x,Number.isFinite(p?.x)?p.x:0)),
  y:y===0?0:Math.max(-y,Math.min(y,Number.isFinite(p?.y)?p.y:0))};
}
export function createPhotoTheater({chooseFirearm,chooseAccessory}={}){
 if(typeof document==="undefined")return {render(){}};
 const $=id=>document.getElementById(id);
 const stage=$("theater-stage"),image=$("theater-main-image");
 let currentId=null,zoom=1,pan={x:0,y:0},drag=null,selected=null;
 const currentPhoto=()=>selected?benchPhotoFor(selected):null;
 const limits=()=>theaterPan(pan,stage.getBoundingClientRect(),zoom);
 function display(){
  pan=limits();
  image.style.setProperty("--stage-zoom",String(zoom));
  image.style.setProperty("--stage-pan-x",pan.x+"px");
  image.style.setProperty("--stage-pan-y",pan.y+"px");
  stage.dataset.zoomed=String(zoom>1);
  stage.style.touchAction=zoom>1?"none":"pan-y";
  $("theater-zoom-count").textContent=Math.round(zoom*100)+"%";
  $("theater-zoom-out").disabled=zoom<=1||image.hidden;
  $("theater-zoom-in").disabled=zoom>=4||image.hidden;
  $("theater-zoom-reset").disabled=zoom===1;
  $("theater-fullscreen").disabled=image.hidden;
 }
 function setZoom(v){
  zoom=theaterZoom(v);
  if(zoom===1)pan={x:0,y:0};
  display();
 }
 function present(item,accessory){
  selected=item;
  $("theater-product-title").textContent=researchTitle(item);
  $("theater-department").textContent=(item.department||"PRODUCT").toUpperCase()+" / REAL REFERENCE";
  const media=researchPhotoFor(item),photo=currentPhoto();
  const changed=currentId!==item.id;currentId=item.id;
  if(changed){zoom=1;pan={x:0,y:0};}
  $("theater-no-image").hidden=!!photo;
  $("theater-image-error").hidden=true;
  image.hidden=!photo;
  if(photo){
   if(image.src!==photo.src)image.src=photo.src;
   image.alt=photo.alt;
   $("theater-photo-note").textContent=media?"Real, licensed research photograph · one original view":"Owner-approved exact-product photo";
  }else{
   image.removeAttribute("src");image.alt="";
   $("theater-photo-note").textContent="Photo not approved · manufacturer link";
   const a=$("theater-maker-link");a.hidden=!item.source;
   if(item.source)a.href=item.source;
  }
  $("theater-attribution").hidden=!media;
  if(media){
   $("theater-author").textContent=media.author;
   $("theater-origin").href=media.sourcePage;
   $("theater-license").href=media.licenseUrl;
   $("theater-license").textContent=media.license;
   $("theater-modifications").textContent=media.modifications;
   $("theater-source-fallback").href=media.sourcePage;
  }
  const optic=accessory?researchPhotoFor(accessory):null;
  const opticPhoto=accessory?benchPhotoFor(accessory):null;
  $("theater-accessory-title").textContent=accessory?researchTitle(accessory):"Nothing selected yet";
  $("theater-accessory-description").textContent=accessory?
    (accessory.subtitle||"Actual accessory research")+" · displayed separately":
    "Pick an accessory below to explore it without leaving the room.";
  const aimg=$("theater-accessory-image");
  aimg.hidden=!opticPhoto;
  $("theater-accessory-placeholder").hidden=!!opticPhoto;
  if(opticPhoto){aimg.alt=opticPhoto.alt;if(aimg.src!==opticPhoto.src)aimg.src=opticPhoto.src;}
  else {aimg.removeAttribute("src");aimg.alt="";}
  $("theater-accessory-credit").hidden=!optic;
  if(optic){
   // Source and author are separate, not an invented endorsement.
   const node=$("theater-accessory-credit");
   node.replaceChildren();
   node.append(document.createTextNode("Photo: "+optic.author+" · "+optic.license+" · "));
   const link=document.createElement("a");
   link.textContent="Photo source ↗";link.href=optic.sourcePage;
   link.target="_blank";link.rel="noopener noreferrer";
   node.append(link);
  }
  const proof=accessory?evaluatePairing(item,accessory):null;
  $("theater-fit-status").dataset.status=proof?.status||"none";
  $("theater-fit-status").textContent=proof?proof.short:"CHOOSE AN ACCESSORY";
  $("theater-fit-summary").textContent=proof?
   proof.summary+" Visual pairing has not been independently approved.":
   "No accessory selected. Neither physical pairing nor price has been verified.";
  display();
 }
 image.addEventListener("error",()=>{
  if(image.hidden||!selected)return;
  image.hidden=true;
  $("theater-image-error").hidden=false;
  display();
 });
 image.addEventListener("load",()=>{
  if(!selected||!currentPhoto())return;
  image.hidden=false;$("theater-image-error").hidden=true;display();
 });
 $("theater-accessory-image").addEventListener("error",()=>{
  $("theater-accessory-image").hidden=true;
  $("theater-accessory-placeholder").hidden=false;
 });
 $("theater-zoom-in").addEventListener("click",()=>setZoom(zoom+.25));
 $("theater-zoom-out").addEventListener("click",()=>setZoom(zoom-.25));
 $("theater-zoom-reset").addEventListener("click",()=>{pan={x:0,y:0};setZoom(1);});
 stage.addEventListener("pointerdown",e=>{
  if(zoom<=1||(e.pointerType==="mouse"&&e.button!==0))return;
  drag={id:e.pointerId,x:e.clientX,y:e.clientY,pan:{...pan}};
  stage.setPointerCapture?.(e.pointerId);
 });
 stage.addEventListener("pointermove",e=>{
  if(!drag||drag.id!==e.pointerId)return;
  pan={x:drag.pan.x+e.clientX-drag.x,y:drag.pan.y+e.clientY-drag.y};
  display();
 });
 for(const event of ["pointerup","pointercancel"])stage.addEventListener(event,e=>{
  if(drag?.id===e.pointerId)drag=null;
 });
 stage.addEventListener("keydown",e=>{
  if(["ArrowLeft","ArrowRight","ArrowUp","ArrowDown"].includes(e.key)&&zoom>1){
   const d={ArrowLeft:[-32,0],ArrowRight:[32,0],ArrowUp:[0,-32],ArrowDown:[0,32]}[e.key];
   e.preventDefault();pan={x:pan.x+d[0],y:pan.y+d[1]};display();
  }
  if(["=","+"].includes(e.key)){e.preventDefault();setZoom(zoom+.25);}
  if(e.key==="-"){e.preventDefault();setZoom(zoom-.25);}
 });
 $("theater-fullscreen").addEventListener("click",async()=>{
  if(!selected||image.hidden)return;
  try{
   if(stage.requestFullscreen)await stage.requestFullscreen();
   else throw Error("Fullscreen unavailable");
   stage.focus();
  }catch{
   $("theater-fit-summary").textContent="Fullscreen isn't supported here. You can still zoom and drag the original photo.";
  }
 });
 $("theater-try-meopta").addEventListener("click",()=>{
  chooseAccessory?.("meopta-optika6-3-18x56-rd-sfp");
 });
 $("theater-switch-ruger").addEventListener("click",()=>{
  const next=currentId==="ruger-precision-6mm-2019-photo"?
    "ruger-precision-308-gen1":"ruger-precision-6mm-2019-photo";
  chooseFirearm?.(next);
 });
 return {render:present};
}
