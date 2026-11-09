/* Public-only opportunities publication gate.
 * A Randbeck internal opportunity is a PRIVATE recommendation, not public
 * advertising approval. This accepts explicitly reviewed editorial copy for
 * existing public research IDs; never exports supplier economics or prices. */
import {REFERENCE_PRODUCTS} from "./product-room-research.mjs";
export const FEATURED_SCHEMA="area33.featured.public.v1";
const PUBLIC_IDS=new Set(REFERENCE_PRODUCTS.filter(x=>x.kind==="firearm").map(x=>x.id));
const EXACT_KEYS=new Set(["publicId","productId","headline","description","label","ownerApproved","productIdentityReviewed","publicationRightsReviewed","reviewedAt","expiresAt"]);
const BANNED=/\b(dealer[_ -]?cost|buy[_ -]?cost|landed[_ -]?cost|gross[_ -]?margin|supplier[_ -]?token|internal[_ -]?opportunity|wholesale|profit[_ -]?margin)\b/i;
const DATE=s=>typeof s==="string"&&Number.isFinite(Date.parse(s))&&/^[0-9]{4}-[0-9]{2}-[0-9]{2}T/.test(s);
export function validateFeaturedPublic(raw,{now=Date.now()}={}){
 if(!raw||typeof raw!=="object"||Array.isArray(raw)||raw.schema!==FEATURED_SCHEMA||
  !Array.isArray(raw.items)||raw.items.length>8||Object.keys(raw).some(k=>!["schema","items"].includes(k)))return null;
 const seen=new Set(),items=[];
 for(const f of raw.items){
  if(!f||typeof f!=="object"||Array.isArray(f)||Object.keys(f).length!==EXACT_KEYS.size||
   Object.keys(f).some(k=>!EXACT_KEYS.has(k))||
   f.ownerApproved!==true||f.productIdentityReviewed!==true||f.publicationRightsReviewed!==true||
   typeof f.publicId!=="string"||!/^feature-[a-z0-9-]{4,60}$/.test(f.publicId)||seen.has(f.publicId)||
   typeof f.productId!=="string"||!PUBLIC_IDS.has(f.productId)||
   typeof f.headline!=="string"||f.headline.trim().length<5||f.headline.length>120||
   typeof f.description!=="string"||f.description.trim().length<8||f.description.length>260||
   typeof f.label!=="string"||!["Featured discovery","Area 33 spotlight","Opportunity highlight"].includes(f.label)||
   !DATE(f.reviewedAt)||!DATE(f.expiresAt)||Date.parse(f.expiresAt)<=now||Date.parse(f.reviewedAt)>now||
   Date.parse(f.expiresAt)<=Date.parse(f.reviewedAt)||BANNED.test(f.headline+" "+f.description))return null;
  seen.add(f.publicId);
  items.push(Object.freeze({publicId:f.publicId,productId:f.productId,headline:f.headline.trim(),
    description:f.description.trim(),label:f.label,expiresAt:f.expiresAt,published:true}));
 }
 return Object.freeze(items);
}
export const EDITORIAL_RESEARCH_HIGHLIGHTS=Object.freeze([
 Object.freeze({productId:"ruger-precision-308-gen1",headline:"Explore the Ruger Precision Rifle",description:"A real, licensed photo reference. See the details, known related models, and scope research.",label:"Research discovery",published:false}),
 Object.freeze({productId:"glock-g19-gen5-mos",headline:"Take a closer look at factory MOS",description:"Explore the G19 Gen5 MOS reference and learn how factory mounting interfaces differ from other variants.",label:"Research discovery",published:false}),
 Object.freeze({productId:"ruger-precision-6mm-2019-photo",headline:"Another Ruger Precision example",description:"A separately photographed rifle example—not an alternate view of the .308 model.",label:"Research discovery",published:false}),
]);
export function visibleFeatured(publicItems=[],{allowEditorialFallback=true}={}){
 const verified=Array.isArray(publicItems)?publicItems.filter(x=>x?.published===true):[];
 return verified.length?verified:allowEditorialFallback?EDITORIAL_RESEARCH_HIGHLIGHTS:[];
}
