"use strict";
(function(){
const byId=id=>document.getElementById(id),section=byId("case-study");
if(!section)return;
const before=byId("case-before"),after=byId("case-after"),range=byId("case-range");
const allowed=/^assets\/approved\/[a-zA-Z0-9/_-]+\.(?:png|jpg|jpeg|webp)$/;
const safe=s=>typeof s==="string"&&s.length<=180&&!s.includes("..")&&allowed.test(s);
function split(){const p=Number(range.value);after.style.clipPath="inset(0 0 0 "+p+"%)";byId("case-line").style.left=p+"%";byId("case-pct").textContent=p+"%";}
range.addEventListener("input",split);
byId("case-close").addEventListener("click",()=>{section.hidden=true;before.removeAttribute("src");after.removeAttribute("src");});
document.addEventListener("area33:open-case",e=>{
 const d=e.detail||{};if(!safe(d.before)||!safe(d.after))return;
 before.onerror=after.onerror=()=>{byId("case-status").textContent="One approved photo could not load; please ask the provider for details.";};
 before.src=d.before;after.src=d.after;
 const title=String(d.title||"Approved work").slice(0,150),business=String(d.business||"Participating provider").slice(0,100);
 before.alt="Approved before photograph for "+title;after.alt="Approved after photograph for "+title;
 byId("case-title").textContent=title;byId("case-source").textContent=business+" · published by permission";
 byId("case-status").textContent="Public, client-approved work. Photo comparisons alone do not verify workmanship or safety.";
 range.value="50";split();section.hidden=false;
 section.scrollIntoView({block:"start",behavior:window.matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth"});
});
})();
