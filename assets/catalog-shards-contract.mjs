/* Area 33 static approved-only catalog v2: index plus verified, paged shards.
   This is NOT a distributor inventory feed or an approval authority.
   The existing v1 browser sanitizer independently validates every public item. */
import {sanitizeCatalogManifest} from "./catalog-static-contract.mjs";

const VERSION=/^r[a-f0-9]{20}$/;
const ID=/^catalog_[a-f0-9]{20}$/;
const SHA=/^[a-f0-9]{64}$/;
const PATH=/^assets\/catalog-shards\/(r[a-f0-9]{20})\/part-([0-9]{4})\.json$/;
const TYPES=new Set(["complete","part","accessory","ammunition","other"]);
const MAX_ITEMS=50000, MAX_SHARDS=500, PER_SHARD=100;
const IN_KEYS=new Set(["schema","version","as_of","coverage","total","shards","products"]);
const SUMMARY_KEYS=new Set(["id","manufacturer","model","variant","description","category","product_type","shard"]);
const SHARD_KEYS=new Set(["url","sha256","count"]);
const DOC_KEYS=new Set(["schema","version","items"]);
function plain(o){return !!o&&typeof o==="object"&&!Array.isArray(o);}
function exact(o,keys){return plain(o)&&Object.keys(o).length===keys.size&&Object.keys(o).every(k=>keys.has(k));}
function txt(v,n=160){return typeof v==="string"&&v.length>0&&v.length<=n&&v.trim()===v&&!/[\u0000-\u001f\u007f]/.test(v);}
function optional(v,n=160){return v===""||txt(v,n);}
function summary(raw){
  if(!exact(raw,SUMMARY_KEYS)||!ID.test(raw.id)||
     !txt(raw.manufacturer,100)||!txt(raw.model,120)||
     !optional(raw.variant,100)||!optional(raw.description,200)||
     !txt(raw.category,100)||!TYPES.has(raw.product_type)||
     !Number.isInteger(raw.shard)||raw.shard<0)return null;
  return raw;
}

export function validateApprovedIndex(doc){
  if(!exact(doc,IN_KEYS)||doc.schema!=="area33.catalog.index.v2"||
     !VERSION.test(doc.version)||typeof doc.as_of!=="string"||
     !Number.isFinite(Date.parse(doc.as_of))||
     !exact(doc.coverage,new Set(["description"]))||
     !txt(doc.coverage.description,200)||
     !Number.isInteger(doc.total)||doc.total<0||doc.total>MAX_ITEMS||
     !Array.isArray(doc.shards)||doc.shards.length>MAX_SHARDS||
     !Array.isArray(doc.products)||doc.products.length!==doc.total||
     (doc.total===0)!==(doc.shards.length===0))return null;
  const counts=doc.shards.map((shard,i)=>{
    if(!exact(shard,SHARD_KEYS)||typeof shard.url!=="string"||!SHA.test(shard.sha256)||
       !Number.isInteger(shard.count)||shard.count<1||shard.count>PER_SHARD)return -1;
    const match=shard.url.match(PATH);
    if(!match||match[1]!==doc.version||Number(match[2])!==i+1)return -1;
    return shard.count;
  });
  if(counts.some(v=>v<0)||counts.reduce((a,b)=>a+b,0)!==doc.total)return null;
  const ids=new Set(), perShard=Array(doc.shards.length).fill(0);
  for(const raw of doc.products){
    const candidate=summary(raw);
    if(!candidate||ids.has(candidate.id)||candidate.shard>=perShard.length)return null;
    ids.add(candidate.id);
    perShard[candidate.shard]++;
  }
  if(perShard.some((v,i)=>v!==counts[i]))return null;
  return {schema:doc.schema,version:doc.version,as_of:doc.as_of,
          coverage:doc.coverage.description,total:doc.total,
          shards:doc.shards,products:doc.products};
}

