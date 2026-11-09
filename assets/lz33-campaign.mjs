/* LZ 33 — one approved public promotion, three surfaces.
   Input must come from validatePublicDeals(), never a raw distributor record.
   No invented prices, discounts, purchase links or automatic email sending. */
export const LZ33_BRAND = Object.freeze({
  name: 'LZ 33',
  expanded: 'Landing Zone 33',
  tagline: 'Where the best deals land.'
});

export function selectLz33(validatedDeals) {
  if (!Array.isArray(validatedDeals)) return Object.freeze({ primary: null, justLanded: [] });
  const seenProducts = new Set();
  const accepted = [];
  for (const deal of validatedDeals) {
    if (!deal || deal.approved !== true || typeof deal.productId !== 'string'
        || typeof deal.headline !== 'string' || typeof deal.offerTerms !== 'string'
        || typeof deal.description !== 'string') continue;
    if (seenProducts.has(deal.productId)) continue;
    seenProducts.add(deal.productId);
    accepted.push(deal);
  }
  return Object.freeze({ primary: accepted[0] || null, justLanded: Object.freeze(accepted.slice(1, 8)) });
}

export function lz33CampaignDraft(primary) {
  const footer = 'Area 33 delivered pricing requires a verified destination-specific quote. The receiving FFL transfer fee is separate. Subject to applicable law and final verification.';
  if (!primary || primary.approved !== true) {
    return Object.freeze({
      subject: 'LZ 33 | Next landing coming soon',
      heading: 'LZ 33 · Landing Zone 33',
      body: 'Nothing has cleared the Area 33 public promotion review yet. This is an internal layout preview, not a live offer.',
      footer,
      publishable: false
    });
  }
  return Object.freeze({
    subject: 'LZ 33 | Just landed: ' + primary.headline,
    heading: primary.headline,
    body: primary.description + '\n\n' + primary.offerTerms,
    footer,
    publishable: false // Draft construction never authorizes mailing.
  });
}