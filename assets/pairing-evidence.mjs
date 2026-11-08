/* Area 33 pairing evidence v1.
   Manufacturer compatibility claims != owner-verified physical fitting,
   installation instructions, rendering rights, stock or prices.
   Fail closed: never infer compatibility for similarly named variants,
   approved catalog items or unspecified accessory/SKU variants. */
export const PAIRING_SCHEMA="area33.pair-evidence.research.v1";
export const PAIRING_REVIEWED="2026-11-08";
const SOURCES=Object.freeze({
 glockMOS:"https://us.glock.com/en/press-release/news-page/take-aim-with-glocks-new-modular-optic-ready-pistols",
 glockOptics:"https://us.glock.com/en/about/technology/optic-mounting",
 glockSlim:"https://us.glock.com/en/press-release/news-page/glock-introduces-optic-ready-slimline-models-g43x-and-g48",
 holosunSCS:"https://www.holosun.com/products/scs-m-gr",
 streamlightFit:"https://www.streamlight.com/docs/default-source/compatibility-list/tlr-7ortlr-8_compatibilitylist.pdf?sfvrsn=5b23b8f0_37",
});
const EVIDENCE=Object.freeze([
 Object.freeze({
  firearmId:"glock-g19-gen5-mos",accessoryId:"holosun-scs-m-gr",
  status:"manufacturer-listed",
  short:"Manufacturer-listed direct mount",
  summary:"Holosun explicitly lists the G19 Gen5 MOS under direct-mount fitment for the SCS-M-GR.",
  why:"GLOCK identifies the G19 Gen5 MOS as the factory MOS model. Holosun lists that exact model for this exact optic, without an adapter plate.",
  caution:"Manufacturer's listed fit is not independent physical inspection. Confirm the exact pistol slide and accessory SKU, current documentation and qualified installation. Nothing here confirms other optics, modified slides, inventory or price.",
  evidence:[
   {label:"Holosun SCS-M-GR direct-mount model list",url:SOURCES.holosunSCS,checkedAt:PAIRING_REVIEWED},
   {label:"GLOCK G19 Gen5 MOS model announcement",url:SOURCES.glockMOS,checkedAt:PAIRING_REVIEWED}
  ]
 }),
 Object.freeze({
  firearmId:"glock-g19-gen5",accessoryId:"holosun-scs-m-gr",
  status:"factory-interface-differs",
  short:"Not a factory direct-MOS pairing",
  summary:"The standard G19 Gen5 and the G19 Gen5 MOS are different slide configurations.",
  why:"Holosun lists the G19 Gen5 MOS, not the unmodified standard G19 Gen5, for direct slide mounting. This is an interface distinction, not a claim that no aftermarket solution could ever exist.",
  caution:"Do not assume a model sharing the G19 name has a factory MOS mounting cut. Any aftermarket modification or alternative solution requires separate manufacturer and professional evaluation.",
  evidence:[
   {label:"GLOCK documents the separate G19 Gen5 MOS configuration",url:SOURCES.glockMOS,checkedAt:PAIRING_REVIEWED},
   {label:"Holosun direct-mount fitment list",url:SOURCES.holosunSCS,checkedAt:PAIRING_REVIEWED}
  ]
 }),
 Object.freeze({
  firearmId:"glock-g43x-mos",accessoryId:"holosun-scs-m-gr",
  status:"factory-interface-differs",
  short:"Slimline MOS uses a different interface",
  summary:"The G43X MOS has a Slimline MOS optic interface; this SCS model is marketed for full-size GLOCK MOS slides.",
  why:"GLOCK distinguishes slimline MOS cuts from standard full-size MOS. Holosun's SCS-M-GR exact model list does not include the G43X MOS.",
  caution:"A shared MOS label does not prove fit. Do not present this as a direct mount. Alternative optics/adapters require separate, exact manufacturer evidence.",
  evidence:[
   {label:"GLOCK optic mounting: Slimline versus standard MOS",url:SOURCES.glockOptics,checkedAt:PAIRING_REVIEWED},
   {label:"Holosun SCS-M-GR supported models",url:SOURCES.holosunSCS,checkedAt:PAIRING_REVIEWED}
  ]
 }),
 Object.freeze({
  firearmId:"glock-g19-gen5-mos",accessoryId:"streamlight-tlr7-x",
  status:"family-guidance",
  short:"Manufacturer family guidance; exact fit unconfirmed",
  summary:"Streamlight's TLR-7/8 guide lists most rail-equipped full-size and compact Gen5 GLOCK pistols with a 1913-1 key, but it does not establish this exact individual configuration as tested.",
  why:"The fit-guide reference is for a family and mounting key. Exact firearm rail, light revision, key, clearance and professional evaluation still matter.",
  caution:"Do not treat the family guide as an exact verified pairing, a clearance test, or a holster fit approval.",
  evidence:[{label:"Streamlight TLR-7 / TLR-8 manufacturer compatibility list",url:SOURCES.streamlightFit,checkedAt:PAIRING_REVIEWED}]
 }),
 Object.freeze({
  firearmId:"glock-g19-gen5",accessoryId:"streamlight-tlr7-x",
  status:"family-guidance",
  short:"Manufacturer family guidance; exact fit unconfirmed",
  summary:"Streamlight includes most rail-equipped compact GLOCK Gen5 models in the TLR-7/8 family guide. This is a family-level reference.",
  why:"The manufacturer specifies a mounting-key family, not a universal fit assertion for every Glock variant.",
  caution:"Verify the actual rail, key, light revision, clearances and any holster combination separately.",
  evidence:[{label:"Streamlight TLR-7 / TLR-8 manufacturer compatibility list",url:SOURCES.streamlightFit,checkedAt:PAIRING_REVIEWED}]
 })
]);
const statuses=new Set(["manufacturer-listed","factory-interface-differs","family-guidance"]);
const pairIds=new Set();
for(const p of EVIDENCE){
 const key=p.firearmId+"|"+p.accessoryId;
 if(pairIds.has(key))throw Error("Duplicate pair evidence");
 pairIds.add(key);
 if(!statuses.has(p.status)||!p.summary||!p.caution||!p.why||!p.short||!Array.isArray(p.evidence)||!p.evidence.length)throw Error("Invalid evidence record");
 for(const e of p.evidence){
  const url=new URL(e.url);
  if(url.protocol!=="https:"||url.username||url.password||!Object.values(SOURCES).includes(e.url)||!e.label||e.checkedAt!==PAIRING_REVIEWED)throw Error("Unapproved evidence URL");
 }
}
export const PAIRING_EVIDENCE=EVIDENCE;
export function evaluatePairing(firearm,accessory){
 if(!firearm||!accessory)return null;
 const unknown={
  status:"not-reviewed",short:"No exact pairing evidence",
  summary:"Area 33 has not reviewed manufacturer evidence for this exact pair of products.",
  why:"Product categories and visual similarity are not proof of compatibility.",
  caution:"Inspect official compatibility sources and have the exact product variants reviewed before treating this as a fit. This selection cannot enable a visual try-on.",
  evidence:[]
 };
 if(firearm.kind!=="firearm"||accessory.kind!=="accessory"||firearm.approvedItem||accessory.approvedItem)return unknown;
 const record=EVIDENCE.find(p=>p.firearmId===firearm.id&&p.accessoryId===accessory.id);
 return record||unknown;
}
export function manufacturerListedSuggestions(firearm,accessoryItems){
 if(!firearm||firearm.approvedItem||!Array.isArray(accessoryItems))return [];
 return accessoryItems.filter(x=>!x.approvedItem&&
  EVIDENCE.some(p=>p.firearmId===firearm.id&&p.accessoryId===x.id&&p.status==="manufacturer-listed"));
}
