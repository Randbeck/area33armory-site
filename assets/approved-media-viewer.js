// Approved media only: no example records or external customer-facing feed.
const manifestURL = "assets/approved-media-manifest.json";
const el = id => document.getElementById(id);
let items = [], selected = null, frameIndex = 0, startX = null;
const text = value => typeof value === "string" ? value.trim().slice(0,240) : "";
function approvedURL(value) {
  if (typeof value !== "string" || !value.startsWith("assets/approved/") || value.includes("..") || value.includes("?") || value.includes("#")) return null;
  const url = new URL(value, document.baseURI);
  if (url.origin !== location.origin || !/\.(webp|png|jpe?g)$/i.test(url.pathname)) return null;
  return url.href;
}
function date(value){if(typeof value!=="string" || !/^\d{4}-\d\d-\d\d$/.test(value))return null;const d=new Date(value+"T00:00:00Z");return Number.isNaN(d.getTime())?null:value;}
function approvedItem(raw){
  if(!raw||typeof raw!=="object"||raw.status!=="published"||raw.rights!=="approved"||raw.exact_identity_verified!==true||raw.publication_approved!==true)return null;
  const id=text(raw.id),manufacturer=text(raw.manufacturer),model=text(raw.model),variant=text(raw.variant),identity=text(raw.identity_evidence),rightsSource=text(raw.rights_source),updated=date(raw.checked_at);
  if(!id||!manufacturer||!model||!identity||!rightsSource||!updated||!Array.isArray(raw.frames)||raw.frames.length<2||raw.frames.length>72)return null;
  const frames=raw.frames.map(f=>f&&typeof f==="object"&&approvedURL(f.path)&&text(f.alt)?{url:approvedURL(f.path),alt:text(f.alt)}:null);
  if(frames.some(f=>!f))return null;
  const hotspots=Array.isArray(raw.hotspots)?raw.hotspots.slice(0,12).filter(h=>h&&Number.isFinite(h.x)&&Number.isFinite(h.y)&&h.x>=0&&h.x<=100&&h.y>=0&&h.y<=100&&text(h.label)&&text(h.note)&&text(h.evidence_label)).map(h=>({x:h.x,y:h.y,label:text(h.label),note:text(h.note),source:text(h.evidence_label)})):[];
  return {id,manufacturer,model,variant,identity,rightsSource,updated,frames,hotspots};
}
function resetViewer(note){
  selected=null;frameIndex=0;el("media-image").hidden=true;el("media-image").removeAttribute("src");el("media-empty").hidden=false;el("media-product-title").textContent="No product selected";el("media-explanation").textContent=note;el("media-annotation").textContent="Feature notes will appear here only when linked to approved product evidence.";el("media-hotspot-layer").replaceChildren();refreshControls();
}
function refreshControls(){
  const ready=!!selected;
  el("media-prev").disabled=!ready;el("media-next").disabled=!ready;el("media-scrub").disabled=!ready;
  el("media-scrub").max=ready?String(selected.frames.length-1):"0";el("media-scrub").value=String(frameIndex);
  el("media-frame").textContent=ready?(frameIndex+1)+" / "+selected.frames.length:"— / —";
}
function showFrame(next){
  if(!selected)return;
  frameIndex=(next+selected.frames.length)%selected.frames.length;
  const frame=selected.frames[frameIndex], image=el("media-image");
  image.hidden=false;image.src=frame.url;image.alt=frame.alt;
  el("media-empty").hidden=true;refreshControls();
}
function choose(id){
  selected=items.find(item=>item.id===id)||null;
  if(!selected){resetViewer("No approved product media selected.");return;}
  frameIndex=0;
  el("media-product-title").textContent=[selected.manufacturer,selected.model,selected.variant].filter(Boolean).join(" ");
  el("media-explanation").textContent="Identity reviewed: "+selected.identity+" · Rights: "+selected.rightsSource+" · Checked: "+selected.updated+". Images do not establish accessory compatibility.";
  const layer=el("media-hotspot-layer");layer.replaceChildren();
  for(const h of selected.hotspots){
    const b=document.createElement("button");b.type="button";b.textContent="+";b.style.left=h.x+"%";b.style.top=h.y+"%";b.setAttribute("aria-label","Learn about "+h.label);
    b.addEventListener("click",()=>{el("media-annotation").textContent=h.label+": "+h.note+" (Source: "+h.source+")";});
    layer.append(b);
  }
  showFrame(0);
}
el("media-prev").addEventListener("click",()=>showFrame(frameIndex-1));
el("media-next").addEventListener("click",()=>showFrame(frameIndex+1));
el("media-scrub").addEventListener("input",e=>showFrame(Number(e.target.value)));
el("media-item").addEventListener("change",e=>choose(e.target.value));
el("media-viewer").addEventListener("keydown",e=>{if(!selected)return;if(e.key==="ArrowRight"||e.key==="ArrowLeft"){e.preventDefault();showFrame(frameIndex+(e.key==="ArrowRight"?1:-1));}});
el("media-viewer").addEventListener("pointerdown",e=>{if(!selected||e.target.closest("button"))return;startX=e.clientX;});
el("media-viewer").addEventListener("pointerup",e=>{if(!selected||startX===null)return;const delta=e.clientX-startX;startX=null;if(Math.abs(delta)>25)showFrame(frameIndex+(delta<0?1:-1));});
el("media-viewer").addEventListener("pointercancel",()=>{startX=null;});
el("media-image").addEventListener("error",()=>{resetViewer("Approved image could not be loaded. Media is temporarily unavailable; no substitute image is shown.");el("media-status").textContent="Media error";});
async function load(){
 try{
  const response=await fetch(manifestURL,{credentials:"omit",cache:"no-store"});if(!response.ok)throw Error("manifest unavailable");
  const data=await response.json();if(!data||!Array.isArray(data.products))throw Error("invalid manifest");
  items=data.products.map(approvedItem).filter(Boolean);
  const select=el("media-item");select.replaceChildren(new Option("Choose approved product media",""));
  for(const item of items)select.add(new Option([item.manufacturer,item.model,item.variant].filter(Boolean).join(" "),item.id));
  el("media-status").textContent=items.length?items.length+" approved media set(s)":"No approved product media published";
  resetViewer(items.length?"Choose an approved media set to explore its views.":"No approved product media is published yet. The viewer is ready for reviewed assets.");
 }catch{el("media-status").textContent="Media unavailable";resetViewer("The approved media manifest could not be loaded. No fictional product images will be shown.");}
}
load();
