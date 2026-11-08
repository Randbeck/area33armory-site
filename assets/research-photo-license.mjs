/* Explicitly scoped third-party research photography with a verified open license.
   This is NOT an owner-approved catalog listing or an accessory pairing.
   No generic model matching; one image belongs only to one exact research reference.
   Attribution: Coati077, Wikimedia Commons, CC BY-SA 4.0. Unmodified photograph. */
export const OPEN_LICENSE_MEDIA = Object.freeze([
  Object.freeze({
    productId:"ruger-precision-308-gen1",
    src:"https://upload.wikimedia.org/wikipedia/commons/b/ba/Ruger_Precision_Rifle_308_Gen_1.jpg",
    sourcePage:"https://commons.wikimedia.org/wiki/File:Ruger_Precision_Rifle_308_Gen_1.jpg",
    license:"CC BY-SA 4.0",
    licenseUrl:"https://creativecommons.org/licenses/by-sa/4.0/",
    author:"Coati077",
    caption:"Ruger Precision Rifle, .308 Winchester, Generation 1 (photo description)",
    view:"Single left-side reference photograph",
    modifications:"Photo unmodified; interactive zoom/pan is a viewer-only effect.",
  })
]);
const allowed=new Set([
 "https://upload.wikimedia.org/wikipedia/commons/b/ba/Ruger_Precision_Rifle_308_Gen_1.jpg"
]);
const ids=new Set();
for(const media of OPEN_LICENSE_MEDIA){
 if(ids.has(media.productId))throw Error("Duplicate photo identity");ids.add(media.productId);
 const url=new URL(media.src);
 if(url.protocol!=="https:"||url.username||url.password||url.search||url.hash||!allowed.has(media.src))throw Error("Unallowlisted research photo");
 for(const u of [media.sourcePage,media.licenseUrl])if(new URL(u).protocol!=="https:")throw Error("Insecure attribution URL");
 if(!media.author||!media.license||!media.modifications||!media.caption)throw Error("Incomplete credit metadata");
}
export function researchPhotoFor(item){
 if(!item||item.kind!=="firearm"||item.approvedItem)return null;
 return OPEN_LICENSE_MEDIA.find(media=>media.productId===item.id)||null;
}
