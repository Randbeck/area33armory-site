import assert from "node:assert/strict";
import fs from "node:fs";
import {approvedPath,sanitizeShowroomManifest,sanitizeShowroomItem} from "../assets/showroom-contract.mjs";
const frame=angle=>({angle,src:"assets/approved/showroom/record_123456789/"+angle+".webp",alt:"Approved "+angle});
function valid(){
 return {
  id:"record_123456789",manufacturer:"Test brand",model:"Exact item",variant:"",
  status:"published",publication_approved:true,exact_identity_verified:true,
  rights:"approved",rights_source:"Licensed rights source",
  identity_evidence_label:"Exact identity checked",checked_at:"2026-11-04",
  frames:[frame("left"),frame("right")],
  configurations:[{
   id:"option_123456789",label:"Approved attachment appearance",publication_approved:true,media_rights_approved:true,
   exact_accessory_verified:true,pairing_verified:true,alignment_reviewed:true,
   pairing_evidence_label:"Manual evidence review",
   frames:[{...frame("left"),src:"assets/approved/showroom/record_123456789/left-with.webp"},{...frame("right"),src:"assets/approved/showroom/record_123456789/right-with.webp"}]
  }],
  secret_dealer_cost: 1
 }
}
assert.equal(approvedPath("../secret.jpg"),null);
assert.equal(approvedPath("https://example.com/img.webp"),null);
assert.ok(sanitizeShowroomItem(valid()));
assert.equal(sanitizeShowroomItem({...valid(),publication_approved:false}),null);
assert.equal(sanitizeShowroomItem({...valid(),rights:"unclear"}),null);
const foreignBase=valid();foreignBase.frames[0].src="assets/approved/showroom/other_product_123/left.webp";
assert.equal(sanitizeShowroomItem(foreignBase),null);
const foreignConfig=valid();foreignConfig.configurations[0].frames[0].src="assets/approved/showroom/other_product_123/left.webp";
assert.equal(sanitizeShowroomItem(foreignConfig).configurations.length,0);
const clean=sanitizeShowroomItem(valid());
assert.equal(clean.secret_dealer_cost,undefined);
assert.equal(clean.configurations.length,1);
const bad=valid();bad.configurations[0].frames[0].angle="wrong";
assert.equal(sanitizeShowroomItem(bad).configurations.length,0);
assert.deepEqual(sanitizeShowroomManifest({schema:"area33.showroom.v1",items:[]}),[]);
assert.equal(sanitizeShowroomManifest({schema:"wrong",items:[]}),null);
assert.equal(sanitizeShowroomManifest({schema:"area33.showroom.v1",items:[valid(),valid()]}),null);
const publicFile=JSON.parse(fs.readFileSync(new URL("../assets/showroom-public.json",import.meta.url),"utf8"));
assert.equal(publicFile.schema,"area33.showroom.v1");
assert.deepEqual(publicFile.items,[]);
const html=fs.readFileSync(new URL("../showroom.html",import.meta.url),"utf8");
for(const id of ["viewer","product","configuration","compare","split-control","angle","base-image","selected-image","zoom-in","zoom-out"]){
 assert.ok(html.includes('id="'+id+'"'),"Missing interactive element "+id);
}
console.log("Area 33 showroom: access rules, exact-angle pairs and empty-state verified.");
