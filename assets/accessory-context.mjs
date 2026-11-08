/* Contextual discovery rules, not live Randbeck AI, manufacturer fit approval,
   or inventory. A relevant product category is never an exact fit claim. */
export const GUIDANCE_SCHEMA="area33.accessory-context.v1";
export function firearmContext(firearm){
 if(!firearm||firearm.kind!=="firearm")return {id:"none",name:"Choose a firearm",message:"Choose a firearm to see context-aware categories."};
 if(firearm.department==="pistols")return {id:"pistol",name:"Handgun counter",message:"Explore handgun-oriented optics, lights and holsters. Mounts, rail keys and holster shells still require exact-model verification."};
 if(firearm.department==="rifles"&&(/precision/i.test(firearm.model||"")||/ruger-precision/.test(firearm.id||"")))
  return {id:"precision-rifle",name:"Precision rifle counter",message:"Start with magnified rifle scopes and precision-rifle equipment. Pistol holsters and compact pistol reflex sights are not suggested as primary accessories."};
 if(firearm.department==="rifles")return {id:"rifle",name:"Rifle counter",message:"Start with rifle-appropriate optics and equipment. Handgun holsters and pistol-specific mounting interfaces are not recommended."};
 if(firearm.department==="shotguns")return {id:"shotgun",name:"Shotgun counter",message:"Choose shotgun-specific accessories by model and intended use. There are no shotgun-specific, reviewed accessory examples in this small preview yet."};
 return {id:"unknown",name:"Needs product classification",message:"This firearm needs a reviewed classification before Area 33 recommends accessories."};
}
const result=(tier,label,reason)=>({tier,label,reason});
export function reviewAccessoryContext(firearm,accessory){
 const context=firearmContext(firearm);
 if(context.id==="none"||context.id==="unknown"||!accessory||accessory.kind!=="accessory")
  return result("review","Needs review","Choose exact product identities before evaluating a use-case match.");
 const kind=accessory.accessoryType;
 if(kind==="holsters"&&context.id!=="pistol")
  return result("not-applicable","Handgun holster — not suggested","This is a handgun holster, not a rifle or shotgun carrying case. It will not be recommended for the selected long gun.");
 if(accessory.approvedItem)
  return result("review","Published item — assess intended use","A published product listing alone does not tell us its exact mounting interface, application, or fit.");
 if(context.id==="shotgun")
  return result("review","No shotgun-specific review","This preview has no reviewed shotgun-specific accessory matching for this exact item. Browse for research only.");
 const id=accessory.id||"";
 const pistolSights=new Set(["holosun-scs-m-gr","holosun-hs507k-x2"]);
 const pistolLights=new Set(["streamlight-tlr7-x","streamlight-tlr7-x-sub"]);
 const longScope=id==="meopta-optika6-3-18x56-rd-sfp";
 if(context.id==="pistol"){
  if(longScope)return result("not-suggested","Rifle scope — not suggested","A large magnified rifle scope is not a sensible default accessory for a handgun.");
  if(kind==="holsters")return result("explore","Explore handgun holsters","Only model-specific holster shells are useful; verify the exact pistol, installed light, optic and holster SKU.");
  if(pistolSights.has(id))return result("explore","Explore handgun optics","Pistol reflex-sight category is relevant. The exact optic footprint and slide mounting still need manufacturer evidence.");
  if(pistolLights.has(id))return result("explore","Explore handgun lights","Compact pistol-light category is relevant. Confirm the exact rail, mounting key, clearance and holster combination.");
  return result("review","Use-case review needed","This product has not been classified as a reviewed handgun-oriented accessory.");
 }
 if(context.id==="precision-rifle"||context.id==="rifle"){
  if(longScope)return result("explore","Explore magnified rifle optics","A magnified rifle scope is a sensible category to explore. Rail, rings, dimensions and actual fit are not verified.");
  if(pistolSights.has(id))return result("not-suggested","Pistol optic — not the primary suggestion","This exact compact pistol reflex optic is not a default primary sight for the selected rifle. A rifle may use other red dots or secondary sights; that does not prove this item fits.");
  if(pistolLights.has(id))return result("not-suggested","Compact pistol light — not suggested","This light is marketed for compact handgun mounting; do not infer rifle fit from a rail alone.");
  return result("review","Rifle application needs review","The accessory needs rifle-specific intended-use and interface evidence.");
 }
 return result("review","Needs review","No category-level guidance exists for this exact combination.");
}
export function suggestedAccessories(firearm,items){
 if(!Array.isArray(items))return [];
 return items.filter(item=>reviewAccessoryContext(firearm,item).tier==="explore");
}
