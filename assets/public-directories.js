"use strict";
/* Static public-only browsing. Never load Randbeck private records or credentials. */
(async function () {
  const kind = document.body.dataset.directory;
  if (kind !== "portfolio" && kind !== "ffl") return;
  const byId=id=>document.getElementById(id);
  const mode = kind === "portfolio" ? {
    file:"assets/passport-public.json",schema:"passport.public.v1",noun:"portfolios"
  } : {
    file:"assets/ffl-public.json",schema:"ffl.partners.public.v1",noun:"receiving dealers"
  };
  const allowedIndustries=new Set(["firearm-services","automotive","construction","fabrication","other"]);
  const txt=(s,n=160)=>typeof s==="string"?s.trim().slice(0,n):"";
  const element=(tag,cls,value)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(value!==undefined)e.textContent=value;return e;};
  const results=byId("results"),empty=byId("empty"),status=byId("status");
  let items=[];
  function imagePath(value) {
    const s=txt(value,180);
    return /^assets\/approved\/[a-zA-Z0-9/_-]+\.(png|jpg|jpeg|webp)$/.test(s)&&!s.includes("..")?s:null;
  }
  function cleanPortfolio(r){
    if(!r||typeof r!=="object"||r.published!==true||!allowedIndustries.has(r.industry))return null;
    const name=txt(r.business_name,100),title=txt(r.title,150),id=txt(r.public_id,90);
    if(!name||!title||!id||!txt(r.service,90)||!txt(r.summary,900))return null;
    return {id,industry:r.industry,name,title,service:txt(r.service),summary:txt(r.summary,900),location:txt(r.location_label,100),period:txt(r.completed_period,50),evidence:txt(r.verification_label,90),image:imagePath(r.cover_image)};
  }
  function cleanDealer(r){
    if(!r||typeof r!=="object"||r.published!==true||r.acceptance_confirmed!==true)return null;
    const name=txt(r.business_name,100),id=txt(r.public_id,90),state=txt(r.state,2).toUpperCase(),city=txt(r.city,100);
    if(!name||!id||!city||! /^[A-Z]{2}$/.test(state))return null;
    return {id,name,state,city,zip:txt(r.zip,5),updated:txt(r.acceptance_checked_at,10),policy:txt(r.transfer_policy_summary,400)};
  }
  function makeCard(r){
    const article=element("article","card");
    if(kind==="portfolio"){
      const art=element("div","card-art","APPROVED WORK");
      if(r.image){const im=element("img");im.src=r.image;im.alt="Published project image provided by "+r.name;im.loading="lazy";im.addEventListener("error",()=>im.replaceWith(element("div","card-art","Image unavailable")));art.replaceChildren(im);}
      article.append(art);
    }
    const body=element("div","card-body");
    body.append(element("span","tag",kind==="portfolio"?r.industry.replaceAll("-"," "):"Receiving FFL / reconfirm"));
    body.append(element("h3","",kind==="portfolio"?r.title:r.name));
    body.append(element("small","",kind==="portfolio"?r.name+" · "+r.service:r.city+", "+r.state+" "+r.zip));
    body.append(element("p","",kind==="portfolio"?r.summary:(r.policy||"Contact dealer directly to reconfirm transfer terms.")));
    body.append(element("small","",kind==="portfolio"?(r.evidence||"Professional-reported; independent verification not established"):(r.updated?"Last acceptance check: "+r.updated:"Check date not supplied")));
    if(kind==="ffl"){
      const a=element("a","action","Ask Area 33 about this dealer ↗");
      a.href="mailto:area33armory@mail.com?subject="+encodeURIComponent("Receiving FFL inquiry: "+r.name)+"&body="+encodeURIComponent("Please confirm whether "+r.name+" in "+r.city+", "+r.state+" can receive the proposed transfer. No shipment is authorized.");
      body.append(a);
    }
    article.append(body);return article;
  }
  function draw(){
    const q=txt(byId("keyword").value,100).toLowerCase();
    const filter=txt(byId("filter").value,80).toLowerCase();
    const shown=items.filter(r=>{
      const fields=kind==="portfolio"?[r.title,r.name,r.service,r.summary,r.location]:[r.name,r.city,r.zip,r.state];
      const okQ=!q||fields.some(v=>v.toLowerCase().includes(q));
      const okFilter=!filter||(kind==="portfolio"?r.industry===filter:r.state.toLowerCase()===filter);
      return okQ&&okFilter;
    });
    results.replaceChildren(...shown.slice(0,60).map(makeCard));
    results.hidden=!shown.length;
    empty.hidden=!!shown.length;
    byId("empty-title").textContent=items.length?(kind==="portfolio"?"No matching published projects.":"No matching confirmed partner records."):(kind==="portfolio"?"No public portfolios yet.":"No confirmed transfer partners published.");
    status.textContent=shown.length+" "+mode.noun+" shown · "+items.length+" approved records in the published directory"+(shown.length>60?" · Showing first 60":"");
  }
  byId("directory-form").addEventListener("submit",e=>{e.preventDefault();draw();});
  try{
    const r=await fetch(mode.file,{headers:{"Accept":"application/json"},credentials:"omit",cache:"no-store"});
    if(!r.ok)throw Error("Directory unavailable");
    const body=await r.json();
    if(!body||body.schema!==mode.schema||!Array.isArray(body.items)||body.items.length>100000)throw Error("Invalid public manifest");
    items=body.items.map(kind==="portfolio"?cleanPortfolio:cleanDealer).filter(Boolean);
    draw();
  }catch{
    empty.hidden=false;results.hidden=true;
    status.textContent="Public directory is not available. No substitute or sample records are shown.";
    byId("empty-title").textContent="Directory unavailable.";
    byId("empty-text").textContent="Please use the official resources linked below or contact Area 33. Private Randbeck records are not accessible from this website.";
  }
})();
