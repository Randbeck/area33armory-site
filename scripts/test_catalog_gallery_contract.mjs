import assert from "node:assert/strict";
import fs from "node:fs";
import {galleryAllowed,createApprovedGallery,clampGalleryZoom,galleryPointerPercent}
  from "../assets/catalog-gallery.mjs";
import {sanitizeCatalogManifest} from "../assets/catalog-static-contract.mjs";

const id="catalog_0123456789abcdefabcd";
const base="https://area33armory.com/catalog.html";
const path=index=>"assets/approved/catalog/"+id+"/view-0"+index+".jpg";
const item={
  id,manufacturer:"Example",model:"Exact approved product",variant:"Black",
  category:"Holsters",product_type:"accessory",presentation_mode:"image",
  description:"Original approved information",
  specifications:[],evidence:[{source_label:"Human review",checked_at:"2026-11-07"}],
  publication_updated_at:"2026-11-07T08:00:00Z",
  images:[1,2,3].map(i=>({url:path(i),alt:"Approved angle "+i,rights:"approved"}))
};
const publicDoc={schema:"area33.catalog.public.v1",
  coverage:{description:"Only owner-approved items"},items:[item]};
const sanitized=sanitizeCatalogManifest(publicDoc,{baseUrl:base});
assert.ok(sanitized);
const product=sanitized.items[0];
globalThis.location={origin:"https://area33armory.com"};
assert.equal(galleryAllowed(product),true);
assert.equal(product.images.length,3);
assert.equal(galleryAllowed({...product,presentationMode:"text_only"}),false);
assert.equal(galleryAllowed({...product,images:[]}),false);
assert.equal(createApprovedGallery({...product,presentationMode:"text_only"}),null);
assert.equal(createApprovedGallery({...product,images:[]}),null);
assert.equal(galleryAllowed({...product,id:"catalog_ffffffffffffffffffff"}),false);
assert.equal(galleryAllowed({...product,images:[
  {url:"https://unlicensed.example"+new URL(product.images[0].url).pathname,alt:"Unlicensed"}
]}),false);
assert.equal(galleryAllowed({...product,images:[
  {url:"https://area33armory.com/assets/approved/catalog/catalog_ffffffffffffffffffff/view-01.jpg",alt:"Wrong ID"}
]}),false);
assert.equal(galleryAllowed({...product,images:[
  {url:"https://area33armory.com/assets/approved/catalog/"+id+"/view-01.jpg?private=1",alt:"URL params"}
]}),false);
assert.equal(galleryAllowed({...product,images:[
  {url:"https://area33armory.com/assets/approved/catalog/"+id+"/../private.jpg",alt:"Traversal"}
]}),false);
assert.equal(galleryAllowed({...product,images:[
  {url:"file:///mnt/data/private.jpg",alt:"Local"}
]}),false);
assert.equal(galleryAllowed({...product,images:[
  {url:"https://area33armory.com/assets/approved/catalog/"+id+"/view-01.jpg",alt:""}
]}),false);
assert.equal(sanitizeCatalogManifest({...publicDoc,items:[{
  ...item,images:[{...item.images[0],rights:"pending"}]
}]},{baseUrl:base}),null);
assert.equal(galleryAllowed({
  ...product,images:[{url:"https://area33armory.com/assets/approved/catalog/"+id+"/view-01.jpg",alt:"Approved"}]
}),true);
globalThis.location={origin:"http://localhost:8080"};
const local=sanitizeCatalogManifest(publicDoc,{baseUrl:"http://localhost:8080/catalog.html"});
assert.ok(local);
assert.equal(galleryAllowed(local.items[0]),true);
assert.equal(galleryAllowed(product),false);
delete globalThis.location;

assert.equal(clampGalleryZoom(-25),1);
assert.equal(clampGalleryZoom(0),1);
assert.equal(clampGalleryZoom(2.5),2.5);
assert.equal(clampGalleryZoom(22),4);
assert.equal(clampGalleryZoom(NaN),1);
assert.deepEqual(galleryPointerPercent(20,40,{left:0,top:0,width:100,height:100}),{x:20,y:40});
assert.deepEqual(galleryPointerPercent(-5,200,{left:0,top:0,width:100,height:100}),{x:0,y:100});
assert.deepEqual(galleryPointerPercent(5,5,{left:0,top:0,width:0,height:0}),{x:50,y:50});
const js=fs.readFileSync(new URL("../assets/catalog.js",import.meta.url),"utf8");
const css=fs.readFileSync(new URL("../assets/catalog.css",import.meta.url),"utf8");
const html=fs.readFileSync(new URL("../catalog.html",import.meta.url),"utf8");
assert.match(js,/import \{createApprovedGallery\} from "\.\/catalog-gallery\.mjs"/);
assert.match(js,/if\(item\.images\.length\)\{const gallery=createApprovedGallery\(item\)/);
assert.match(js,/No approved photo is available for this exact product/);
assert.match(js,/Text-only product record\. No manufacturer image rights/);
assert.match(css,/gallery-stage\.hover-zooming \.gallery-hero\{transform:scale/);
assert.match(css,/@media\(hover:none\),\(pointer:coarse\)/);
assert.match(css,/\.gallery-lightbox-stage\{[^}]*touch-action:none/);
assert.match(html,/id="detail-dialog"/);
assert.doesNotMatch(js,/localStorage|sessionStorage/);
assert.doesNotMatch(js,/private_dealer_cost|source_sku|source_image_path/);
assert.deepEqual(JSON.parse(fs.readFileSync(
  new URL("../assets/catalog-public.json",import.meta.url),"utf8")).items,[]);
console.log("Area 33 approved photo gallery: secure path, same origin, hover/touch zoom logic and empty text-only catalog checked.");