export function filterApprovedIndex(products,{query="",category="",productType="",brand=""}={}){
  const terms=String(query).toLowerCase().trim().split(/\s+/).filter(Boolean);
  return products.filter(item=>{
    const haystack=[item.manufacturer,item.model,item.variant,item.description,
                    item.category,item.product_type].join(" ").toLowerCase();
    return terms.every(term=>haystack.includes(term))&&
      (!category||item.category.toLowerCase()===String(category).toLowerCase())&&
      (!productType||item.product_type===productType)&&
      (!brand||item.manufacturer.toLowerCase().includes(String(brand).toLowerCase()));
  });
}

export function validateApprovedShard(doc,index,shardNumber,{baseUrl}={}){
  const shard=index.shards[shardNumber];
  if(!shard||!exact(doc,DOC_KEYS)||doc.schema!=="area33.catalog.shard.v2"||
     doc.version!==index.version||!Array.isArray(doc.items)||
     doc.items.length!==shard.count)return null;
  const publicDoc={schema:"area33.catalog.public.v1",
                   coverage:{description:index.coverage},items:doc.items};
  const sanitized=sanitizeCatalogManifest(publicDoc,{baseUrl});
  if(!sanitized||sanitized.items.length!==shard.count)return null;
  const expected=new Map(index.products.filter(item=>item.shard===shardNumber)
                                     .map(item=>[item.id,item]));
  if(expected.size!==shard.count)return null;
  for(let i=0;i<sanitized.items.length;i++){
    const publicItem=sanitized.items[i],source=doc.items[i],e=expected.get(publicItem.id);
    if(!e||source.manufacturer!==e.manufacturer||source.model!==e.model||
       source.variant!==e.variant||(source.description||"")!==e.description||
       source.category!==e.category||source.product_type!==e.product_type)return null;
    expected.delete(publicItem.id);
  }
  return expected.size?null:sanitized.items;
}

export async function fetchApprovedShard(index,shardNumber,fetcher,{baseUrl}={}){
  if(!index||typeof fetcher!=="function")throw Error("Invalid approved shard request");
  const shard=index.shards[shardNumber];
  if(!shard)throw Error("Shard number outside approved index");
  const base=new URL(baseUrl||"https://area33armory.com/catalog.html");
  if(!["http:","https:"].includes(base.protocol))throw Error("Invalid site origin");
  const target=new URL(shard.url,base);
  if(target.origin!==base.origin||target.username||target.password)
    throw Error("Off-origin catalog shard");
  const response=await fetcher(target.href,{credentials:"omit",cache:"no-store"});
  if(!response.ok)throw Error("Approved shard unavailable");
  const body=await response.text();
  if(body.length>1_000_000)throw Error("Unexpected large public catalog shard");
  if(!globalThis.crypto?.subtle)throw Error("Cannot verify approved shard integrity");
  const digest=await globalThis.crypto.subtle.digest(
    "SHA-256",new TextEncoder().encode(body)
  );
  const checksum=Array.from(new Uint8Array(digest),v=>v.toString(16).padStart(2,"0")).join("");
  if(checksum!==shard.sha256)throw Error("Approved shard hash mismatch");
  const parsed=JSON.parse(body);
  const validated=validateApprovedShard(parsed,index,shardNumber,{baseUrl:base.href});
  if(!validated)throw Error("Approved shard content does not match index");
  return validated;
}

export async function pageApprovedIndex(index,filters,offset,limit,fetcher,{baseUrl}={}){
  if(!index||!Number.isInteger(offset)||offset<0||
     !Number.isInteger(limit)||limit<1||limit>100)throw Error("Invalid pagination");
  const matched=filterApprovedIndex(index.products,filters);
  const selected=matched.slice(offset,offset+limit);
  const shardNums=[...new Set(selected.map(x=>x.shard))];
  const lookup=new Map();
  for(const shardNum of shardNums){
    const verified=await fetchApprovedShard(index,shardNum,fetcher,{baseUrl});
    for(const item of verified)lookup.set(item.id,item);
  }
  const items=selected.map(rec=>{
    const item=lookup.get(rec.id);
    if(!item)throw Error("Approved index and shard disagree");
    return item;
  });
  return {items,total:matched.length,hasMore:offset+items.length<matched.length};
}
