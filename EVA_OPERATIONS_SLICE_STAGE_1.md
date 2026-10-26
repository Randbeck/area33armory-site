# EVA Operations Lab — first executable vertical slice
This commits a **functional, isolated frontend simulation** to `operations-lab.html`, deliberately outside production navigation and marked `noindex,nofollow`.

Built: three fictional intake scenarios; deterministic unique simulated IDs; an interactive owner inbox with statuses, status filters and counts; a human-reviewed response draft; permitted state transitions; local audit chronology; customer-safe status preview; reset. All data is hardcoded fictional and in memory only (lost on reload).

Verified by code inspection of event wiring and finite-state transitions. **Not yet browser-automated or integrated into the FastAPI backend**. The prototype contains no real caller/customer data, does not perform calls, save to a server, persist to browser storage, send messages, authorize real customer accounts or claim a quote. Do not link it from the public live site.

Next actual product stage: implement tenant-scoped inquiry/event models and persistence in the Randbeck backend with idempotency, authentication, permission checks, retention and audit tests; wire this inbox through a private authenticated API. Only then connect EVA transport, notification channels and customer status pages after carrier/service approvals. Never publish or collect live data before privacy and safety review.
