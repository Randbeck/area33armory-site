# Randbeck — Ten Connected Opportunities and First Build Stage
Status: Product proposal and scoped implementation plan. Nothing herein is live.

## Ten opportunities
1. Opportunity Radar — observe approved distributor/promotional intelligence privately; rank opportunities by evidence quality and all-in economics.
2. EVA Follow-Up Desk — capture phone/web inquiry, answer supported FAQs, confirm callback contact, record consent and prepare owner follow-up.
3. Intelligent Quote Builder — prepare an approval-required customer quote using exact public product identity and private landed-cost analysis.
4. Visual Inspector — image-based possible identification with visible uncertainty, supported references and professional inspection escalation.
5. Service Scheduling — capture requests, propose real published slots, and avoid false confirmed bookings.
6. Passport Service Records — opt-in, provenance-backed, item-scoped service timeline entries with authorization checks.
7. Randbeck Learning Coach — source-backed educational content, progress, quizzes and project learning.
8. Randbeck for Other Businesses — tenant-isolated industry-neutral assistant services, with Area 33 the pilot.
9. Customer Journey Tracker — signed-in customer sees real statuses (inquiry received, review, response ready); EVA reads approved status only. No invented transitions.
10. Randbeck Business Autopilot — owner-oriented summary, risks, proposed actions and approval queue; no unsupervised financial, public, compliance or customer commitments.

## Shared Randbeck Action Engine
Event schema: event_id, tenant_id, type, occurred_at, actor, data_classification, correlation_id, causation_id, idempotency_key. Audit and minimize payloads. Authorization and tenant isolation apply to all event handlers.
Action proposal: proposal_id, tenant_id, source_event_id, action_type, evidence_refs, policy_version, confidence/status, requested_by, approval_state, approved_by, approved_at, execution_status, result_refs. Clearly separate **observation**, **suggestion**, **approved action**, and **completed result**.
Default-deny: outbound communications, customer-facing quotes, bookings, price/availability guarantees, order changes, Passport updates and regulated-service conclusions must have explicit permission/approval policies before execution.
Customer status changes are driven only by real validated events with provenance; transitions are audited, with explicit unknown/unavailable states.

## First substantial delivery: Inquiry-to-follow-up vertical slice
1. Intake contract for EVA call summaries and website inquiries: inquiry ID, channel, customer-provided contact, preferred callback times, question, consent/disclosure flags, timestamp, and state. Never assume caller ID proves identity.
2. Validation, contact minimization and a documented retention policy; no collection by the public static site until secured server-side handling is implemented.
3. Private owner inbox in Randbeck Executive Suite: new, needs attention, waiting, resolved. Evidence and actionable notes with clear priorities.
4. Explicit status workflow that can later power Customer Journey Tracker: received -> under_review -> response_ready -> closed; no automatic claimed completion.
5. Approval-required response drafts (with channel consent checks) and callback tasks. No unapproved automated sales messages.
6. Integration tests for cross-tenant access, duplicate webhook delivery, missing/malformed contact, sensitive content, replay, source evidence and permission failures.
7. Add quote-preparation from existing verified Randbeck product data only after inquiry identity and review controls are reliable.
8. Pilot with simulated calls/test inquiries before phone carrier routing or real customer data.

## Architecture and dependencies
Randbeck shared services: identity, evidence & product normalization, notification preferences, Action Engine and tenant-scoped inquiry persistence. EVA is a channel-specific agent with limited tools. Area 33 website is a customer-facing pilot, not a separate intelligence fork. GitHub Pages hosts only static presentation: private workflow services must be deployed separately with authentication, audit and operational safeguards.

## Success and decision gates
- A simulated customer inquiry arrives exactly once, can be triaged, assigned for callback, and marked resolved with audit evidence.
- No external communication or quote confirmation happens without configured policy and required approval.
- Customer Journey Tracker displays only valid event-backed statuses.
- Business Autopilot briefing lists authentic tasks and sources, not invented metrics.
- Provider selection, phone/voice usage charges, marketing/compliance review, and live activation require owner approval.

Build order: inquiry intake and EVA Follow-Up Desk -> owner Action Engine queue -> customer status view -> quote drafting -> cross-tenant multi-business service. Parallel work only when it materially reduces launch time.
