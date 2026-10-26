# Area 33 Customer Identity & Marketing Permissions

**Status:** Approved planning direction, not implemented. Provider, costs, legal review, and release remain gated.

## Product decision
- One optional Area 33 Account, powered by Randbeck, for the standard catalog, Experience Lab, Workshop/Project Companion, and permissioned Passport.
- **Guest browsing always remains available.** No account required to read public product/education pages.
- Creating an account does **not** automatically subscribe to marketing; people may opt into newsletters without creating accounts.
- Marketing is not a condition of using saved features. No prechecked marketing boxes or bundled consent.

## Release stages
**I1 — Provider and architecture review**: Evaluate hosted authentication (email verification, passkeys or passwordless options, MFA/recovery, pricing, session policies, privacy controls) and firearms-industry-compatible email service providers (acceptable use policy, deliverability, unsubscribes, pricing, list portability). No vendor is presumed approved. Define first-party privacy notice and applicable marketing compliance review.

**I2 — Secure identity foundation**: Managed authentication via secured backend; email verification and protected user identifiers; session renewal/logout/recovery; rate limiting, CSRF and abuse protection; consent-independent account creation; audit logs and user-controlled deletion. Do not store passwords or secrets in GitHub Pages.

**I3 — Customer dashboard / saved features**: Saved product IDs and comparisons; optional Experience Lab interests; Workshop progress and private projects. Verified access policies and export/delete workflows. Private data remains server-side and is not accessible across customers or dealer tenants.

**I4 — Marketing consent and subscription**: Explicit unchecked opt-in, distinct from account terms, with consent version, timestamp, source, proof and withdrawal history. Double opt-in where supported or required. Provide unsubscribe link in every marketing email and preference center; implement suppression promptly and preserve minimal suppression records. Transactional/security mail must not be disguised marketing. No unsolicited marketing based on project, service history, ownership or Passport content.

**I5 — Passport access integration**: Separately gated scoped permissions and explicit grants to private item/service records. QR access never equates to ownership. Test tenant isolation and revocation before release.

## Minimum proposed data boundaries
- Identity service: opaque user ID, verified email status, minimal profile and authentication provider reference.
- Customer saved-items service: user-scoped saved published-product IDs; no dealer cost or private supplier offers.
- Marketing preference service: subscription state, purpose/topic, consent provenance, timestamps, withdrawal and provider sync status. Marketing exports only active consenting subscribers with limited necessary attributes.
- Passport: separate item-scoped records and authorization; marketing system cannot query them.
- Do not copy private firearms ownership records, NICS/4473 information or private gunsmithing/service notes into marketing tools.

## UX
- Header: Sign in / My Area 33, without blocking guest exploration.
- Saved features prompt: explain why a free account helps, and allow skipping.
- Account creation: email-based registration and verification; independent unchecked marketing checkbox, clear Privacy Policy and Terms links.
- Email-only subscription: separate voluntary form with purpose and unsubscribe terms.
- User preferences: subscription topics, pause/unsubscribe, export/delete data, account sign out.
- Clear truthfulness: no fake working login or accepting real information on a static-only preview.

## Acceptance gates
Security review; service provider firearm-category acceptable-use confirmation; applicable email/privacy legal review (including CAN-SPAM and relevant state laws); full consent audit and opt-out test; accessible forms; abuse/rate-limit tests; email deliverability; user/tenant permission tests; recovery and data deletion; owner approval. No live collection until implementation and policies approved.

**Deployment:** all work in `site-refresh-v1` until explicit approval. GitHub Pages hosts public UI only.


## Shared Randbeck ID decision
Use a single Randbeck ID as the identity foundation across participating platforms while retaining the **Area 33 Account** label for Area 33 visitors. Guest browsing and independent optional marketing consent remain required. The optional Passport invitation occurs only after a verified completed transaction/transfer, never merely at Loadout quote request. See `RANDBECK_ID_PASSPORT_FLOW.md`.
