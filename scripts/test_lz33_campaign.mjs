import assert from "node:assert/strict";
import fs from "node:fs";
import {DEALS_SCHEMA,validatePublicDeals} from "../assets/deals-public-contract.mjs";
import {LZ33_BRAND,selectLz33,lz33CampaignDraft} from "../assets/lz33-campaign.mjs";

const now=Date.parse("2026-11-09T15:00:00Z");
const base={
 publicId:"deal-test-ruger-one",productId:"ruger-precision-308-gen1",
 headline:"Owner-approved example",description:"Sample verified listing only, not a real promoted item.",
 label:"Verified Offer",offerTerms:"Destination quote required; receiving FFL transfer fee separate.",
 ownerApproved:true,exactProductReviewed:true,mediaRightsReviewed:true,
 publicOfferReviewed:true,inventoryVerified:true,termsVerified:true,
 reviewedAt:"2026-11-09T14:00:00Z",expiresAt:"2026-11-10T14:00:00Z"
};
const second={...base,publicId:"deal-test-ruger-two",headline:"Second illustrative listing"};
const manifest=items=>({schema:DEALS_SCHEMA,items});
assert.equal(LZ33_BRAND.name,"LZ 33");
assert.equal(LZ33_BRAND.expanded,"Landing Zone 33");
assert.equal(selectLz33(validatePublicDeals(manifest([]),{now})).primary,null,"No public promotions means no hero deal");
assert.equal(lz33CampaignDraft(null).publishable,false,"Empty preview cannot send");
assert.doesNotMatch(lz33CampaignDraft(null).body,/\$[0-9]/,"No fabricated prices");
const checked=validatePublicDeals(manifest([base,second]),{now});
assert.equal(checked?.length,2);
const chosen=selectLz33(checked);
assert.equal(chosen.primary?.productId,base.productId);
assert.equal(chosen.justLanded.length,0,"Never duplicate the same product across LZ33 placements");
assert.equal(chosen.primary?.approved,true);
const draft=lz33CampaignDraft(chosen.primary);
assert.match(draft.subject,/LZ 33 \| Just landed/);
assert.match(draft.body,/Owner-approved example|Sample verified listing/);
assert.equal(draft.publishable,false,"Preview never sends");
assert.equal(selectLz33([{...checked[0],approved:false}]).primary,null);
assert.equal(validatePublicDeals(manifest([{...base,ownerApproved:false}]),{now}),null);
assert.equal(validatePublicDeals(manifest([{...base,expiresAt:"2026-11-08T15:00:00Z"}]),{now}),null);
const home=fs.readFileSync(new URL("../index.html",import.meta.url),"utf8");
const ui=fs.readFileSync(new URL("../assets/featured-opportunities-ui.js",import.meta.url),"utf8");
const manifestFile=JSON.parse(fs.readFileSync(new URL("../assets/deals-public.json",import.meta.url),"utf8"));
assert.deepEqual(manifestFile,{schema:DEALS_SCHEMA,items:[]},"No fake public deals published");
assert.match(home,/id="lz33"/);
assert.match(home,/id="lz33-hero-headline"/);
assert.match(home,/id="lz33-email-preview"/);
assert.match(home,/Just Landed\./);
assert.doesNotMatch(home,/hero-feature-photo|href="#featured-opportunities">Deals &amp; Specials/);
assert.match(ui,/selectLz33\(deals\)/);
assert.match(ui,/lz33CampaignDraft\(landingForEmail\)/);
assert.equal((ui.match(/fetch\("assets\/deals-public\.json"/g)||[]).length,1,"One shared source for all three promotions");
assert.doesNotMatch(ui,/sendMail|mail\.send|fetch\(["']https:|Authorization:|localStorage|sessionStorage/);
console.log("LZ33: single reviewed manifest powers one primary, nonduplicated additional offers and unsent owner email.");
