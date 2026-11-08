/* Rights-checked editorial inspiration ONLY, never a product image, fit proof,
   promotional offer, or accessory-specific photo. */
export const INSPIRATION_MEDIA=Object.freeze([
  Object.freeze({
    id:"real-world-customization-example",
    src:"https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b6/Handgun_with_Red_Dot_-_S%26W_M%26P_2.0_Trijicon_and_Streamlight.jpg/960px-Handgun_with_Red_Dot_-_S%26W_M%26P_2.0_Trijicon_and_Streamlight.jpg",
    source:"https://commons.wikimedia.org/wiki/File:Handgun_with_Red_Dot_-_S%26W_M%26P_2.0_Trijicon_and_Streamlight.jpg",
    license:"CC BY 2.0",
    licenseUrl:"https://creativecommons.org/licenses/by/2.0/",
    creator:"Tony Webster",
    alt:"Real-world photograph showing a Smith & Wesson M&P 2.0 10mm with an attached red-dot sight and weapon light, photographed by Tony Webster.",
    caption:"An existing photographed configuration of an M&P 2.0 10mm with optic and light. This is not the product you selected and is not an accessory fitment demonstration.",
    modifications:"Image shown unmodified; changing display size does not modify the original image."
  })
]);
const ALLOWED_IMAGES=new Set([INSPIRATION_MEDIA[0].src]);
export function verifyInspiration(item){
 if(!item||!ALLOWED_IMAGES.has(item.src)||item.license!=="CC BY 2.0"||item.creator!=="Tony Webster")return false;
 const img=new URL(item.src),source=new URL(item.source),license=new URL(item.licenseUrl);
 return img.protocol==="https:"&&img.hostname==="thumb.wikimedia.org"&&
  source.protocol==="https:"&&source.hostname==="commons.wikimedia.org"&&
  license.protocol==="https:"&&license.hostname==="creativecommons.org"&&
  !img.search&&!img.hash&&!img.username&&!img.password&&
  !!item.alt&&!!item.caption&&!!item.modifications;
}
for(const m of INSPIRATION_MEDIA)if(!verifyInspiration(m))throw Error("Invalid or unlicensed inspiration");
export function inspirationForEditorial(id){
 return INSPIRATION_MEDIA.find(x=>x.id===id&&verifyInspiration(x))||null;
}
