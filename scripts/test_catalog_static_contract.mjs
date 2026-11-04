import assert from "node:assert/strict";
import fs from "node:fs";
import {sanitizeCatalogManifest,filterPublicCatalog} from "../assets/catalog-static-contract.mjs";

const empty=JSON.parse(fs.readFileSync(new URL("../assets/catalog-public.json",import.meta.url),"utf8"));
const clean=sanitizeCatalogManifest(empty,{baseUrl:"https://area33armory.com/catalog.html"});
assert.ok(clean);
assert.deepEqual(clean.items,[]);
assert.equal(empty.schema,"area33.catalog.public.v1");

const item={
  id:"catalog_0123456789abcdefabcd",manufacturer:"Example",model:"Exact model",
  variant:"Black",category:"Holsters",product_type:"accessory",
  specifications:[],evidence:[{source_label:"Verified dealer product details",checked_at:"2026-11-04"}],
  images:[{url:"assets/approved/catalog/catalog_0123456789abcdefabcd/view-01.jpg",
           alt:"Example black holster",rights:"approved"}],
  publication_updated_at:"2026-11-04T22:00:00Z"
};
function body(items){return {...empty,items};}
const present=sanitizeCatalogManifest(body([item]),{baseUrl:"https://area33armory.com/catalog.html"});
assert.ok(present);
assert.equal(present.items.length,1);
assert.equal(present.items[0].images[0].url,
             "https://area33armory.com/assets/approved/catalog/catalog_0123456789abcdefabcd/view-01.jpg");
assert.equal(filterPublicCatalog(present.items,{query:"example holster"}).length,1);
assert.equal(filterPublicCatalog(present.items,{query:"holster nonexistent"}).length,0);
assert.equal(filterPublicCatalog(present.items,{category:"Other"}).length,0);
assert.equal(filterPublicCatalog(present.items,{productType:"accessory",brand:"exam"}).length,1);
assert.equal(sanitizeCatalogManifest(body([{...item,source_sku:"PRIVATE_RSR_SKU"}])),null);
assert.equal(sanitizeCatalogManifest(body([{...item,images:[{...item.images[0],rights:"pending"}]}])),null);
assert.equal(sanitizeCatalogManifest(body([{...item,images:[{...item.images[0],
  url:"assets/approved/catalog/catalog_0123456789abcdefabcd/../../hidden.jpg"}]}])),null);
assert.equal(sanitizeCatalogManifest(body([{...item,images:[{...item.images[0],
  url:"https://third-party.example/photo.jpg"}]}])),null);
assert.equal(sanitizeCatalogManifest(body([{...item,images:[{...item.images[0],
  url:"assets/approved/catalog/catalog_ffffffffffffffffffff/view-01.jpg"}]}])),null);
assert.equal(sanitizeCatalogManifest(body([item,item])),null);
assert.equal(sanitizeCatalogManifest(body([{...item,product_type:"unknown"}])),null);

const html=fs.readFileSync(new URL("../catalog.html",import.meta.url),"utf8");
const js=fs.readFileSync(new URL("../assets/catalog.js",import.meta.url),"utf8");
assert.match(html,/type="module" src="assets\/catalog\.js"/);
assert.match(js,/STATIC_CATALOG_PATH = "assets\/catalog-public\.json"/);
assert.match(js,/credentials:"omit"/);
assert.doesNotMatch(js,/localStorage|sessionStorage|Authorization:/);
console.log("Area 33 approved-only catalog static contract: validated.");
