/* Fail-closed public catalog static manifest contract.
   Only owner-approved, same-site exact product images are accepted.
   This does not replace server-side authorization or rights approval. */
const ID=/^catalog_[a-f0-9]{20}$/;
const FRAME=/^assets\/approved\/catalog\/(catalog_[a-f0-9]{20})\/view-0[1-8]\.jpg$/;
const TYPES=new Set(["complete","part","accessory","ammunition","other"]);
const TXT=(v,max=160)=>typeof v==="string"&&v.trim().length>0&&v.trim().length<=max?v.trim():null;
const DATE=(v)=>typeof v==="string"&&Number.isFinite(Date.parse(v))?v:null;
const DATESTAMP=(v)=>typeof v==="string"&&/^\d{4}-\d{2}-\d{2}$/.test(v)&&Number.isFinite(Date.parse(v+"T00:00:00Z"))?v:null;
const ITEM_FIELDS=new Set(["id","manufacturer","model","variant","description","presentation_mode","category","product_type","specifications","evidence","images","publication_updated_at"]);
function exactKeys(obj,allow){return Object.keys(obj).every(k=>allow.has(k));}
export function sanitizeCatalogManifest(doc,{baseUrl="https://area33armory.com/"}={}){
  if(!doc||typeof doc!=="object"||Array.isArray(doc)||doc.schema!=="area33.catalog.public.v1"||!Array.isArray(doc.items)||doc.items.length>100||!doc.coverage||typeof doc.coverage.description!=="string")return null;
  const result=[],ids=new Set();
  let base;try{base=new URL(baseUrl);}catch{return null;}
  if(!["http:","https:"].includes(base.protocol))return null;
  for(const raw of doc.items){
    if(!raw||typeof raw!=="object"||Array.isArray(raw)||!exactKeys(raw,ITEM_FIELDS))return null;
    const id=TXT(raw.id,64),manufacturer=TXT(raw.manufacturer,100),model=TXT(raw.model,120),category=TXT(raw.category,100);
    const variant=raw.variant===""?"":TXT(raw.variant,100),description=raw.description===undefined||raw.description===""?"":TXT(raw.description,200),type=TXT(raw.product_type,20);
    if(!id||!ID.test(id)||ids.has(id)||!manufacturer||!model||!category||variant===null||description===null||!TYPES.has(type))return null;
    const presentationMode=raw.presentation_mode===undefined?"image":raw.presentation_mode;
    if(!["image","text_only"].includes(presentationMode))return null;
    if(!DATE(raw.publication_updated_at))return null;
    if(!Array.isArray(raw.specifications)||raw.specifications.length!==0)return null;
    if(!Array.isArray(raw.evidence)||raw.evidence.length!==1)return null;
    const evidence=raw.evidence[0];
    if(!evidence||!TXT(evidence.source_label,160)||!DATESTAMP(evidence.checked_at))return null;
    if(!Array.isArray(raw.images)||raw.images.length>8||
       (presentationMode==="text_only"&&raw.images.length!==0)||
       (presentationMode==="image"&&raw.images.length<1))return null;
    const images=[],angles=new Set();
    for(const photo of raw.images){
      if(!photo||typeof photo!=="object"||photo.rights!=="approved"||!TXT(photo.alt,160))return null;
      if(typeof photo.url!=="string"||!FRAME.test(photo.url))return null;
      const match=photo.url.match(FRAME);
      if(match[1]!==id||angles.has(photo.url))return null;
      angles.add(photo.url);
      const url=new URL(photo.url,base);
      if(url.origin!==base.origin||url.username||url.password)return null;
      images.push({url:url.href,alt:photo.alt.trim()});
    }
    ids.add(id);
    result.push({
      id,manufacturer,model,variant,description,presentationMode,type,category,specs:[],
      evidence:[{source:evidence.source_label.trim(),date:evidence.checked_at}],
      images,updated:raw.publication_updated_at.slice(0,10)
    });
  }
  return {items:result,coverage:doc.coverage.description.slice(0,200)};
}
export function filterPublicCatalog(items,{query="",category="",productType="",brand=""}={}){
  const q=query.toLowerCase().trim().split(/\s+/).filter(Boolean);
  return items.filter(item=>{
    const haystack=[item.manufacturer,item.model,item.variant,item.description,item.category,item.type].join(" ").toLowerCase();
    return q.every(term=>haystack.includes(term)) &&
      (!category||item.category.toLowerCase()===category.toLowerCase()) &&
      (!productType||item.type===productType) &&
      (!brand||item.manufacturer.toLowerCase().includes(brand.toLowerCase()));
  });
}
