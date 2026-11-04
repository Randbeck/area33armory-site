# Standard browsing first; Experience Lab optional
Decision implemented in the draft branch.

- `catalog.html` remains the ordinary browsing destination, with search, filters, informational cards, detail dialog and comparison.
- An explicit optional Experience Lab invitation appears above catalog results; each future approved result card has an optional lab link.
- The lab itself is not required to understand specs or make an inquiry. Its visual media can remain unavailable while the standard catalog functions.
- No automatic redirect or media download from the standard page. Current catalog data remains disconnected until publication/security gates are met.
- Follow-up when approved catalog records exist: carry an opaque **public** product ID into the lab, deep-link only if matching approved media exists, and return users to the relevant standard product. Do not expose internal identifiers or compatibility assumptions.

Testing before release: keyboard navigation, touch, screen readers, mobile performance, unavailable interactive assets and standard-only journeys. Production `main` must remain unchanged until approval.
