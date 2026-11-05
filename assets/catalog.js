"use strict";
import {sanitizeCatalogManifest,filterPublicCatalog} from "./catalog-static-contract.mjs";
import {validateApprovedIndex,pageApprovedIndex} from "./catalog-shards-contract.mjs";
/* The API must be a public, approval-gated, same-origin or explicitly trusted endpoint.
   No credentials, dealer data or demo product records belong in this browser file. */
const PUBLIC_CATALOG_ENDPOINT = null; // Future filtered server API; not enabled.
const STATIC_CATALOG_PATH = "assets/catalog-public.json"; // Approved-only, empty by default.
const SHARDED_INDEX_PATH = "assets/catalog-index.v2.json"; // Optional approved-only full index.
let approvedIndex=null, approvedIndexChecked=false;
const $=id=>document.getElementById(id);
const state={query:"",category:"",productType:"",brand:"",cursor:null,next:null,page:0,items:[],seen:new Set(),compare:[],request:0};
const LIMIT=12, MAX_COMPARE=3;
const allowedTypes=new Set(["complete","part","accessory","ammunition","other"]);
const safeText=v=>typeof v==="string"?v.trim().slice(0,200):"";
function safeImage(value){if(!value||typeof value!=="object"||value.rights!=="approved")return null;try{const u=new URL(value.url,location.href);if(u.protocol!=="https:"||u.username||u.password)return null;return{url:u.href,alt:safeText(value.alt)||"Product image"};}catch{return null;}}
function cleanRecord(record){if(!record||typeof record!=="object"||Array.isArray(record))return null;const id=safeText(record.id),name=safeText(record.model),manufacturer=safeText(record.manufacturer);if(!id||!name||!manufacturer||!allowedTypes.has(record.product_type))return null;const specs=Array.isArray(record.specifications)?record.specifications.slice(0,30).filter(s=>s&&typeof s==="object"&&safeText(s.label)&&typeof s.value==="string").map(s=>({label:safeText(s.label),value:safeText(s.value)})):[];const evidence=Array.isArray(record.evidence)?record.evidence.slice(0,10).filter(e=>e&&typeof e==="object"&&safeText(e.source_label)).map(e=>({source:safeText(e.source_label),date:validDate(e.checked_at)})):[];const images=Array.isArray(record.images)?record.images.map(safeImage).filter(Boolean).slice(0,6):[];return{id,model:name,manufacturer,variant:safeText(record.variant),description:safeText(record.description),presentationMode:record.presentation_mode==="text_only"?"text_only":"image",type:record.product_type,category:safeText(record.category)||"Uncategorized",specs,evidence,images,updated:validDate(record.publication_updated_at)};}
function validDate(v){if(typeof v!=="string"||!/^\d{4}-\d{2}-\d{2}T/.test(v))return null;const d=new Date(v);return Number.isFinite(d.getTime())?d.toISOString().slice(0,10):null;}
function el(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;}
function setMessage(title,body){$("message").replaceChildren(el("strong","",title),el("p","",body));$("message").hidden=false;}
function searchParams(cursor){const params=new URLSearchParams({limit:String(LIMIT)});if(state.query)params.set("q",state.query);if(state.category)params.set("category",state.category);if(state.productType)params.set("product_type",state.productType);if(state.brand)params.set("brand",state.brand);if(cursor)params.set("cursor",cursor);return params;}
async function loadStaticLegacy(reset,token){
  if(reset){state.cursor=null;state.next=null;state.page=0;state.items=[];state.seen.clear();$("grid").replaceChildren();$("grid").hidden=true;}
  $("next").disabled=true;
  setMessage("Checking approved catalog…","Only owner-approved public product records can be shown.");
  try{
    const response=await fetch(STATIC_CATALOG_PATH,{credentials:"omit",cache:"no-store"});
    if(!response.ok)throw Error("Approved static catalog unavailable");
    const catalog=sanitizeCatalogManifest(await response.json(),{baseUrl:location.href});
    if(!catalog)throw Error("Invalid public catalog schema");
    if(token!==state.request)return;
    const matches=filterPublicCatalog(catalog.items,{
      query:state.query,category:state.category,productType:state.productType,brand:state.brand
    });
    const offset=state.items.length;
    const page=matches.slice(offset,offset+LIMIT);
    for(const item of page){if(!state.seen.has(item.id)){state.seen.add(item.id);state.items.push(item);}}
    state.next=state.items.length<matches.length?String(state.items.length):null;
    state.page++;
    $("coverage").textContent=catalog.coverage;
    drawCards();
    $("page-label").textContent=state.items.length+" approved public record(s) loaded. "+
      (state.next?"More matching published records available.":"End of approved published results.");
    $("pagination").hidden=!state.items.length;
    $("next").hidden=!state.next;
    if(!state.items.length){
      setMessage("No approved public listings","No matching owner-approved product records are published here yet. This does not indicate supplier inventory or availability.");
    }else $("message").hidden=true;
  }catch{
    if(token!==state.request)return;
    setMessage("Approved product catalog unavailable","The published catalog could not be verified. No substitute or private supplier records will be displayed.");
    $("coverage").textContent="Verified public listing data unavailable";
  }finally{if(token===state.request)$("next").disabled=false;}
}
function populateApprovedCategories(index){
  const select=$("category"),selected=select.value,existing=new Set(
    [...select.options].map(o=>o.value)
  );
  const categories=[...new Set(index.products.map(item=>item.category))].sort(
    (a,b)=>a.localeCompare(b)
  );
  for(const value of categories){
    if(existing.has(value))continue;
    const option=document.createElement("option");
    option.value=value;option.textContent=value;select.append(option);
  }
  select.value=categories.includes(selected)?selected:"";
}
async function loadSharded(reset,token){
  if(reset){
    state.cursor=null;state.next=null;state.page=0;state.items=[];
    state.seen.clear();$("grid").replaceChildren();$("grid").hidden=true;
  }
  $("next").disabled=true;
  setMessage("Checking approved catalog…",
             "Reading owner-approved public product records only.");
  try{
    const page=await pageApprovedIndex(
      approvedIndex,{query:state.query,category:state.category,
        productType:state.productType,brand:state.brand},
      state.items.length,LIMIT,fetch,{baseUrl:location.href}
    );
    if(token!==state.request)return;
    for(const item of page.items){
      if(!state.seen.has(item.id)){
        state.seen.add(item.id);state.items.push(item);
      }
    }
    state.page++;
    state.next=page.hasMore?String(state.items.length):null;
    $("coverage").textContent=approvedIndex.coverage;
    drawCards();
    $("page-label").textContent=state.items.length+" of "+page.total+
      " matching approved public records loaded.";
    $("pagination").hidden=!state.items.length;
    $("next").hidden=!state.next;
    if(!state.items.length){
      setMessage("No approved public listings",
                 "No matching owner-approved records are available. This is not a stock check.");
    }else $("message").hidden=true;
  }catch{
    if(token!==state.request)return;
    state.items=[];state.seen.clear();state.next=null;
    $("grid").replaceChildren();$("grid").hidden=true;
    $("pagination").hidden=true;
    $("coverage").textContent="Approved public catalog unavailable";
    setMessage("Catalog verification failed",
               "Approved product records could not be verified. No supplier data is displayed.");
  }finally{if(token===state.request)$("next").disabled=false;}
}
async function loadStatic(reset,token){
  if(!approvedIndexChecked){
    try{
      const response=await fetch(SHARDED_INDEX_PATH,{
        credentials:"omit",cache:"no-store"
      });
      if(response.status===404){
        approvedIndexChecked=true;
      }else{
        if(!response.ok)throw Error("Approved index unavailable");
        const verified=validateApprovedIndex(await response.json());
        if(!verified)throw Error("Approved index failed validation");
        approvedIndex=verified;
        approvedIndexChecked=true;
        populateApprovedCategories(verified);
      }
    }catch{
      if(token!==state.request)return;
      state.items=[];state.seen.clear();state.next=null;
      $("grid").replaceChildren();$("grid").hidden=true;
      $("pagination").hidden=true;
      $("coverage").textContent="Approved public catalog unavailable";
      setMessage("Catalog verification failed",
                 "The approved catalog index is invalid or unavailable. No private data is shown.");
      return;
    }
  }
  if(token!==state.request)return;
  if(approvedIndex)return loadSharded(reset,token);
  return loadStaticLegacy(reset,token);
}
async function load(reset=true){const token=++state.request;if(!PUBLIC_CATALOG_ENDPOINT)return loadStatic(reset,token);if(!PUBLIC_CATALOG_ENDPOINT){setMessage("Catalog not connected yet","We're preparing the verified public product catalog. No product information, inventory or pricing has been published here. Educational guides and direct inquiries remain available.");$("coverage").textContent="Public catalog connection pending";return;}if(reset){state.cursor=null;state.next=null;state.page=0;state.items=[];state.seen.clear();$("grid").replaceChildren();$("grid").hidden=true;}$("next").disabled=true;setMessage("Loading public records…","Retrieving approved information.");try{const base=new URL(PUBLIC_CATALOG_ENDPOINT,location.href);if(base.protocol!=="https:"&&!(base.protocol==="http:"&&base.hostname==="localhost"))throw Error("Invalid public endpoint");base.search=searchParams(state.cursor).toString();const response=await fetch(base.href,{method:"GET",credentials:"omit",headers:{"Accept":"application/json"}});if(!response.ok)throw Error("Request failed");const body=await response.json();if(!body||!Array.isArray(body.items)||!("next_cursor" in body)||!body.coverage||typeof body.coverage.description!=="string")throw Error("Invalid public response");if(token!==state.request)return;const incoming=body.items.map(cleanRecord).filter(Boolean);const fresh=incoming.filter(item=>!state.seen.has(item.id));fresh.forEach(item=>state.seen.add(item.id));state.items.push(...fresh);if(typeof body.next_cursor==="string"&&body.next_cursor.length>0&&body.next_cursor!==state.cursor)state.next=body.next_cursor;else state.next=null;state.page++;if(token!==state.request)return;$("coverage").textContent=safeText(body.coverage.description)||"Approved published catalog (coverage not specified)";drawCards();$("page-label").textContent=state.items.length+" published record(s) loaded. "+(state.next?"More pages available.":"No more matching published pages.");$("pagination").hidden=!state.items.length;$("next").hidden=!state.next;if(!state.items.length)setMessage("No published matches","Try different terms or filters. This search covers approved public records only, not all supplier inventory.");else $("message").hidden=true;}catch{if(token!==state.request)return;setMessage("Catalog currently unavailable","Public product information could not be retrieved. No substitute or sample inventory is being shown. Please try again later or contact Area 33.");$("coverage").textContent="Connection unavailable";}finally{if(token===state.request)$("next").disabled=false;}}
function productTitle(item){return[item.manufacturer,item.model,item.variant].filter(Boolean).join(" ");}
function drawCards(){const grid=$("grid");grid.replaceChildren();for(const item of state.items){const card=el("article","product-card"),media=el("div","product-media");if(item.images[0]){const img=el("img");img.src=item.images[0].url;img.alt=item.images[0].alt;img.loading="lazy";img.referrerPolicy="no-referrer";img.addEventListener("error",()=>{img.replaceWith(el("div","placeholder","Image unavailable"))});media.append(img);}else if(item.presentationMode==="text_only"){media.classList.add("text-first");media.append(
  el("span","text-first-eyebrow","PRODUCT PROFILE"),
  el("strong","text-first-brand",item.manufacturer),
  el("span","text-first-model",item.model)
);}else media.append(el("div","placeholder","IMAGE PENDING APPROVAL"));
media.append(el("small","",item.presentationMode==="text_only"?"Text-only verified listing":item.images.length?"Approved product image":"No approved image"));const body=el("div","product-info");body.append(el("span","type",item.category+" · "+item.type),el("h4","",productTitle(item)));const spec=el("p","specs",item.description||item.specs.slice(0,3).map(s=>s.label+": "+s.value).join(" · ")||"Verified specifications not provided");body.append(spec,el("div","source",item.evidence.length?"Source: "+item.evidence[0].source+" · Checked: "+(item.evidence[0].date||"date not supplied"):"Source details not provided"));const actions=el("div","product-actions"),view=el("button","","View details");view.type="button";view.onclick=()=>showDetail(item);const compare=el("button","secondary",state.compare.some(i=>i.id===item.id)?"Remove comparison":"Compare");compare.type="button";compare.setAttribute("aria-pressed",String(state.compare.some(i=>i.id===item.id)));compare.onclick=()=>toggleCompare(item);actions.append(view,compare);const labLink=el("a","secondary lab-product-link","Optional Experience Lab ↗");labLink.href="experience-lab.html?product="+encodeURIComponent(item.id);labLink.setAttribute("aria-label","Open optional Experience Lab; product-specific media may not be available");actions.append(labLink);body.append(actions);card.append(media,body);grid.append(card);}grid.hidden=!state.items.length;}
function showDetail(item){const root=$("detail-content");root.replaceChildren(el("h2","",productTitle(item)),el("p","",item.category+" / "+item.type));if(item.description)root.append(el("p","",item.description));if(item.images[0]){const img=el("img","detail-media");img.src=item.images[0].url;img.alt=item.images[0].alt;img.referrerPolicy="no-referrer";root.append(img);}else root.append(el("p","muted",item.presentationMode==="text_only"?
  "Text-only product record. No manufacturer image rights or visual specifications are implied.":
  "No approved photo is available for this exact product."));const dl=el("dl","detail-list");const values=[["Exact public ID",item.id],["Variant",item.variant||"Not specified"],["Published update",item.updated||"Unknown"],["Stock status","Not verified"],["Customer price","Not published"]];for(const s of item.specs)values.push([s.label,s.value]);for(const e of item.evidence)values.push(["Evidence",e.source+" — checked "+(e.date||"date unknown")]);for(const [key,value] of values)dl.append(el("dt","",key),el("dd","",value));root.append(dl,el("p","muted","Information is not a quote, live stock confirmation, or purchase option."));const optional=el("a","lab-product-link","Explore available interactive media ↗");optional.href="experience-lab.html?product="+encodeURIComponent(item.id);root.append(optional);const rights=el("a","lab-product-link","Report an image or attribution concern");rights.href="contact.html?topic="+encodeURIComponent("Image or trademark rights")+"&product="+encodeURIComponent(item.id);rights.style.marginLeft="8px";root.append(rights);$("detail-dialog").showModal();}
