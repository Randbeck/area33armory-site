# Area 33 Workshop — Powered by Randbeck

**Product direction:** Owner-approved October 26, 2026. **Status:** Roadmap / architecture only; Workshop, Project Companion and Passport-connected workflows are not built or live.

## Positioning
Area 33 Workshop is the customer-facing, mobile-first educational and service companion. Randbeck Intelligence provides shared, evidence-backed product identity, approved references, reasoning, workflow orchestration and publication controls. The system must be reusable later for other industries or professional deployments without copying the core.

Do not replace normal catalog browsing or force interactive tools. Offer Workshop as a distinct opt-in destination, with a straightforward route back to standard product search, contact and services.

## Primary experiences

### 1. Ask the Workshop
- Natural-language firearms and gunsmithing Q&A for **general education**, terminology, product identification, routine care principles, manufacturer manual discovery and non-invasive troubleshooting triage.
- Evidence card with source, date, exact-model applicability, limitations, conflicts and certainty.
- Clarifying questions only when meaningful; photo upload for possible identification with clear uncertainty (do not claim model identification from resemblance alone).
- Distinguish educational observations from safety-critical maintenance, repair or functional tests. Escalate potentially unsafe symptoms and modifications to manufacturer or qualified professional; do not fabricate model-specific repair/installation steps.

### 2. Learning Center
- Browse/search curated illustrated lessons, technical drawings, machining fundamentals using inert practice materials, measurement and tolerances, workshop safety, maintenance recordkeeping, tool familiarity and knowledge checks.
- All technical content versioned, source-backed, license-reviewed, with accessible imagery and clear skill/prerequisite labels.
- Structured learning progress is opt-in, private and portable.

### 3. Project Companion
- Create a project with type, goal, product-model reference if available, evidence references, project stage and a safety review state.
- Document measurements, photos, diagrams, tool inventories, observations, notes, checklists and changes. Separate user-entered notes from professionally verified claims.
- Start, save, resume, export, close and request professional review. Never silently treat completion of a checklist as certification of safe operation.
- Safe initial templates: inspection intake, service-history documentation, parts-identification research, non-firearm machining practice project and technical drawing/tolerance study.
- Safety-critical operations and restricted modifications go to appropriate professional support; no unsupported operational steps or automatic compatibility/legality certification.
- No public storage of confidential owner/customer data. File attachments use authenticated hosting, virus scanning, access authorization and retention policies.

### 4. Firearms Passport handoff
- Shared *catalog model identity* and separately permissioned *individual-item* identity. UPC/MPN/model data does not uniquely identify a physical firearm.
- Optional, authenticated links between project records and authorized Passport service/inspection timeline entries after explicit user action and appropriate verification.
- Differentiate self-reported observations, shop-supplied records and independently reviewed events. Audit source, authorization, timestamp, corrections/retractions and who can see each entry.
- A QR/code is a discovery/claim path only and does not prove ownership or reveal records to unauthenticated visitors. No public owner/serial-number registry or automatic share.
- Passport does not block Workshop or catalog launch.

## Delivery stages (substantial increments, not individual cosmetic tasks)

**W1 — Workshop educational MVP**
- Public landing page with guides, informational Q&A intake and clear escalation pathways, without falsely representing an AI backend as connected.
- Fast search across genuinely approved educational content, accessibility/mobile QA, author/source attribution.
- *Exit gate:* accurate content and customer messaging; no unreviewed functional guidance or private data storage.

**W2 — Randbeck Q&A service**
- Authenticated or appropriately rate-limited service hosted off static GitHub Pages; citations, content scopes, confidence, source freshness, privacy protections, dangerous-symptom escalation and tests.
- *Exit gate:* high-quality reviewed answer corpus, repeatable evaluations and security boundaries, not just a chat UI.

**W3 — Project Companion MVP**
- Private project persistence, user-controlled exports, safe template library, attachment permissions, review/escalation, activity history and meaningful save/resume experience.
- *Exit gate:* complete user journey and access-control tests including media lifecycle and deletion.

**W4 — Permissioned Passport bridge**
- Explicit opt-in and authorization-scoped record linking, correction workflows, audit trail and separation of model from physical-item identity.
- *Exit gate:* owner privacy and cross-user/tenant isolation tests; no anonymous ownership exposure.

**W5 — Rich interactive learning**
- Rights-cleared diagrams, hotspots, approved multi-angle visuals, optional guided educational experiences and optional professional workflows.
- *Exit gate:* substantive educational value, rights proof and accessibility; never require 3D to use Workshop.

## Shared API boundaries (proposed, not implemented)
- Public catalog: approved product identity/specifications only.
- Workshop knowledge: curated educational content plus source provenance; no private dealer pricing.
- Project service: authenticated private CRUD, tenant/user-scoped attachments and audit history.
- Passport service: item-scoped permission checks, explicit linking, reader grants, retractions and event provenance.
- Never expose dealer costs, supplier feeds, NICS/4473 data, raw credentials, other customers' records or internal reasoning artifacts to public clients.
- Keep secrets and authentication server-side; GitHub Pages is not a private backend.

## Initial questions worth deferring until decision gates
- Whether professional shops get their own white-labeled Randbeck Workshop.
- Which manuals/images have confirmed publication and reuse rights.
- Whether records require paid accounts and what hosting/storage costs are acceptable.
- Which legally reviewed services and transaction paths Area 33 will ultimately support.

## Measures of success
A visitor can find a trustworthy learning resource, record a safe planning project, request help and return to their standard catalog journey without being pushed into an interactive experience. Later, an authorized user can attach a professionally supported record to Passport without disclosing ownership or internal dealer data.

**Release control:** Develop only on `site-refresh-v1`; do not merge to `main`, publish or promise a live feature without explicit owner approval.


## Shared identity dependency (approved)
Before W3 private project persistence and W4 Passport linking, implement an Area 33 Account identity service governed by `CUSTOMER_IDENTITY_MARKETING_ROADMAP.md`. Guest learning and public guides (W1) remain available without login. Marketing subscription is a **separate optional consent** and must not be required for account creation, project saving, or Passport access.


## Randbeck ID cross-app account agreement
Workshop saved projects should rely on the shared Randbeck ID subject and application-specific permission scopes. The Area 33 label remains **Area 33 Account**, but authenticated customers may access participating Randbeck products with a common secure sign-in. Passport record linking requires explicit customer permission and independently checked authorization, not merely possession of the account or an existing Loadout. See `RANDBECK_ID_PASSPORT_FLOW.md`.
