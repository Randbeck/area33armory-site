# Multi-industry Passport and FFL Finder — development foundation

This is the Area 33 public website on the site-refresh-v1 branch; no live deployment.

**Built:** search/filter interface for publicly approved portfolios across firearm service, automotive, construction/home services, fabrication and other specialties; curated confirmed receiving-FFL partner search. Data manifests ship intentionally empty. No fake work, reviews or accepting dealers are shown.

The Python publication script produces a restricted public JSON manifest from a **separately curated private input** only when the user/technician have consented to each individual portfolio and a human has reviewed content and image rights. FFL partner publication requires consent to the directory, recently confirmed transfer acceptance (<=60 days) and license status review (<=30 days). Publication does not authorize shipping.

Commands from repository root:

python scripts/test_publish_public_directories.py

When real and individually approved private input records are available, review then run:
python scripts/publish_public_directories.py --mode portfolio --input PRIVATE_INPUT.json --output assets/passport-public.json --publish

or:
python scripts/publish_public_directories.py --mode ffl --input PRIVATE_INPUT.json --output assets/ffl-public.json --publish

The private input MUST remain outside GitHub. Review and approve the sanitized output before separately committing it. Automatic publication, cache revocation, live ATF roster import and a secure inquiry backend are not yet implemented. This is neither a full nationwide FFL finder nor a live Passport marketplace.

Public Passport entries use industry-neutral work and verification concepts. No customer identity or firearm serial should be disclosed. Individual projects can be retracted in a future authenticated publisher with cache invalidation.

The July 6, 2026 ATF withdrawal means eZ Check does not automatically replace required transferee-license documentation. See https://www.atf.gov/rules-and-regulations/rulemaking-notices/licensee-ez-check-verification-transfers-withdrawing-direct-final-rule and 27 CFR 478.94.
