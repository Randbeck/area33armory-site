/* Source-neutral browser+Node validator for rights-cleared exact-product public media. */
const pathPattern=/^assets\/approved\/showroom\/[a-z0-9_-]+\/[a-z0-9_-]+\.(?:webp|png|jpe?g)$/i;
const idPattern=/^[a-z0-9_-]{12,64}$/i;
export const approvedPath=(s)=>typeof s==="string"&&s.length<=180&&!s.includes("..")&&pathPattern.test(s)?s:null;
const text=(s,n=120)=>typeof s==="string"?s.trim().slice(0,n):"";
function mediaFrames(frames,itemId){
  if(!Array.isArray(frames)||frames.length<2||frames.length>48)return null;
  const arr=frames.map(f=>{
    if(!f||typeof f!=="object")return null;
    const angle=text(f.angle,50),src=approvedPath(f.src),alt=text(f.alt,200);
    if(!angle||!src||!alt||!src.startsWith("assets/approved/showroom/"+itemId+"/"))return null;
    return {angle,src,alt};
  });
  if(arr.some(v=>!v)||new Set(arr.map(f=>f.angle)).size!==arr.length)return null;
  return arr;
}
export function sanitizeShowroomItem(r){
  if(!r||typeof r!=="object"||Array.isArray(r)||r.status!=="published"||r.publication_approved!==true||r.exact_identity_verified!==true||r.rights!=="approved")return null;
  const id=text(r.id,64),manufacturer=text(r.manufacturer),model=text(r.model),variant=text(r.variant),rights=text(r.rights_source,160),identity=text(r.identity_evidence_label,160),checked=text(r.checked_at,20);
  if(!idPattern.test(id)||!manufacturer||!model||!rights||!identity||! /^\d{4}-\d\d-\d\d$/.test(checked)||!Number.isFinite(Date.parse(checked+"T00:00:00Z")))return null;
  const frames=mediaFrames(r.frames,id);
  if(!frames)return null;
  const configurations=[];
  for(const c of (Array.isArray(r.configurations)?r.configurations:[])){
    if(!c||typeof c!=="object"||c.publication_approved!==true||c.media_rights_approved!==true||c.exact_accessory_verified!==true||c.pairing_verified!==true||c.alignment_reviewed!==true)continue;
    const cid=text(c.id,64),label=text(c.label),evidence=text(c.pairing_evidence_label,160);
    const images=mediaFrames(c.frames,id);
    if(!idPattern.test(cid)||!label||!evidence||!images||images.length!==frames.length||images.some((f,i)=>f.angle!==frames[i].angle))continue;
    configurations.push({id:cid,label,evidence,frames:images});
    if(configurations.length===24)break;
  }
  return {id,manufacturer,model,variant,rights,identity,checked,frames,configurations};
}
export function sanitizeShowroomManifest(body){
  if(!body||body.schema!=="area33.showroom.v1"||!Array.isArray(body.items)||body.items.length>200)return null;
  const items=body.items.map(sanitizeShowroomItem).filter(Boolean);
  const ids=new Set();
  for(const item of items){if(ids.has(item.id))return null;ids.add(item.id);}
  return items;
}