function toggleCompare(item){const at=state.compare.findIndex(i=>i.id===item.id);if(at>=0)state.compare.splice(at,1);else if(state.compare.length<MAX_COMPARE)state.compare.push(item);else{window.alert("Compare up to three products at a time.");return;}drawCards();drawCompare();}
function drawCompare(){const section=$("compare");section.hidden=state.compare.length===0;if(!state.compare.length)return;const wrap=$("compare-content");wrap.replaceChildren();const table=el("table"),thead=el("thead"),head=el("tr");head.append(el("th","","Field"));state.compare.forEach(item=>head.append(el("th","",productTitle(item))));thead.append(head);table.append(thead);const tbody=el("tbody");const names=["Product type","Category","Variant","Last published","Source checked",...new Set(state.compare.flatMap(item=>item.specs.map(s=>s.label)))];for(const name of names){const tr=el("tr");tr.append(el("th","",name));for(const item of state.compare){let v="Unknown";if(name==="Product type")v=item.type;else if(name==="Category")v=item.category;else if(name==="Variant")v=item.variant||"Unknown";else if(name==="Last published")v=item.updated||"Unknown";else if(name==="Source checked")v=item.evidence[0]?.date||"Unknown";else v=item.specs.find(s=>s.label===name)?.value||"Unknown";tr.append(el("td","",v));}tbody.append(tr);}table.append(tbody);wrap.append(table);}
function updateFilters(){state.query=$("query").value.trim().slice(0,160);state.category=$("category").value;state.productType=$("product-type").value;state.brand=$("brand").value.trim().slice(0,100);state.compare=[];$("compare").hidden=true;load(true);}
const requested=new URLSearchParams(location.search).get("product");if(requested){const context=$("catalog-context");context.hidden=false;context.textContent="Returned to standard browsing. Product-specific results will become available once the approved public catalog is connected.";}
$("catalog-form").addEventListener("submit",e=>{e.preventDefault();updateFilters();});$("apply").addEventListener("click",updateFilters);$("clear").addEventListener("click",()=>{$("query").value="";$("category").value="";$("product-type").value="";$("brand").value="";updateFilters();});$("next").addEventListener("click",()=>{if(!state.next)return;state.cursor=state.next;load(false);});$("reset-compare").addEventListener("click",()=>{state.compare=[];$("compare").hidden=true;drawCards();});$("close-detail").addEventListener("click",()=>$("detail-dialog").close());$("detail-dialog").addEventListener("click",e=>{if(e.target===$("detail-dialog"))$("detail-dialog").close();});load(true);
