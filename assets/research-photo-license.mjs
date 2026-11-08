/* Exact-photo research manifest. Each image is one named item only;
   no automatic substituting stock photos, no accessory overlay.
   Published catalog photos are reviewed via a separate approval manifest.
   License reviews: Commons file description pages, 2026-11-08. */
export const OPEN_LICENSE_MEDIA = Object.freeze([
  Object.freeze({
    productId:"ruger-precision-308-gen1",kind:"firearm",
    src:"https://upload.wikimedia.org/wikipedia/commons/b/ba/Ruger_Precision_Rifle_308_Gen_1.jpg",
    sourcePage:"https://commons.wikimedia.org/wiki/File:Ruger_Precision_Rifle_308_Gen_1.jpg",
    license:"CC BY-SA 4.0",licenseUrl:"https://creativecommons.org/licenses/by-sa/4.0/",
    author:"Coati077",
    caption:"Ruger Precision Rifle, .308 Winchester, Generation 1 (photo description)",
    view:"One original photo of a first-generation .308 rifle",
    modifications:"Unmodified source photo; viewer zoom, crop and scaling do not change the source file."
  }),
  Object.freeze({
    productId:"ruger-precision-6mm-2019-photo",kind:"firearm",
    src:"https://upload.wikimedia.org/wikipedia/commons/1/1f/Ruger_Precision_Rifle_6mm_Creedmoor.png",
    sourcePage:"https://commons.wikimedia.org/wiki/File:Ruger_Precision_Rifle_6mm_Creedmoor.png",
    license:"CC BY 3.0",licenseUrl:"https://creativecommons.org/licenses/by/3.0/",
    author:"Tactical Accountants",
    caption:"Photographed example of a Ruger Precision Rifle chambered in 6mm Creedmoor, photographed with an optic already mounted",
    view:"One real-world photograph; not a second angle of the .308 Generation 1",
    modifications:"Unmodified source photograph; browser zoom and cropping are display-only."
  }),
  Object.freeze({
    productId:"meopta-optika6-3-18x56-rd-sfp",kind:"accessory",
    src:"https://upload.wikimedia.org/wikipedia/commons/6/64/Rifle_scope.jpg",
    sourcePage:"https://commons.wikimedia.org/wiki/File:Rifle_scope.jpg",
    license:"CC BY-SA 4.0",licenseUrl:"https://creativecommons.org/licenses/by-sa/4.0/",
    author:"Microflexer",
    caption:"Meopta MeoPro Optika6 3–18×56 RD SFP rifle scope photographed separately",
    view:"One standalone product photo; does not establish mounting or fitment",
    modifications:"Unmodified source photograph; browser zoom and cropping are display-only."
  })
]);
const allow=new Map([
 ["ruger-precision-308-gen1","https://upload.wikimedia.org/wikipedia/commons/b/ba/Ruger_Precision_Rifle_308_Gen_1.jpg"],
 ["ruger-precision-6mm-2019-photo","https://upload.wikimedia.org/wikipedia/commons/1/1f/Ruger_Precision_Rifle_6mm_Creedmoor.png"],
 ["meopta-optika6-3-18x56-rd-sfp","https://upload.wikimedia.org/wikipedia/commons/6/64/Rifle_scope.jpg"]
]);
const ids=new Set();
for(const media of OPEN_LICENSE_MEDIA){
 if(ids.has(media.productId))throw Error("Duplicate research image identity");
 ids.add(media.productId);
 if(!allow.has(media.productId)||media.src!==allow.get(media.productId))throw Error("Image not on identity allowlist");
 for(const value of [media.src,media.sourcePage,media.licenseUrl]){
  const url=new URL(value);
  if(url.protocol!=="https:"||url.username||url.password||url.search||url.hash)throw Error("Invalid media URL");
 }
 if(new URL(media.src).hostname!=="upload.wikimedia.org"||
    new URL(media.sourcePage).hostname!=="commons.wikimedia.org"||
    new URL(media.licenseUrl).hostname!=="creativecommons.org")throw Error("Unknown media host");
 if(!["firearm","accessory"].includes(media.kind)||!media.author||!media.caption||!media.modifications||!media.view)throw Error("Incomplete media record");
}
export function researchPhotoFor(item){
 if(!item||item.approvedItem||!["firearm","accessory"].includes(item.kind))return null;
 return OPEN_LICENSE_MEDIA.find(media=>media.productId===item.id&&media.kind===item.kind)||null;
}
