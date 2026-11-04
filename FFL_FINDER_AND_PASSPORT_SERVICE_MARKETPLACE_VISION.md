# Area 33 FFL Finder + Passport Service Portfolio Vision
Updated: November 3, 2026
Status: Owner concept and implementation roadmap, not built or deployed.

## Product direction
Area 33's public site should be an exceptional interactive showroom, not a Gearfire-style catalog. Two complementary products support that experience:
1. An FFL Finder for transfers associated with future lawful sales, if the transaction service is developed and approved.
2. Randbeck Passport as a customer-visible service portfolio and discoverable work-history/reviews platform—something analogous to Angi or Yelp for firearm service professionals, but evidence-based and privacy-preserving.

## Feature A — FFL Finder (public discovery / private fulfillment)
Customer experience:
- Enter ZIP code/city/state and discover nearby potential receiving FFLs using current ATF Federal Firearms Listings and address geocoding.
- Display business name, public address, transfer policy/fee when *verified directly*, telephone, last confirmed/updated date and whether the FFL has opted into the directory.
- Search/filter by distance, accepting transfers, customer rating based on verified transfer experiences (optional later), and hours *only if confirmed*.
- Select a preferred receiving FFL as a *request*, not an automatic shipment approval.
- Show status: selected -> FFL contacted -> accepting confirmed -> license verified -> fulfillment reviewed -> ready for lawful shipment.
- No shipment should be authorized merely because an FFL appears in the public monthly list or a customer selects it.
Operational workflow:
- Obtain required receiving-license documentation and perform ATF eZ Check verification as appropriate, preserve check timestamp and verifying operator, compare shipping/premises details, ensure receiving FFL explicitly agrees to accept shipment, retain applicable records, and confirm current law and shipping policies with a compliance professional.
- Distinguish dealer validity from willingness to accept a transfer, fees and processing times; never invent these fields.
- Prevent private license copies or customer order data from appearing in public search.
Data: licensed dealer ID, ATF dataset version/date, official premises vs public business address, verified contact details, acceptance status and stale-status. Dealer confirmations are not inferred from ATF list.
Legal caveat: ATF's May 2026 proposed direct-final rule to make eZ Check a substitute for a certified license copy under 27 CFR 478.94 was withdrawn July 6, 2026 after comments. Do NOT treat that withdrawn proposal as current authorization. Follow current regulation and ATF guidance. ATF references:
https://www.atf.gov/firearms/tools-and-services-firearms-industry/federal-firearms-listings
https://fflezcheck.atf.gov/FFLEzCheck/
https://www.atf.gov/rules-and-regulations/rulemaking-notices/licensee-ez-check-verification-transfers-withdrawing-direct-final-rule

## Feature B — Randbeck Passport as a service portfolio and trusted discovery network
Concept:
- Customer or prospective customer can find participating professionals, browse an approved portfolio of actual previous work and, optionally, read verified service reviews.
- A professional profile includes service types, publicly verified credentials/business details where available, coverage/availability, samples, galleries, dated work descriptions, documented methods and applicable disclaimers.
- Project cards show before/after photos (rights-cleared), work category, anonymous product identity if approved, date range, verified-by source/workshop, and service outcome without overclaiming safety or performance.
- A Passport may link to an individual product/work-history record, but client ownership and firearm serial numbers are NEVER public by default.
- Private Passport remains private. A technician/shop and customer explicitly approve each individual project's public portfolio publication. The publication copy is separately sanitized. Revocation removes public data and cached indexes on a defined schedule.
- Reviews can be tied to verified service transactions, with fraud protections, moderation, rebuttal mechanisms and transparent scoring (no pay-to-improve-rating).
- Professionals control portfolio membership, but cannot rewrite a verified service history. Distinguish shop-authored descriptions from independent verification.
- Customer profile can collect their own service records in private Passport and opt into publishing an anonymized example; public profiles can attract future clients.
- Permit shops to opt into accepting prospective customer inquiries, with protected contact channels and clear retention/privacy controls.

## Architecture
- Area 33 website: public FFL Finder and Browse Services/Portfolios UI.
- Randbeck Intelligence: canonical product/service facts, service records, evidence, trust signals and publication approval.
- Passport: private work history and customer-controlled permissions; public portfolio is a separate publication artifact.
- An isolated public API or static snapshot contains only approved, minimal fields; never expose operational Randbeck backend, dealer costs, customer identities, serials, private notes or internal supplier data.
- Keep transactional FFL transfer eligibility/compliance separate from portfolio/review ranking to avoid conflating legal status with reputation.

## Build order
1. Interactive showroom is priority: use a genuine, rights-cleared product media set and build authentic interactive experience.
2. FFL Finder discovery with sourced dealer records and explicit 'transfer policy unconfirmed' labels. Validate secure workflows before any shipping feature.
3. Passport opt-in professional portfolios with approved example records and before/after galleries.
4. Trust layer: verified-service reviews, provider discovery, customer inquiries and reputation safeguards.
5. Real checkout/fulfillment only after legal, licensing, payments, transfer, shipping, privacy and hosting reviews.

## Acceptance
- FFL Finder never represents listings as guaranteed accepting dealers and never auto-ships.
- Portfolio never publicizes a customer or serial without affirmative record-specific permission, and allows revocation.
- Provider ratings reflect verified evidence and clearly distinguish unreviewed from poor/negative ratings.
- Public website remains a distinct customer experience, not an internal Randbeck dashboard.
- No change to live main until owner approves.
