"use strict";
import {REFERENCE_PRODUCTS,DEPARTMENTS,researchTitle} from "./product-room-research.mjs";
import {firearmContext} from "./accessory-context.mjs";
import {researchPhotoFor} from "./research-photo-license.mjs";
import {SIX_VIEW_SCHEMA,ANGLES,validateSixViewManifest,getViewsForProduct,pickFirstView,
 curatedAccessorySet,researchPackage,buildResearchShareUrl} from "./six-view-contract.mjs";
/* No automatic rights approval, live AI, private supplier data, price quoting,
   image compositing, local storage, or image uploads. Browser-local previews
   exist only until the viewer closes/reloads. */
const $=id=>document.getElementById(id);
const firearms=REFERENCE_PRODUCTS.filter(p=>p.kind==="firearm");
const accessories=REFERENCE_PRODUCTS.filter(p=>p.kind==="accessory");
const angleIcons={left:"←",right:"→",top:"↑",bottom:"↓",front:"⊙",rear:"⊗"};
let selected=firearms.find(x=>x.id==="ruger-precision-308-gen1")||firearms[0];
let department=selected.department,preferredAngle="reference",activeView=null;
let approvedViews=[],localByProduct=new Map(),lastAccessory=null,zoom=1,pan={x:0,y:0},drag=null;
const chosen=new Set();
const clamp=(n,min,max)=>Math.max(min,Math.min(max,n));
const create=(tag,cls,value)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(value!==undefined)e.textContent=value;return e;};
const sort=(items)=>items.slice().sort((a,b)=>researchTitle(a).localeCompare(researchTitle(b)));
const has=(list,x)=>list.includes(x);
const localFor=(id)=>Object.fromEntries(localByProduct.get(id)||[]);
function getCurrentViews(){return getViewsForProduct(selected,approvedViews,localFor(selected.id));}
function fitPhoto(){
 if(!activeView?.photo){$("zoom-amount").textContent="100%";$("zoom-out").disabled=true;$("zoom-in").disabled=true;$("reset-image").disabled=true;$("fullscreen").disabled=true;return;}
 pan=clampPan(pan,zoom);
 $("main-photo").style.setProperty("--scale",String(zoom));
 $("main-photo").style.setProperty("--pan-x",pan.x+"px");
 $("main-photo").style.setProperty("--pan-y",pan.y+"px");
 $("zoom-amount").textContent=Math.round(zoom*100)+"%";
 $("zoom-out").disabled=zoom<=1;$("zoom-in").disabled=zoom>=4;$("reset-image").disabled=zoom===1;$("fullscreen").disabled=false;
}
function clampPan(p,z){
 const rect=$("image-space").getBoundingClientRect();
 return {x:z<=1?0:clamp(p.x,-rect.width*(z-1)*.43,rect.width*(z-1)*.43),
         y:z<=1?0:clamp(p.y,-rect.height*(z-1)*.43,rect.height*(z-1)*.43)};
}
function setZoom(next){
 if(!activeView?.photo)return;
 zoom=clamp(next,1,4);
 if(zoom===1)pan={x:0,y:0};
 fitPhoto();
}
function writeCredit(media,mode){
 const box=$("image-credit");box.replaceChildren();
 if(!media){box.textContent="No exact-item image available for this view.";return;}
 if(mode==="local-preview"){box.textContent="LOCAL-ONLY PREVIEW · Not published, verified, or stored. Use photographs of the same selected product.";return;}
 box.append(create("span","",media.credit||"Research photo · license attribution available"));
 if(media.sourcePage){
  const a=create("a",""," Original source ↗");a.href=media.sourcePage;a.target="_blank";a.rel="noopener noreferrer";box.append(a);
 }
 if(media.licenseUrl){
  const a=create("a",""," License ↗");a.href=media.licenseUrl;a.target="_blank";a.rel="noopener noreferrer";box.append(a);
 }
}
function showImage(view){
 const img=$("main-photo"),empty=$("no-photo"),error=$("image-error");
 zoom=1;pan={x:0,y:0};drag=null;
 activeView=view;
 empty.hidden=!!view?.photo;error.hidden=true;
 img.hidden=!view?.photo;
 if(view?.photo){
  img.alt=view.photo.alt||"User-selected local inspection photo";
  if(img.getAttribute("src")!==view.photo.src)img.src=view.photo.src;
 }else{img.removeAttribute("src");img.alt="";}
 $("view-label").textContent=!view?.photo?"NO APPROVED PHOTO":view.angle==="reference"?"DOCUMENTED REFERENCE":view.angle.toUpperCase()+" VIEW";
 $("mode-caption").textContent=view?.mode==="local-preview"?"Temporary local photo · never published":
 view?.mode==="approved-public"?"Approved exact-product directional view":
 view?.mode==="reference"?"Licensed research photograph · direction not asserted":"No exact-view media available";
 writeCredit(view?.photo,view?.mode);
 fitPhoto();
}
function rebuildAngles(){
 const views=getCurrentViews();
 $("coverage-number").textContent=views.count+" / 6";
 $("coverage-caption").textContent=views.count===6?"Six approved or local views ready":views.count+" documented-direction views · "+(6-views.count)+" pending";
 const active=pickFirstView(views,preferredAngle);
 preferredAngle=active.angle||"reference";
 const grid=$("angles-grid");grid.replaceChildren();
 for(const slot of views.angles){
  const btn=create("button","angle-button");btn.type="button";
  btn.dataset.angle=slot.angle;btn.disabled=!slot.available;
  btn.setAttribute("aria-pressed",String(active.angle===slot.angle));
  const icon=slot.available?create("img","angle-thumb"):create("span","",angleIcons[slot.angle]);
  if(slot.available){icon.src=slot.photo.src;icon.alt="";icon.loading="lazy";icon.referrerPolicy="no-referrer";}else icon.setAttribute("aria-hidden","true");
  btn.append(icon,create("strong","",slot.angle.charAt(0).toUpperCase()+slot.angle.slice(1)),
   create("small","",slot.mode==="local-preview"?"Local preview":slot.mode==="approved-public"?"Approved view":"Not available"));
  btn.title=slot.available?"Show actual "+slot.angle+" photograph":"No authorized exact "+slot.angle+" view yet";
  btn.addEventListener("click",()=>selectAngle(slot.angle));
  grid.append(btn);
 }
 const reference=$("reference-view");
 reference.disabled=!views.reference;
 reference.setAttribute("aria-pressed",String(active.angle==="reference"));
 reference.textContent=views.reference?"View original documented reference photo":"No additional licensed reference photo";
 showImage(active);
}
function selectAngle(angle){
 const view=getCurrentViews();
 const slot=pickFirstView(view,angle);
 if(slot.angle!==angle)return;
 preferredAngle=angle;
 rebuildAngles();
}
function moveAngle(direction){
 const views=getCurrentViews();
 const avail=["reference",...ANGLES].filter(x=>(x==="reference"&&views.reference)||(views.angles.find(a=>a.angle===x)?.available));
 if(avail.length<2)return;
 const idx=avail.indexOf(activeView?.angle);
 selectAngle(avail[(idx+direction+avail.length)%avail.length]);
}
function populateModelChoices(preferId){
 const brand=$("product-brand").value;
 const models=sort(firearms.filter(x=>x.department===department&&x.brand===brand));
 $("product-model").replaceChildren(...models.map(item=>{
  const option=new Option(item.model,item.id);
  return option;
 }));
 const pick=models.find(m=>m.id===preferId)||models[0]||null;
 if(pick){$("product-model").value=pick.id;setProduct(pick.id);}
}
function populateBrands(preferBrand,preferId){
 const brands=[...new Set(firearms.filter(x=>x.department===department).map(x=>x.brand))].sort();
 $("product-brand").replaceChildren(...brands.map(name=>new Option(name,name)));
 $("product-brand").value=brands.includes(preferBrand)?preferBrand:brands[0];
 populateModelChoices(preferId);
}
function setDepartment(next){
 if(!DEPARTMENTS.includes(next))return;
 department=next;
 document.querySelectorAll("[data-department]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.department===next)));
 const first=firearms.find(x=>x.department===next);
 populateBrands(first?.brand,first?.id);
}
function setProduct(id){
 const item=firearms.find(x=>x.id===id&&x.department===department);if(!item)return;
 const changed=selected?.id!==item.id;
 selected=item;
 if(changed){chosen.clear();lastAccessory=null;preferredAngle="reference";$("browse-all").checked=false;}
 $("headline").textContent=researchTitle(selected);
 $("model-subtitle").textContent=selected.subtitle||"Real manufacturer reference";
 $("product-description").textContent=selected.note||"See the official manufacturer source for exact specifications.";
 const link=$("manufacturer-link");link.hidden=!selected.source;
 if(selected.source)link.href=selected.source;
 rebuildAngles();renderAccessories();renderReceipt();
}
function renderAccessories(){
 const all=$("browse-all").checked;
 const context=firearmContext(selected);
 $("context-message").textContent=context.name+" · "+context.message+
  (all?" All-product browsing is research only; unrelated choices do not become recommendations.":"");
 const rows=curatedAccessorySet(selected,accessories,{includeAll:all});
 const container=$("accessory-choices");container.replaceChildren();
 if(!rows.length){container.append(create("div","no-accessories","No reviewed use-case product references yet for this exact firearm. Browse all for research, or choose another model."));}
 for(const row of rows){
  const item=row.item;
  const button=create("button","accessory-button");button.type="button";
  button.dataset.accessory=item.id;
  const added=chosen.has(item.id);
  button.setAttribute("aria-pressed",String(added));
  const icon=create("span","accessory-icon",item.accessoryType==="optics"?"◎":item.accessoryType==="lights"?"✦":item.accessoryType==="holsters"?"▱":"▣");
  icon.setAttribute("aria-hidden","true");
  const label=create("span");
  label.append(create("span","name",researchTitle(item)),
   create("small","sub",row.context.label+" · "+row.pairing.short));
  button.append(icon,label,create("span","pick",added?"Remove":"Explore +"));
  button.addEventListener("click",()=>toggleAccessory(item.id));
  container.append(button);
 }
 renderAccessoryDetail();
}
function toggleAccessory(id){
 const item=accessories.find(x=>x.id===id);if(!item)return;
 if(chosen.has(id))chosen.delete(id);else chosen.add(id);
 lastAccessory=id;
 renderAccessories();renderReceipt();
}
function renderAccessoryDetail(){
 const detail=$("accessory-detail");detail.hidden=!lastAccessory;
 if(!lastAccessory)return;
 const item=accessories.find(x=>x.id===lastAccessory);if(!item)return;
 const row=curatedAccessorySet(selected,[item],{includeAll:true})[0];
 const media=researchPhotoFor(item);
 $("accessory-name").textContent=researchTitle(item)+(chosen.has(item.id)?" · On research list":" · Removed");
 $("accessory-evidence").textContent=row.context.reason+" "+row.pairing.summary+
  " This does not establish physical installation or show it mounted on the selected firearm.";
 $("fit-label").textContent=row.pairing.short.toUpperCase();
 $("accessory-photo").hidden=!media;$("accessory-photo-missing").hidden=!!media;
 if(media){$("accessory-photo").alt=media.caption;$("accessory-photo").src=media.src;}
 else{$("accessory-photo").removeAttribute("src");$("accessory-photo").alt="";}
 $("accessory-credit").textContent=media?"Photo: "+media.author+" · "+media.license+" (separate accessory photograph)":"No licensed photograph for this exact accessory in this preview.";
 const maker=$("accessory-maker-link");
 maker.hidden=!item.source;if(item.source)maker.href=item.source;
 const evidence=$("accessory-evidence-link");
 evidence.hidden=!row.pairing.evidence.length;if(row.pairing.evidence.length)evidence.href=row.pairing.evidence[0].url;
}
function renderReceipt(){
 const box=$("package-lines");box.replaceChildren();
 const pkg=researchPackage(selected,[...chosen]);
 for(const line of pkg.lines){
  const div=create("div","receipt-row");
  const left=create("span");
  left.append(create("strong","",line.title),create("small","",line.kind==="firearm"?"Exact research model · no verified sellable SKU":line.status+" · availability unconfirmed"));
  div.append(left,create("span","","Not quoted"));box.append(div);
 }
 $("package-total").textContent="Quote pending";
 $("package-note").textContent=pkg.notice+" Accessory combinations, mounting hardware, taxes and fulfillment require review.";
 window.dispatchEvent(new CustomEvent("area33:counter-update",{detail:{productId:selected.id,selectedAccessories:[...chosen]}}));
}
function localMap(){
 if(!localByProduct.has(selected.id))localByProduct.set(selected.id,new Map());
 return localByProduct.get(selected.id);
}
function uploadLocal(){
 const file=$("local-photo").files?.[0];$("local-photo").value="";
 if(!file)return;
 if(!["image/jpeg","image/png","image/webp"].includes(file.type)||file.size>15*1024*1024||file.size<1){
  $("local-status").textContent="That file isn't a supported JPG, PNG or WebP under 15 MB.";
  return;
 }
 const angle=$("local-direction").value;
 if(!has(ANGLES,angle))return;
 const existing=localMap().get(angle);
 if(existing?.src)URL.revokeObjectURL(existing.src);
 const src=URL.createObjectURL(file);
 localMap().set(angle,{src,alt:"Local preview photo of "+researchTitle(selected)+" from "+angle+" direction",credit:"Local preview: "+file.name,view:angle});
 preferredAngle=angle;
 rebuildAngles();
 $("local-status").textContent="Showing "+angle+" view for "+researchTitle(selected)+". Local browser preview only. No upload or publication.";
}
function clearLocal(){
 const map=localByProduct.get(selected.id);
 if(map)for(const view of map.values())URL.revokeObjectURL(view.src);
 localByProduct.delete(selected.id);
 preferredAngle="reference";rebuildAngles();
 $("local-status").textContent="Local-only views cleared for this product. Nothing was published.";
}
function cleanupLocal(){
 for(const map of localByProduct.values())for(const view of map.values())URL.revokeObjectURL(view.src);
 localByProduct.clear();
}
async function copySelection(){
 const angle=activeView?.mode==="local-preview"?"reference":activeView?.angle||"reference";
 const url=buildResearchShareUrl(location.href,selected,[...chosen],angle);
 if(!url){$("copy-result").textContent="No sharable research selection is available.";return;}
 try{
  if(!navigator.clipboard?.writeText)throw Error("Clipboard unsupported");
  await navigator.clipboard.writeText(url);
  $("copy-result").textContent="Research-only link copied. Local photos do not travel with this link.";
 }catch{$("copy-result").textContent="Copy this URL (no local pictures): "+url;}
}
async function loadApproved(){
 try{
  const response=await fetch("assets/multiview-public.json",{cache:"no-store",credentials:"omit"});
  if(!response.ok)throw Error("Manifest unavailable");
  const manifest=await response.json();
  approvedViews=validateSixViewManifest(manifest,{origin:location.origin})||[];
 }catch{approvedViews=[];}
 rebuildAngles();
}
function bindEvents(){
 document.querySelectorAll("[data-department]").forEach(button=>button.addEventListener("click",()=>setDepartment(button.dataset.department)));
 $("product-brand").addEventListener("change",()=>populateModelChoices());
 $("product-model").addEventListener("change",()=>setProduct($("product-model").value));
 $("browse-all").addEventListener("change",renderAccessories);
 $("reference-view").addEventListener("click",()=>selectAngle("reference"));
 $("zoom-in").addEventListener("click",()=>setZoom(zoom+.25));
 $("zoom-out").addEventListener("click",()=>setZoom(zoom-.25));
 $("reset-image").addEventListener("click",()=>{pan={x:0,y:0};setZoom(1);});
 $("fullscreen").addEventListener("click",async()=>{
  if(!activeView?.photo)return;
  try{if(!$("view-stage").requestFullscreen)throw Error("No fullscreen");await $("view-stage").requestFullscreen();}
  catch{$("image-credit").append(create("span",""," Fullscreen is unavailable here; zoom remains available."));}
 });
 $("main-photo").addEventListener("error",()=>{
  $("main-photo").hidden=true;$("image-error").hidden=false;
 });
 $("main-photo").addEventListener("load",()=>{
  if(activeView?.photo){$("main-photo").hidden=false;$("image-error").hidden=true;}
 });
 const space=$("image-space");
 space.addEventListener("pointerdown",e=>{
  if(zoom<=1||(e.pointerType==="mouse"&&e.button!==0))return;
  drag={id:e.pointerId,x:e.clientX,y:e.clientY,pan:{...pan}};
  space.setPointerCapture?.(e.pointerId);
 });
 space.addEventListener("pointermove",e=>{
  if(!drag||drag.id!==e.pointerId)return;
  pan={x:drag.pan.x+e.clientX-drag.x,y:drag.pan.y+e.clientY-drag.y};
  fitPhoto();
 });
 for(const type of ["pointerup","pointercancel","lostpointercapture"])
  space.addEventListener(type,e=>{if(drag?.id===e.pointerId)drag=null;});
 space.addEventListener("wheel",e=>{if(!activeView?.photo)return;e.preventDefault();setZoom(zoom+(e.deltaY<0?.17:-.17));},{passive:false});
 $("view-stage").addEventListener("keydown",e=>{
  if(e.target!==$("view-stage"))return;
  if(e.key==="ArrowRight"||e.key==="ArrowLeft"){
   e.preventDefault();
   if(zoom===1)moveAngle(e.key==="ArrowRight"?1:-1);
   else {pan.x+=e.key==="ArrowRight"?35:-35;fitPhoto();}
  }
  if((e.key==="ArrowUp"||e.key==="ArrowDown")&&zoom>1){e.preventDefault();pan.y+=e.key==="ArrowUp"?-35:35;fitPhoto();}
  if(e.key==="+"||e.key==="="){e.preventDefault();setZoom(zoom+.25);}
  if(e.key==="-"){e.preventDefault();setZoom(zoom-.25);}
 });
 $("local-photo").addEventListener("change",uploadLocal);
 $("clear-local").addEventListener("click",clearLocal);
 $("clear-package").addEventListener("click",()=>{chosen.clear();lastAccessory=null;renderAccessories();renderReceipt();});
 $("copy-selection").addEventListener("click",copySelection);
 window.addEventListener("resize",fitPhoto);
 window.addEventListener("beforeunload",cleanupLocal);
}
function init(){
 bindEvents();
 const query=new URLSearchParams(location.search);
 const requested=firearms.find(x=>x.id===query.get("product"))||selected;
 department=requested.department;
 document.querySelectorAll("[data-department]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.department===department)));
 preferredAngle=query.get("view")||"reference";
 populateBrands(requested.brand,requested.id);
 const extras=query.getAll("accessory").filter(id=>accessories.some(a=>a.id===id));
 if(extras.some(id=>!curatedAccessorySet(selected,[accessories.find(a=>a.id===id)]).length))$("browse-all").checked=true;
 for(const id of extras)chosen.add(id);
 if(extras.length)lastAccessory=extras[extras.length-1];
 renderAccessories();renderReceipt();
 loadApproved();
}
init();
