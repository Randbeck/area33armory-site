/* Area 33 six-direction *photo* inspection contract.
   Missing angles are unavailable, never inferred, mirrored, AI-generated, or
   substituted from another item/variant. Browser-local previews are not public
   media approvals and must never be persisted or advertised. */
import {REFERENCE_PRODUCTS} from "./product-room-research.mjs";
import {researchPhotoFor} from "./research-photo-license.mjs";
import {evaluatePairing} from "./pairing-evidence.mjs";
import {reviewAccessoryContext} from "./accessory-context.mjs";
export const SIX_VIEW_SCHEMA="area33.six-view.public.v1";
export const ANGLES=Object.freeze(["left","right","top","bottom","front","rear"]);
const ANGLE_SET=new Set(ANGLES);
const RESEARCH_IDS=new Set(REFERENCE_PRODUCTS.filter(x=>x.kind==="firearm").map(x=>x.id));
const ID_RX=/^[a-z0-9-]{5,65}$/;
const IMG_RX=/^assets\/approved\/multiview\/([a-z0-9-]{5,65})\/(left|right|top|bottom|front|rear)\.(jpg|jpeg|png|webp)$/;
const allowedKeys=new Set(["productId","angle","src","alt","rights","verifiedExactItem","reviewedAt","sourcePage","credit"]);
const exactly=(o,keys)=>o&&typeof o==="object"&&!Array.isArray(o)&&Object.keys(o).every(k=>keys.has(k));
const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
const date=s=>typeof s==="string"&&/^\d{4}-\d\d-\d\d$/.test(s)&&!Number.isNaN(Date.parse(s+"T00:00:00Z"));
const SOURCE_HOSTS=new Set(["commons.wikimedia.org","area33armory.com","www.area33armory.com",...REFERENCE_PRODUCTS.map(item=>new URL(item.source).hostname)]);
const urlHost=src=>{try{const u=new URL(src);return u.protocol==="https:"&&!u.username&&!u.password&&!u.hash&&SOURCE_HOSTS.has(u.hostname);}catch{return false;}};
export function validateSixViewManifest(manifest,{origin="https://area33armory.com"}={}){
 if(!exactly(manifest,new Set(["schema","views"]))||manifest.schema!==SIX_VIEW_SCHEMA||!Array.isArray(manifest.views)||manifest.views.length>600)return null;
 let base;try{base=new URL(origin);}catch{return null;}
 if(!["http:","https:"].includes(base.protocol))return null;
 const seen=new Set(),views=[];
 for(const raw of manifest.views){
  if(!exactly(raw,allowedKeys)||Object.keys(raw).length!==9||!own(raw,"productId")||!own(raw,"src")||!own(raw,"angle")||!own(raw,"alt")||!own(raw,"credit")||!own(raw,"sourcePage")||!own(raw,"rights")||!own(raw,"verifiedExactItem")||!own(raw,"reviewedAt"))return null;
  const {productId,angle,src,alt,credit,sourcePage,reviewedAt,rights,verifiedExactItem}=raw;
  if(!ID_RX.test(productId)||!RESEARCH_IDS.has(productId)||!ANGLE_SET.has(angle)||rights!=="approved"||verifiedExactItem!==true||!date(reviewedAt)||!urlHost(sourcePage))return null;
  if(typeof src!=="string"||!IMG_RX.test(src)||src.match(IMG_RX)[1]!==productId||src.match(IMG_RX)[2]!==angle)return null;
  if(typeof alt!=="string"||!alt.trim()||alt.length>180||typeof credit!=="string"||!credit.trim()||credit.length>180)return null;
  const key=productId+"|"+angle;if(seen.has(key))return null;seen.add(key);
  const u=new URL(src,base);
  if(u.origin!==base.origin||u.username||u.password||u.search||u.hash)return null;
  views.push(Object.freeze({productId,angle,src:u.href,alt:alt.trim(),credit:credit.trim(),sourcePage,reviewedAt,rights:"approved",published:true}));
 }
 return Object.freeze(views);
}
export function getViewsForProduct(product,approvedViews=[],localViews={}){
 if(!product||product.kind!=="firearm")return {reference:null,angles:[],count:0};
 const reference=researchPhotoFor(product);
 const angles=ANGLES.map(angle=>{
  const pub=approvedViews.find(v=>v.productId===product.id&&v.angle===angle);
  const local=localViews?.[angle]||null;
  const view=local||pub||null;
  return {angle,available:!!view,photo:view,mode:local?"local-preview":pub?"approved-public":"pending"};
 });
 return {reference:reference?{
   src:reference.src,alt:reference.caption,credit:"Photo: "+reference.author+" · "+reference.license,
   sourcePage:reference.sourcePage,licenseUrl:reference.licenseUrl,view:"reference",published:true
 }:null,angles,count:angles.filter(x=>x.available).length};
}
export function pickFirstView(views,preference){
 if(preference==="reference"&&views.reference)return {angle:"reference",photo:views.reference,mode:"reference"};
 if(ANGLES.includes(preference)){
  const requested=views.angles.find(x=>x.angle===preference&&x.available);
  if(requested)return {angle:preference,photo:requested.photo,mode:requested.mode};
 }
 const first=views.angles.find(x=>x.available);
 return first?{angle:first.angle,photo:first.photo,mode:first.mode}:
 views.reference?{angle:"reference",photo:views.reference,mode:"reference"}:
 {angle:null,photo:null,mode:"empty"};
}
export function curatedAccessorySet(firearm,accessories,{includeAll=false}={}){
 if(!firearm||!Array.isArray(accessories))return [];
 return accessories.filter(item=>item.kind==="accessory")
  .map(item=>({item,context:reviewAccessoryContext(firearm,item),pairing:evaluatePairing(firearm,item)}))
  .filter(row=>includeAll||row.context.tier==="explore");
}
export function researchPackage(firearm,accessoryIds=[]){
 const accessories=REFERENCE_PRODUCTS.filter(x=>x.kind==="accessory");
 const seen=new Set(),lines=[];
 if(firearm&&firearm.kind==="firearm")lines.push({id:firearm.id,title:firearm.brand+" "+firearm.model,kind:"firearm",price:null,status:"Source quote required"});
 for(const id of accessoryIds){
  if(seen.has(id))continue;seen.add(id);
  const item=accessories.find(x=>x.id===id);if(!item||!firearm)continue;
  const pairing=evaluatePairing(firearm,item);
  lines.push({id,title:item.brand+" "+item.model,kind:"accessory",price:null,status:pairing.short,context:reviewAccessoryContext(firearm,item).tier});
 }
 return {lines,total:null,quoteReady:false,notice:"No customer quote is connected. Current availability, landed costs, taxes and applicable charges have not been verified."};
}
export function buildResearchShareUrl(baseUrl,firearm,accessoryIds=[],angle="reference"){
 if(!firearm||!RESEARCH_IDS.has(firearm.id))return null;
 let url;try{url=new URL(baseUrl);}catch{return null;}
 if(!["https:","http:"].includes(url.protocol)||url.username||url.password)return null;
 url.hash="";url.search="";url.searchParams.set("product",firearm.id);
 const seen=new Set();for(const id of accessoryIds){
  if(REFERENCE_PRODUCTS.some(x=>x.kind==="accessory"&&x.id===id)&&!seen.has(id)){seen.add(id);url.searchParams.append("accessory",id);}
 }
 if(ANGLES.includes(angle)||angle==="reference")url.searchParams.set("view",angle);
 return url.toString();
}
