import assert from "node:assert/strict";
import {createHash,webcrypto} from "node:crypto";
import {
  validateApprovedIndex,validateApprovedShard,filterApprovedIndex,
  pageApprovedIndex,fetchApprovedShard
} from "../assets/catalog-shards-contract.mjs";
globalThis.crypto ||= webcrypto;
const base="https://area33armory.com/catalog.html";
const version="r"+"c".repeat(20);
const product=(i)=>({
  id:"catalog_"+i.toString(16).padStart(20,"0"),
  manufacturer:"Example Maker",model:"Model "+i,
  variant:i%2?"Black":"",description:i===204?
    "Unique long-tail feature for record 204":"Verified source details "+i,
  category:i%3===0?"Optics":"Accessories",
  product_type:"accessory",specifications:[],
  evidence:[{source_label:"Owner-reviewed product documentation",checked_at:"2026-11-04"}],
  images:[{
    url:"assets/approved/catalog/catalog_"+i.toString(16).padStart(20,"0")+
        "/view-01.jpg",
    alt:"Original photo for exact product "+i,rights:"approved",
  }],
  publication_updated_at:"2026-11-05T09:00:00Z"
});
const products=Array.from({length:205},(_,i)=>product(i));
// A fully reviewed, owner-written product without any supplier imagery can
// coexist in the SAME approved-only 205-record sharded catalog.
products[203]={...products[203],presentation_mode:"text_only",images:[],
  description:"Original owner-written product profile for 203"};
const shards=[],texts=new Map();
for(let i=0;i<products.length;i+=100){
  const group=products.slice(i,i+100);
  const shardNumber=i/100, url="assets/catalog-shards/"+version+
    "/part-"+String(shardNumber+1).padStart(4,"0")+".json";
  const body=JSON.stringify({
    schema:"area33.catalog.shard.v2",version,items:group,
  });
  texts.set(new URL(url,base).href,body);
  shards.push({url,count:group.length,sha256:createHash("sha256")
               .update(body,"utf8").digest("hex")});
}
const index={
  schema:"area33.catalog.index.v2",version,as_of:"2026-11-05T09:00:00Z",
  coverage:{description:"Only expressly owner-approved Area 33 product records."},
  total:products.length,shards,
  products:products.map((p,i)=>({
    id:p.id,manufacturer:p.manufacturer,model:p.model,variant:p.variant,
    description:p.description,category:p.category,
    product_type:p.product_type,shard:Math.floor(i/100),
  })),
};
const verified=validateApprovedIndex(index);
assert.ok(verified);
assert.equal(verified.total,205);
assert.equal(verified.shards.length,3);
assert.equal(filterApprovedIndex(verified.products,{query:"unique long-tail"}).length,1);
assert.equal(filterApprovedIndex(verified.products,{query:"model 204"}).length,1);
assert.equal(filterApprovedIndex(verified.products,{category:"Optics"}).length,69);
assert.equal(filterApprovedIndex(verified.products,{brand:"nonexistent"}).length,0);

let reads=[];
const fetcher=async (url,options)=>{
  assert.equal(options.credentials,"omit");
  assert.equal(options.cache,"no-store");
  reads.push(url);
  return {ok:true,text:async()=>texts.get(url)};
};
const first=await pageApprovedIndex(verified,{},0,12,fetcher,{baseUrl:base});
assert.equal(first.items.length,12);
assert.equal(first.items[0].id,products[0].id);
assert.equal(first.total,205);
assert.equal(first.hasMore,true);
assert.equal(reads.length,1);
const boundary=await pageApprovedIndex(verified,{},98,12,fetcher,{baseUrl:base});
assert.equal(boundary.items.length,12);
assert.equal(boundary.items[0].id,products[98].id);
assert.equal(boundary.items.at(-1).id,products[109].id);
assert.equal(reads.length,3); // 1 for first page, 2 for boundary page
const end=await pageApprovedIndex(verified,{},200,12,fetcher,{baseUrl:base});
assert.equal(end.items.length,5);
assert.equal(end.hasMore,false);
assert.equal(end.items[3].presentationMode,"text_only");
assert.deepEqual(end.items[3].images,[]);
assert.equal(end.items[3].description,"Original owner-written product profile for 203");
const longTail=await pageApprovedIndex(verified,{query:"unique long-tail"},0,12,fetcher,{baseUrl:base});
assert.equal(longTail.items.length,1);
assert.equal(longTail.items[0].id,products[204].id);

assert.equal(validateApprovedIndex({...index,total:204}),null);
assert.equal(validateApprovedIndex({...index,products:[
  index.products[0],...index.products.slice(1,-1),index.products[0]
]}),null);
assert.equal(validateApprovedIndex({...index,shards:[
  {...shards[0],url:"https://attacker.example/file.json"},...shards.slice(1)
]}),null);
assert.equal(validateApprovedIndex({...index,products:[
  {...index.products[0],dealer_cost:"PRIVATE"},...index.products.slice(1)
]}),null);
assert.equal(validateApprovedIndex({...index,shards:[
  {...shards[0],count:101},...shards.slice(1)
]}),null);
const badShard={
  schema:"area33.catalog.shard.v2",version,
  items:[{...products[0],source_sku:"PRIVATE"},...products.slice(1,100)],
};
assert.equal(validateApprovedShard(badShard,verified,0,{baseUrl:base}),null);
assert.equal(validateApprovedShard({
  schema:"area33.catalog.shard.v2",version,
  items:[{...products[0],images:[
    {...products[0].images[0],rights:"pending"}
  ]},...products.slice(1,100)]
},verified,0,{baseUrl:base}),null);
await assert.rejects(
  ()=>fetchApprovedShard(verified,0,
    async()=>({ok:true,text:async()=>texts.get(reads[0])+"tampered"}),
    {baseUrl:base}),
  /hash mismatch/
);
const changed=new Map(texts);
const goodText=texts.get(new URL(shards[0].url,base).href);
changed.set(new URL(shards[0].url,base).href,goodText.replace("Verified source details 0","Changed public record"));
await assert.rejects(
  ()=>fetchApprovedShard(verified,0,
    async url=>({ok:true,text:async()=>changed.get(url)}),{baseUrl:base}),
  /hash mismatch/
);
const empty={
  schema:"area33.catalog.index.v2",version,as_of:index.as_of,
  coverage:index.coverage,total:0,shards:[],products:[],
};
assert.ok(validateApprovedIndex(empty));
console.log("Area 33 sharded approved-only public catalog: >200 items, lazy paging, integrity, search, privacy checks passed.");
