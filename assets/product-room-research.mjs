/* Curated research references, NOT approved Area 33 listings, current stock,
   price quotes, licensed media, or accessory fit confirmations.
   Primary-source links were checked 2026-11-08. Use exact public variants
   before promoting any item to a sellable listing. */
export const REFERENCE_SCHEMA="area33.experience.research.v1";
export const REFERENCE_CHECKED="2026-11-08";
export const DEPARTMENTS=Object.freeze(["pistols","rifles","shotguns"]);
export const ACCESSORY_CATEGORIES=Object.freeze(["optics","lights","holsters","cases"]);
export const REFERENCE_PRODUCTS=Object.freeze([
  {id:"glock-g19-gen5",kind:"firearm",department:"pistols",brand:"GLOCK",model:"G19 Gen5",
   subtitle:"Compact pistol · 9×19 mm",facts:["Compact Gen5 model","GLOCK Marksman Barrel","Ambidextrous slide stop"],
   note:"The Gen5 model is not automatically equivalent to MOS or other variants.",
   source:"https://us.glock.com/en/products/law-enforcement/pistols/g19-gen5"},
  {id:"glock-g19-gen5-mos",kind:"firearm",department:"pistols",brand:"GLOCK",model:"G19 Gen5 MOS",
   subtitle:"Factory Modular Optic System · compact 9×19 mm",
   facts:["G19 Gen5 factory MOS configuration","Optic-ready slide with GLOCK MOS system","Not equivalent to standard G19 Gen5 slide"],
   note:"GLOCK confirms a distinct factory G19 Gen5 MOS configuration. Direct mounting depends on the exact optic and MOS design; do not treat non-MOS or slimline MOS as interchangeable.",
   source:"https://us.glock.com/en/press-release/news-page/take-aim-with-glocks-new-modular-optic-ready-pistols"},
  {id:"glock-g43x-mos",kind:"firearm",department:"pistols",brand:"GLOCK",model:"G43X MOS",
   subtitle:"Slimline optic-ready pistol · 9×19 mm",facts:["Slimline MOS configuration","Factory slide optic cut","Slim mounting rail"],
   note:"The MOS cut and narrow rail have model-specific requirements.",
   source:"https://us.glock.com/en/press-release/news-page/glock-introduces-optic-ready-slimline-models-g43x-and-g48"},
  {id:"sig-p365-xmacro",kind:"firearm",department:"pistols",brand:"SIG SAUER",model:"P365-XMACRO",
   subtitle:"P365 family · compact 9 mm",facts:["Factory optic-ready slide","Integrated compensator on original model","1913 accessory rail"],
   note:"P365 variants differ; verify the exact SKU before checking accessories.",
   source:"https://www.sigsauer.com/blog/sig-sauer-introduces-p365-xmacro-bringing-even-more-to-everyday-carry"},
  {id:"canik-mete-sft",kind:"firearm",department:"pistols",brand:"CANiK",model:"METE SFT",
   subtitle:"METE series · 9×19 mm",facts:["METE series","Striker-fired model","Manufacturer catalog reference"],
   note:"Global product family reference; U.S. SKU, finish and availability are unverified.",
   source:"https://www.canik.com/global/products"},
  {id:"ruger-american-gen2",kind:"firearm",department:"rifles",brand:"Ruger",model:"American Rifle Generation II",
   subtitle:"Bolt-action rifle family",facts:["Generation II family","Multiple models and chamberings","Exact variant must be selected to verify specs"],
   note:"This is a product family, not a specific rifle SKU.",
   source:"https://ruger.com/products/americanRifleGenII/overview.html"},
  {id:"ruger-precision-308-gen1",kind:"firearm",department:"rifles",brand:"Ruger",model:"Precision Rifle · .308 Win · Gen 1",
   subtitle:"First-generation .308 Winchester research photograph",
   facts:["A specific first-generation Ruger Precision Rifle","Photographed in .308 Winchester","One documented real photograph; not a model's full specifications"],
   note:"The licensed third-party photograph identifies this older rifle as .308 Winchester, Generation 1. It is not a current Ruger SKU or verified sale item. Details beyond the photo require Ruger model-specific documentation.",
   source:"https://ruger.com/products/precisionRifle/overview.html"},
  {id:"ruger-precision-6mm-2019-photo",kind:"firearm",department:"rifles",brand:"Ruger",model:"Precision Rifle · 6mm Creedmoor · photographed example",
   subtitle:"Photographed Ruger Precision Rifle in 6mm Creedmoor · 2019 image",
   facts:["A real photographed example identified as a Ruger Precision Rifle","Photo identifies 6mm Creedmoor chambering","Shows a previously photographed optic; exact optic model unverified"],
   note:"Photographed rifle example from Tactical Accountants (2019); this is not the same rifle or an alternative view of the .308 Generation 1. Any pictured accessory is not independently identified or confirmed as an exact sellable pairing.",
   source:"https://www.ruger.com/products/precisionRifle/overview.html"},
  {id:"ruger-precision",kind:"firearm",department:"rifles",brand:"Ruger",model:"Precision Rifle",
   subtitle:"Precision bolt-action rifle family",facts:["Ruger Precision Rifle family","Multiple calibers and model numbers","Configurations vary by SKU"],
   note:"A family-level research page; do not infer caliber, accessories or price.",
   source:"https://www.ruger.com/products/precisionRifle/overview.html"},
  {id:"mossberg-590a1-pro",kind:"firearm",department:"shotguns",brand:"Mossberg",model:"590A1 Professional Series",
   subtitle:"Pump-action shotgun family",facts:["590A1 Professional Series","Multiple configurations","Manufacturer documentation available"],
   note:"Manufacturer's announcement includes several distinct variants, some regulated.",
   source:"https://resources.mossberg.com/hubfs/press_releases/Mossberg%20Introduces%20590A1%20Professional%20Series%20Shotguns%20PR%201-6-2025%20FINAL.pdf"},
  {id:"beretta-a300-patrol",kind:"firearm",department:"shotguns",brand:"Beretta",model:"A300 Patrol",
   subtitle:"Gas-operated semi-automatic shotgun family",facts:["A300 Patrol family","Manufacturer manual available","Configurations must be checked individually"],
   note:"Exact product variant and availability are not established in this research set.",
   source:"https://dam.beretta.com/content/dam/beretta-usa/user-manuals/Beretta-USA-Semiauto-Manual-Rev-3.pdf"},
  {id:"holosun-scs-m-gr",kind:"accessory",accessoryType:"optics",brand:"Holosun",model:"SCS-M-GR",
   subtitle:"Solar Charging Sight · specifically listed for full-size GLOCK MOS",
   facts:["Holosun names G19 Gen5 MOS under Direct Mount fitment","Designed for full-size GLOCK MOS slide interface","Not an interchangeable generic K-footprint optic"],
   note:"Holosun's fitment list specifically names the G19 Gen5 MOS for the SCS-M-GR. Still verify exact variants, manufacturer updates and safe professional installation before use.",
   source:"https://www.holosun.com/products/scs-m-gr"},
  {id:"meopta-optika6-3-18x56-rd-sfp",kind:"accessory",accessoryType:"optics",brand:"Meopta",model:"MeoPro Optika6 3–18×56 RD SFP",
   subtitle:"Real photographed Meopta riflescope · 3–18×56 RD SFP",
   facts:["Photograph identifies an Optika6 RD SFP scope","Meopta names a 3–18×56 RD SFP variant","Mounting requires independently verified rifle, rail and rings"],
   note:"The actual Meopta scope photo is licensed for use, but there is no manufacturer-verified pairing with the Ruger photographs here. The two items are displayed separately, not digitally attached.",
   source:"https://www.meoptasportsoptics.com/Aton/FileRepository/aton_file_repository_HtmlEditorRepositoryDoc/Root/manual-optika6.pdf"},
  {id:"holosun-hs507k-x2",kind:"accessory",accessoryType:"optics",brand:"Holosun",model:"HS507K-X2",
   subtitle:"Compact reflex optic",facts:["K-footprint optic","Multi-Reticle System","Maker's fitment notes are product-specific"],
   note:"Do not infer fit from 'optic-ready' alone; interface and any adapters need verification.",
   source:"https://www.holosun.com/products/hs507k-x2"},
  {id:"streamlight-tlr7-x",kind:"accessory",accessoryType:"lights",brand:"Streamlight",model:"TLR-7 X",
   subtitle:"Compact rail-mounted light",facts:["Multi-fuel design","Rail fit guide published","Model-specific keys may be required"],
   note:"Rail appearance alone is not proof of clearance or mounting compatibility.",
   source:"https://www.streamlight.com/products/detail/tlr-7-x"},
  {id:"streamlight-tlr7-x-sub",kind:"accessory",accessoryType:"lights",brand:"Streamlight",model:"TLR-7 X sub",
   subtitle:"Subcompact rail-mounted light",facts:["Subcompact variant","Different mounting versions","Manufacturer fit guide required"],
   note:"The sub and standard TLR-7 X are distinct products. Verify exact part number and rail type.",
   source:"https://www.streamlight.com/products/detail/tlr-7-x-sub"},
  {id:"aliengear-photon",kind:"accessory",accessoryType:"holsters",brand:"Alien Gear",model:"PHOTON Holster",
   subtitle:"Inside/outside waistband holster system",facts:["PHOTON product line","Options vary by holster configuration","Exact firearm/light version must be chosen"],
   note:"Holster shell fit cannot be determined from this family-level reference.",
   source:"https://aliengearholsters.com/collections/photon-holsters"},
  {id:"aliengear-cloaktuck35",kind:"accessory",accessoryType:"holsters",brand:"Alien Gear",model:"Cloak Tuck 3.5",
   subtitle:"Inside-the-waistband hybrid holster",facts:["IWB hybrid design","Specific shell required","Maker describes customizable fit"],
   note:"The product page alone is not confirmation for any firearm/accessory combination.",
   source:"https://aliengearholsters.com/products/cloak-tuck-3-5-iwb-holster"}
]);
const ids=new Set(),allowHosts=new Set(["us.glock.com","www.sigsauer.com","www.canik.com","ruger.com","www.ruger.com","resources.mossberg.com","dam.beretta.com","www.holosun.com","www.streamlight.com","aliengearholsters.com","www.meoptasportsoptics.com"]);
for(const item of REFERENCE_PRODUCTS){
 if(ids.has(item.id)||!/^[a-z0-9-]{5,65}$/.test(item.id))throw Error("Duplicate or invalid research id");
 ids.add(item.id);
 if(!["firearm","accessory"].includes(item.kind)||typeof item.brand!=="string"||typeof item.model!=="string")throw Error("Invalid reference");
 if(item.kind==="firearm"&&!DEPARTMENTS.includes(item.department))throw Error("Unknown firearm category");
 if(item.kind==="accessory"&&!ACCESSORY_CATEGORIES.includes(item.accessoryType))throw Error("Unknown accessory category");
 const u=new URL(item.source);
 if(u.protocol!=="https:"||!allowHosts.has(u.hostname)||u.username||u.password)throw Error("Nonofficial source URL");
 if(!Array.isArray(item.facts)||item.facts.length<1||item.facts.some(x=>typeof x!=="string"))throw Error("Invalid research notes");
}
export const researchTitle=item=>[item.brand,item.model].filter(Boolean).join(" ");
export function researchByDepartment(department){
 return REFERENCE_PRODUCTS.filter(x=>x.kind==="firearm"&&x.department===department);
}
export function researchAccessories(category){
 return REFERENCE_PRODUCTS.filter(x=>x.kind==="accessory"&&(!category||x.accessoryType===category));
}
export function chooseDiscovery(items,currentId,seed){
 if(!Array.isArray(items)||!items.length)return null;
 const sorted=items.slice().sort((a,b)=>a.id.localeCompare(b.id));
 let i=Math.abs(Number.isFinite(seed)?Math.trunc(seed):0)%sorted.length;
 if(sorted.length>1&&sorted[i].id===currentId)i=(i+1)%sorted.length;
 return sorted[i];
}
