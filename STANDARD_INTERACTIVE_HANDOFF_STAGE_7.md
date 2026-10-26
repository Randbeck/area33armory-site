# Stage 7 — Standard browsing ↔ optional Experience Lab

- Catalog cards and detail dialog provide optional Experience Lab links with an opaque public product ID in the URL. No internal distributor IDs or raw source records.
- The Experience Lab offers a prominent return path. It only auto-selects media for an exact ID already published in the rights-approved local manifest; otherwise shows an unavailable disclosure and retains standard browsing as the fallback.
- The catalog correctly invalidates in-flight search results when a filter/query changes, before stale response data can mutate the result state. No new network endpoint is connected.
- Standard browsing remains fully independent of multi-angle media and optional interactive controls.

Still outstanding: approved public catalog backend, browser automation and full accessibility audit, licensed exact-product photographs, publication approval. Live main must not change.
