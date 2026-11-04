# Randbeck ID — Shared Identity and Opt-In Passport Claim Architecture

**Decision:** Approved as platform architecture. **Implementation:** Not connected; no credentials, customer records or Passport entries are created by this document.

## Platform-wide identity
Area 33 displays **Area 33 Account** in customer-facing UI. **Randbeck ID** is the shared identity behind Area 33, future Randbeck Workshop and Passport experiences, with standard federated authentication / authorization patterns (OIDC where appropriate), not copied user passwords or independently duplicated accounts.

One sign-in is convenient but must **not** grant access to every service's data. Each app obtains narrowly scoped authorization; Passport item records and service-provider records require separate, explicit permission checks. Multi-tenant isolation and least-privilege scopes must be enforced server-side.

## Customer experiences
- **My Vault**: saved favorites / wish list; never represents legal custody or verified ownership.
- **My Loadout**: pending customer selections for an availability/quote inquiry; no payment, reservation, purchase or guaranteed inventory.
- **My Workbench**: educational and project documentation under account permissions.
- **My Passport**: permission-scoped service history and item records. Can be separate application using the shared identity.
- Anonymous visitors can browse public pages and build a transient Loadout; login enables persistence. Promotional marketing consent is separate from authentication.

## Loadout → quote request → completed purchase → optional Passport
1. Customer adds items to Loadout and sends a **Request Quote & Availability** inquiry. This is not checkout, an order, ownership proof, a binding purchase or a stock reservation.
2. Area 33 reviews sources, product identity, availability, applicable transfer restrictions, and a verified customer quote; the prospective customer can accept/decline in a later authorized process.
3. Only after a separately verified completed sale and required transfer may the system offer an item-specific Passport invitation. Do not create an invitation solely from a Loadout or unfulfilled order.
4. Invitation states clearly what verified item fields would be copied, what will remain private, which evidence backs them, and who could access the new record. Default is **Not now**.
5. An authenticated customer chooses **Add to Passport**, verifies the individual item and claims/authorizes the appropriate connection, then explicitly confirms creation. No automatically inferred ownership, no automatic upload of serial numbers, no sharing with marketing.
6. Optional later handoff: a qualified participating service provider may offer a reviewed maintenance report for inclusion; customer explicitly authorizes linking the service event, with source, permissions and correction history.
7. Support decline, later enrollment, record correction, access revocation and exports. A QR/passport code does not verify ownership.

## Identity model and data boundaries
- `account_id`: opaque global subject ID (never email or serial number as primary identifier).
- `application_grant`: application, scope, consent version, issued_at, revoked_at, purpose, actor.
- `saved_item`: account_id and approved public product_id; distinguish preference from purchase or ownership.
- `loadout`: quote-interest records, quantities and inquiry status; no regulated sale state until separate workflow.
- `verified_transaction`: restricted server-side sale/transfer evidence reference; not exposed to marketing or anonymous clients.
- `passport_invitation`: random single-purpose token, hashed server-side with expiry, linked to verified transaction and intended account; replay protection and revocation.
- `passport_record`: separate authorized per-item record ID, with provenance and immutable event audit; never infer record from model UPC alone.
- `marketing_preference`: independent optional newsletter permission; no access to purchase history, regulated records, Passport or Workshop notes.

## Threat and compliance review gates
- OIDC redirect URI / PKCE / token audience validation; secure sessions; account linking safeguards; MFA where appropriate and recovery flow.
- Signed or server-validated transaction state; verified item identifiers and explicit opt-in; invitation replay/misdelivery prevention.
- Explicit authorization for professional service events; access revocation and correction/retraction.
- Privacy, retention/deletion, vendor policy, firearms and transfer-law review. Do not put NICS/4473 data or sensitive serial/owner records into marketing systems.
- No custom password database or account/Passport authorization logic running solely on static GitHub Pages.
- Add cross-app integration tests and negative authorization tests before any account feature is made live.

## Delivery
**R1 — Architecture and UI language** (this stage): approve service terminology, boundaries, user journeys, minimal public states and no-payment quote request distinction.

**R2 — Managed authentication proof-of-concept**: select eligible provider, secure backend, scoped sign-in and logout, authorization tests, no production user data.

**R3 — Saved experiences**: signed-in Vault, Loadout and Workbench persistence, export/deletion and account preferences.

**R4 — Quote workflow**: inquiry submission with review status, exact public identity references and customer notices; transactions remain separate from inquiry.

**R5 — Passport optional post-transfer enrollment**: invitation and item verification with explicit consent, auditable private record creation and service-event handoffs.

**R6 — Production readiness**: security testing, privacy review, email consent and unsubscribe compliance, customer support procedures, failure recovery, and explicit owner release approval.

Nothing in the current approval authorizes creating production accounts, launching checkout, or collecting regulated customer data.
