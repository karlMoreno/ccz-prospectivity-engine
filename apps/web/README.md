# apps/web

ONE STATIC HTML PAGE: the viewer (E5.3) — MapLibre GL JS + deck.gl loaded from a
CDN with pinned versions and SRI hashes; no npm, no node, no build step, no
framework. It reads the layer catalog E5.1's read-only API serves from a run
directory (`python -m engine.prospectivity.harness`, E5.5) and carries the
honesty surface (E5.4): the claim verdict with its failing preconditions named,
both watermark reasons with their expiry conditions, the uncertainty paired with
every value, and the no-information region marked.

Not built yet — Phase 5 (Alpha Proposal v3 §10, revised 2026-08-22, E5.3).

**Decided 2026-08-22 (Karl; BACKLOG §7):** the Phase-0 plan's "thin Next.js
viewer" is DECLINED. Global Fishing Watch needs React because it has a product
team and a component library; this needs one page, and MapLibre + deck.gl from
a CDN is the same rendering engine with no second toolchain in a solo project.
Measured at E5.0 §5: MapLibre GL JS 6.x ships ESM-only from the CDN (5.24.0 is
the last UMD build), deck.gl 9.3.10 ships a UMD bundle; both usable with a
`<script>`/`<script type="module">` tag and nothing else. The basemap tile
source is a third external dependency still to be named (E5.3).
