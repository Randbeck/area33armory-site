/* Open-license RESEARCH photo viewer only. Does not touch the separate approved
   Area 33 catalog gallery, image rights, inventory, prices or accessory pairings. */
import {researchPhotoFor} from "./research-photo-license.mjs";

export function clampPhotoZoom(value){
 return Number.isFinite(value)?Math.min(3.5,Math.max(1,value)):1;
}
export function clampPhotoPan({x=0,y=0},width,height,zoom){
 const limitX=Math.max(0,(width*(zoom-1))/2);
 const limitY=Math.max(0,(height*(zoom-1))/2);
 return {x:Math.min(limitX,Math.max(-limitX,Number.isFinite(x)?x:0)),y:Math.min(limitY,Math.max(-limitY,Number.isFinite(y)?y:0))};
}
export function createResearchPhotoViewer(){
 const $=id=>document.getElementById(id);
 const container=$("licensed-photo-stage"),viewport=$("licensed-photo-viewport"),image=$("licensed-photo-image");
 const error=$("licensed-photo-error"),zoomLabel=$("licensed-zoom-level");
 const minus=$("licensed-zoom-out"),plus=$("licensed-zoom-in"),reset=$("licensed-zoom-reset");
 let selectedId=null,zoom=1,pan={x:0,y:0},pointer=null;
 function render(){
  pan=clampPhotoPan(pan,viewport.clientWidth||500,viewport.clientHeight||250,zoom);
  image.style.setProperty("--photo-zoom",String(zoom));
  image.style.setProperty("--photo-x",pan.x+"px");
  image.style.setProperty("--photo-y",pan.y+"px");
  viewport.dataset.zoomed=String(zoom>1);
  viewport.style.touchAction=zoom>1?"none":"pan-y";
  zoomLabel.textContent=Math.round(zoom*100)+"%";
  minus.disabled=zoom<=1;plus.disabled=zoom>=3.5;
  reset.disabled=zoom===1&&pan.x===0&&pan.y===0;
 }
 function setZoom(value){
  const next=clampPhotoZoom(value);
  if(next===1)pan={x:0,y:0};
  zoom=next;render();
 }
 function show(item){
  const media=researchPhotoFor(item);
  if(!media){hide();return false;}
  const changed=selectedId!==media.productId;
  container.hidden=false;
  if(changed){
   selectedId=media.productId;zoom=1;pan={x:0,y:0};pointer=null;
   error.hidden=true;image.hidden=false;
   image.alt=media.caption+". "+media.view+". Photo by "+media.author;
   image.src=media.src;
   $("licensed-author").textContent=media.author;
   $("licensed-source").href=media.sourcePage;
   $("licensed-license").href=media.licenseUrl;
   $("licensed-license").textContent=media.license;
   $("licensed-modifications").textContent=media.modifications;
  }
  render();
  return true;
 }
 function hide(){
  selectedId=null;container.hidden=true;
  image.removeAttribute("src");image.alt="";
  pointer=null;zoom=1;pan={x:0,y:0};
 }
 image.addEventListener("error",()=>{
  if(container.hidden)return;
  image.hidden=true;error.hidden=false;
 });
 image.addEventListener("load",()=>{
  if(container.hidden)return;
  image.hidden=false;error.hidden=true;
 });
 plus.addEventListener("click",()=>setZoom(zoom+.25));
 minus.addEventListener("click",()=>setZoom(zoom-.25));
 reset.addEventListener("click",()=>{pan={x:0,y:0};setZoom(1);});
 viewport.addEventListener("pointerdown",e=>{
  if(zoom<=1||(e.pointerType==="mouse"&&e.button!==0))return;
  pointer={id:e.pointerId,x:e.clientX,y:e.clientY,start:{...pan}};
  viewport.setPointerCapture?.(e.pointerId);
 });
 viewport.addEventListener("pointermove",e=>{
  if(!pointer||pointer.id!==e.pointerId)return;
  pan={x:pointer.start.x+e.clientX-pointer.x,y:pointer.start.y+e.clientY-pointer.y};
  render();
 });
 const finish=e=>{if(pointer&&pointer.id===e.pointerId)pointer=null;};
 viewport.addEventListener("pointerup",finish);
 viewport.addEventListener("pointercancel",finish);
 viewport.addEventListener("keydown",e=>{
  if(zoom<=1)return;
  const delta={ArrowLeft:[-25,0],ArrowRight:[25,0],ArrowUp:[0,-25],ArrowDown:[0,25]}[e.key];
  if(!delta)return;
  e.preventDefault();pan={x:pan.x+delta[0],y:pan.y+delta[1]};render();
 });
 return {show,hide};
}
