/* Only owner-approved, public, sourceable deal highlights go on the homepage.
 * No raw Randbeck opportunities, private dealer prices, personal data, or
 * unverifiable discount claims. Public amounts require a destination quote. */
import {REFERENCE_PRODUCTS} from "./product-room-research.mjs";
export const DEALS_SCHEMA="area33.deals.public.v1";
const IDS=new Set(REFERENCE_PRODUCTS.filter(x=>x.kind==="firearm").map(x=>x.id));
const FIELDS=["publicId","productId","headline","description","label","offerTerms",
  "ownerApproved","exactProductReviewed","mediaRightsReviewed","publicOfferReviewed",
  "inventoryVerified","termsVerified","reviewedAt","expiresAt"];
const KEYS=new Set(FIELDS);
const BLOCKED=/\b(dealer[_ -]?cost|buy[_ -]?cost|landed[_ -]?cost|gross[_ -]?margin|supplier[_ -]?token|internal[_ -]?opportunity|wholesale|profit[_ -]?margin|private[_ -]?source)\b/i;
const validDate=s=>typeof s==="string"&&/^\d{4}-\d\d-\d\dT/.test(s)&&Number.isFinite(Date.parse(s));
const clean=s=>typeof s==="string"&&s.trim().length>0;
export function validatePublicDeals(manifest,{now=Date.now()}={}){
 if(!manifest||typeof manifest!=="object"||Array.isArray(manifest)||
    manifest.schema!==DEALS_SCHEMA||Object.keys(manifest).some(k=>!["schema","items"].includes(k))||
    !Array.isArray(manifest.items)||manifest.items.length>8)return null;
 const seen=new Set(),results=[];
 for(const x of manifest.items){
  if(!x||typeof x!=="object"||Array.isArray(x)||Object.keys(x).length!==KEYS.size||
     Object.keys(x).some(k=>!KEYS.has(k))||
     !clean(x.publicId)||!/^deal-[a-z0-9-]{4,65}$/.test(x.publicId)||
     seen.has(x.publicId)||!IDS.has(x.productId)||
     !clean(x.headline)||x.headline.length>110||
     !clean(x.description)||x.description.length>250||
     !["Area 33 Special","Featured Sale","Verified Offer"].includes(x.label)||
     !clean(x.offerTerms)||x.offerTerms.length>240||
     BLOCKED.test([x.headline,x.description,x.offerTerms].join(" "))||
     !["ownerApproved","exactProductReviewed","mediaRightsReviewed","publicOfferReviewed",
       "inventoryVerified","termsVerified"].every(k=>x[k]===true)||
     !validDate(x.reviewedAt)||!validDate(x.expiresAt)||
     Date.parse(x.reviewedAt)>now||Date.parse(x.expiresAt)<=now||
     Date.parse(x.expiresAt)<=Date.parse(x.reviewedAt))return null;
  seen.add(x.publicId);
  results.push(Object.freeze({productId:x.productId,publicId:x.publicId,
   headline:x.headline.trim(),description:x.description.trim(),
   label:x.label,offerTerms:x.offerTerms.trim(),expiresAt:x.expiresAt,
   approved:true}));
 }
 return Object.freeze(results);
}
