"use strict";
import {REFERENCE_PRODUCTS,researchTitle} from "./product-room-research.mjs";
import {evaluatePairing} from "./pairing-evidence.mjs";
import {reviewAccessoryContext} from "./accessory-context.mjs";
import {buildConceptMesh,paintConcept,clampCamera,samplePackage} from "./counter-3d-scene.mjs";
/* Interactive counter *prototype*. No backend calls, permissions to sell,
   exact CAD geometry, private catalog records, or unverified accessory claims. */
const $=id=>document.getElementById(id);
const reference=REFERENCE_PRODUCTS.find(p=>p.id==="glock-g19-gen5-mos");
if(!reference)throw Error("Missing research reference");
const sampleAccessoryIds=["holosun-scs-m-gr","streamlight-tlr7-x","aliengear-photon"];
const products=new Map(sampleAccessoryIds.map(id=>[id,REFERENCE_PRODUCTS.find(p=>p.id===id)]));
if([...products.values()].some(p=>!p))throw Error("Missing accessory references");
let camera=clampCamera({yaw:-.25,pitch:-.15,zoom:1});
let mix=0,targetMix=0,finish="graphite",spin=false,lastTime=0,lastSelected=null;
const chosen=new Set();
const reducedMotion=window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches||false;
const stage=$("model-canvas"),stageCtx=stage.getContext("2d");
let drag=null;
function resizeCanvas(canvas){
 const rect=canvas.getBoundingClientRect(),ratio=Math.min(2,window.devicePixelRatio||1);
 const w=Math.max(1,Math.round(rect.width*ratio)),h=Math.max(1,Math.round(rect.height*ratio));
 if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
 return {width:w,height:h,ratio};
}
function draw3D(){
 if(!stageCtx){$("stage-explanation").textContent="3D canvas is unavailable in this browser; the explanatory controls and package research remain available.";return;}
 const {width,height}=resizeCanvas(stage);
 const mesh=buildConceptMesh({finish,optic:chosen.has("holosun-scs-m-gr")&&
  evaluatePairing(reference,products.get("holosun-scs-m-gr")).status==="manufacturer-listed"});
 paintConcept(stageCtx,width,height,camera,mix,mesh);
}
function syncMode(){
 const finished=targetMix>.5;
 $("mode-blueprint").setAttribute("aria-pressed",String(!finished));
 $("mode-finish").setAttribute("aria-pressed",String(finished));
 $("visual-status").textContent=finished?"SHADED 3D / CONCEPT":"CAD WIREFRAME / CONCEPT";
 $("stage-explanation").textContent=finished?
  "Rotate a shaded, genuinely three-dimensional concept. Finish and any optic are illustrative, not manufacturer CAD or an approved fitted configuration.":
  "Rotate real 3D geometry in a technical wireframe. This is not a flat photograph, dimensional engineering drawing, or manufacturer CAD file.";
}
function setMode(finished,animate=true){
 targetMix=finished?1:0;if(!animate||reducedMotion)mix=targetMix;syncMode();draw3D();
}
function step(time){
 const delta=lastTime?Math.min(48,time-lastTime):16;lastTime=time;
 if(spin&&!reducedMotion)camera.yaw+=delta*.00045;
 if(Math.abs(targetMix-mix)>.001){mix+=Math.sign(targetMix-mix)*Math.min(Math.abs(targetMix-mix),delta/850); }
 else mix=targetMix;
 draw3D();
 window.requestAnimationFrame(step);
}
function showEvidence(id){
 const product=products.get(id);
 if(!product){$("evidence-status").textContent="No selected accessory";return;}
 const verdict=evaluatePairing(reference,product);
 const context=reviewAccessoryContext(reference,product);
 const state=id==="holosun-scs-m-gr"&&verdict.status==="manufacturer-listed"?
  "Manufacturer-listed · illustrative 3D optic outline":
  verdict.status==="family-guidance"?"Family guidance only · no model attached":
  "Exact fit not established · no model attached";
 $("evidence-status").textContent=state;
 $("evidence-copy").textContent=context.reason+" "+verdict.summary+" "+verdict.caution+
  (id==="holosun-scs-m-gr"?" The small 3D shape is an original conceptual outline, NOT a measured Holosun model or verified physical installation.":" No exact accessory geometry is shown attached.");
 const source=$("evidence-source");
 source.hidden=!verdict.evidence.length;source.href=verdict.evidence[0]?.url||product.source;
 source.textContent=verdict.evidence.length?"Read official fitment evidence ↗":"Official product information ↗";
}
function refreshReceipt(){
 const data=samplePackage([...chosen]);
 const lines=$("receipt-lines");
 lines.replaceChildren();
 const fmt=amount=>"$"+amount.toLocaleString("en-US",{maximumFractionDigits:0});
 for(const row of data.lines){
  const item=document.createElement("div");item.className="receipt-row";
  const label=document.createElement("span");
  const title=document.createElement("strong");
  title.textContent=row.id==="base"?"Sample pistol configuration":products.get(row.id)?.brand+" "+products.get(row.id)?.model;
  const description=document.createElement("small");description.textContent=row.name;
  label.append(title,description);
  const amount=document.createElement("b");amount.textContent=fmt(row.amount);
  item.append(label,amount);lines.append(item);
 }
 $("total").textContent=fmt(data.total);
 document.querySelectorAll("[data-accessory]").forEach(button=>{
  const on=chosen.has(button.dataset.accessory);
  button.setAttribute("aria-pressed",String(on));
  button.querySelector(".pick").textContent=on?"Remove":"Add";
 });
}
function toggleAccessory(id){
 if(!products.has(id))return;
 if(chosen.has(id))chosen.delete(id);
 else chosen.add(id);
 lastSelected=id;
 showEvidence(id);
 refreshReceipt();
 draw3D();
}
function setFinish(name){
 if(!["graphite","sand","slate"].includes(name))return;
 finish=name;
 document.querySelectorAll("[data-finish]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.finish===name)));
 draw3D();
}
function setCamera(c){camera=clampCamera({...camera,...c});draw3D();$("zoom-status").textContent=Math.round(camera.zoom*100)+"%";}
function wireEvents(){
 $("mode-blueprint").addEventListener("click",()=>setMode(false));
 $("mode-finish").addEventListener("click",()=>setMode(true));
 $("mode-transition").addEventListener("click",()=>{mix=0;setMode(true,true);});
 $("spin-toggle").addEventListener("click",()=>{
  spin=!spin;$("spin-toggle").setAttribute("aria-pressed",String(spin));$("spin-toggle").textContent="Auto-rotate: "+(spin?"On":"Off");
 });
 $("view-left").addEventListener("click",()=>setCamera({yaw:0,pitch:0}));
 $("view-right").addEventListener("click",()=>setCamera({yaw:Math.PI,pitch:0}));
 $("view-top").addEventListener("click",()=>setCamera({pitch:1.30,yaw:-.38}));
 $("view-reset").addEventListener("click",()=>setCamera({pitch:-.15,yaw:-.25,zoom:1}));
 $("zoom-minus").addEventListener("click",()=>setCamera({zoom:camera.zoom-.15}));
 $("zoom-plus").addEventListener("click",()=>setCamera({zoom:camera.zoom+.15}));
 stage.addEventListener("pointerdown",e=>{
  if(e.pointerType==="mouse"&&e.button!==0)return;
  drag={id:e.pointerId,x:e.clientX,y:e.clientY,yaw:camera.yaw,pitch:camera.pitch};
  stage.setPointerCapture?.(e.pointerId);
 });
 stage.addEventListener("pointermove",e=>{
  if(!drag||drag.id!==e.pointerId)return;
  const rect=stage.getBoundingClientRect();
  setCamera({yaw:drag.yaw+(e.clientX-drag.x)*Math.PI/Math.max(260,rect.width),
    pitch:drag.pitch+(e.clientY-drag.y)*Math.PI/Math.max(260,rect.height)});
 });
 for(const type of ["pointerup","pointercancel","lostpointercapture"]){stage.addEventListener(type,e=>{if(drag?.id===e.pointerId)drag=null;});}
 stage.addEventListener("wheel",e=>{e.preventDefault();setCamera({zoom:camera.zoom+(e.deltaY<0?.09:-.09)});},{passive:false});
 stage.addEventListener("keydown",e=>{
  const direction={ArrowLeft:[-.16,0],ArrowRight:[.16,0],ArrowUp:[0,-.13],ArrowDown:[0,.13]}[e.key];
  if(direction){e.preventDefault();setCamera({yaw:camera.yaw+direction[0],pitch:camera.pitch+direction[1]});}
  if(e.key==="+"||e.key==="=")setCamera({zoom:camera.zoom+.1});
  if(e.key==="-")setCamera({zoom:camera.zoom-.1});
 });
 document.querySelectorAll("[data-finish]").forEach(b=>b.addEventListener("click",()=>setFinish(b.dataset.finish)));
 document.querySelectorAll("[data-accessory]").forEach(b=>b.addEventListener("click",()=>toggleAccessory(b.dataset.accessory)));
 $("reset-selection").addEventListener("click",()=>{chosen.clear();lastSelected=null;refreshReceipt();draw3D();
  $("evidence-status").textContent="All accessory selections cleared";
  $("evidence-copy").textContent="A product category or reference never establishes exact fit. Select an item to see documented evidence.";
  $("evidence-source").hidden=true;
 });
 $("copy-summary").addEventListener("click",async()=>{
  const data=samplePackage([...chosen]);
  const text=[
   "AREA 33 — NON-BINDING INTERACTIVE COUNTER DEMO",
   "Reference: "+researchTitle(reference)+" (3D model is illustrative, not exact CAD)",
   ...data.lines.map(row=>row.name+": $"+row.amount),
   "Illustrative subtotal: $"+data.total,
   "No verified exact configuration, inventory, quote, live pricing or offer."
  ].join("\n");
  try{
   if(!navigator.clipboard?.writeText)throw Error("Clipboard unavailable");
   await navigator.clipboard.writeText(text);$("copy-status").textContent="Demonstration summary copied (not an order or quote).";
  }catch{$("copy-status").textContent="Clipboard unavailable; summary is visible on this page.";}
 });
 window.addEventListener("resize",draw3D);
}
wireEvents();
refreshReceipt();
syncMode();draw3D();
window.requestAnimationFrame(step);
