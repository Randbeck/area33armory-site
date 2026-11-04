"use strict";
import {sanitizeShowroomManifest} from "./showroom-contract.mjs";
const byId=id=>document.getElementById(id);
const elements={empty:byId("empty"),app:byId("app"),select:byId("product"),config:byId("configuration"),base:byId("base-image"),image:byId("selected-image"),slider:byId("angle"),compare:byId("compare"),split:byId("split-control")};
let items=[],current=null,index=0,configuration=null,zoom=1,startX=null,token=0;
const el=(tag,label,value)=>{const node=document.createElement(tag);if(label)node.className=label;if(value!==undefined)node.textContent=value;return node;};
const exactName=item=>[item.manufacturer,item.model,item.variant].filter(Boolean).join(" ");
function presentError(msg){const e=byId("viewer-error");e.textContent=msg;e.hidden=false;}
function setFrame(){
  if(!current)return;
  const serial=++token,base=current.frames[index],overlay=configuration?configuration.frames[index]:null;
  elements.base.onload=()=>{if(serial===token)byId("viewer-error").hidden=true;};
  elements.base.onerror=()=>{if(serial===token)presentError("Approved base photo could not be loaded; this view cannot be shown.");};
  elements.base.src=base.src;elements.base.alt=base.alt;
  if(overlay){
    elements.image.onerror=()=>{if(serial===token){elements.image.hidden=true;presentError("Approved configuration image could not load; no replacement is being shown.");}};
    elements.image.src=overlay.src;elements.image.alt=overlay.alt;
  }
  elements.image.hidden=!overlay;
  byId("compare").disabled=!overlay;
  if(!overlay)elements.compare.checked=false;
  const comparing=!!overlay&&elements.compare.checked;
  elements.split.disabled=!comparing;
  byId("split").hidden=!comparing;
  if(comparing){
    elements.image.style.clipPath="inset(0 0 0 "+elements.split.value+"%)";
    byId("split").style.left=elements.split.value+"%";
  }else elements.image.style.clipPath="none";
  const angleText=(index+1)+" / "+current.frames.length;
  byId("angle-label").textContent=angleText;byId("frame-name").textContent=base.angle.toUpperCase()+" / "+angleText;
  elements.slider.max=String(current.frames.length-1);elements.slider.value=String(index);
  byId("caption").textContent=exactName(current)+" · "+base.angle+". "+(configuration?configuration.label+" (pairing evidence: "+configuration.evidence+")":"As photographed.")+" Photos are recorded reference media, not live stock or price information.";
  document.querySelector(".image-pair").style.setProperty("--zoom",String(zoom));
  byId("zoom-label").textContent=Math.round(zoom*100)+"%";
  byId("prev").disabled=index===0;byId("next").disabled=index===current.frames.length-1;
}
function selectItem(id){
  current=items.find(x=>x.id===id)||items[0]||null;
  if(!current)return;
  index=0;zoom=1;configuration=null;
  elements.select.value=current.id;
  elements.config.replaceChildren(new Option("As photographed","base"));
  current.configurations.forEach(c=>elements.config.add(new Option(c.label,c.id)));
  elements.config.value="base";
  elements.compare.checked=false;
  byId("product-heading").textContent=exactName(current);
  byId("product-description").textContent="Exact model and variant represented by approved publication media.";
  byId("identity-status").textContent="Exact model reviewed · "+current.identity;
  byId("rights-status").textContent="Approved · "+current.rights;
  byId("pairing-status").textContent="Base photo · no accessory pairing claimed";
  byId("checked-status").textContent=current.checked;
  setFrame();
}
function setIndex(next){if(!current)return;index=Math.max(0,Math.min(current.frames.length-1,next));setFrame();}
elements.select.addEventListener("change",()=>selectItem(elements.select.value));
elements.config.addEventListener("change",()=>{
  configuration=current?.configurations.find(c=>c.id===elements.config.value)||null;
  byId("pairing-status").textContent=configuration?"Documented pairing · "+configuration.evidence:"Base photo · no pairing claimed";
  elements.compare.checked=false;setFrame();
});
byId("prev").addEventListener("click",()=>setIndex(index-1));
byId("next").addEventListener("click",()=>setIndex(index+1));
elements.slider.addEventListener("input",()=>setIndex(Number(elements.slider.value)));
elements.compare.addEventListener("change",setFrame);
elements.split.addEventListener("input",()=>{if(!elements.compare.checked)return;elements.image.style.clipPath="inset(0 0 0 "+elements.split.value+"%)";byId("split").style.left=elements.split.value+"%";byId("split-label").textContent=elements.split.value+"%";});
byId("zoom-in").addEventListener("click",()=>{zoom=Math.min(2.5,Math.round((zoom+.25)*100)/100);setFrame();});
byId("zoom-out").addEventListener("click",()=>{zoom=Math.max(1,Math.round((zoom-.25)*100)/100);setFrame();});
byId("zoom-reset").addEventListener("click",()=>{zoom=1;setFrame();});
byId("viewer").addEventListener("keydown",e=>{if(e.key==="ArrowRight"){e.preventDefault();setIndex(index+1);}if(e.key==="ArrowLeft"){e.preventDefault();setIndex(index-1);}});
byId("viewer").addEventListener("pointerdown",e=>{if(e.pointerType!=="mouse")startX=e.clientX;});
byId("viewer").addEventListener("pointerup",e=>{if(startX===null)return;const d=e.clientX-startX;startX=null;if(Math.abs(d)>35)setIndex(index+(d<0?1:-1));});
byId("viewer").addEventListener("pointercancel",()=>{startX=null;});
async function init(){
 try{
  const response=await fetch("assets/showroom-public.json",{credentials:"omit",cache:"no-store"});
  if(!response.ok)throw Error("No approved showroom manifest");
  const data=sanitizeShowroomManifest(await response.json());
  if(!data)throw Error("Invalid publication schema");
  items=data;
  if(!items.length)return;
  elements.empty.hidden=true;elements.app.hidden=false;
  elements.select.replaceChildren(...items.map(item=>new Option(exactName(item),item.id)));
  selectItem(items[0].id);
 }catch{
  byId("empty-heading").textContent="Approved showroom media unavailable.";
  byId("empty-copy").textContent="The public media collection could not be verified. No sample products or substitute images are being displayed. The interactive concept Studio is still available.";
 }
}
init();
