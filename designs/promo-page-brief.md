# Design brief: the promo page (Impeccable `shape`, confirmed 2026-11-13)

Content: `designs/promo-page-content.md` (approved). Product record: `PRODUCT.md`.

1. **Job and audience.** Persuade. Readers this term: a classmate, the teacher, a stranger (laptop, phone, the demo-day projector); none knows gas trading. The page is for gas traders. Within one screen: what it is, who it is for, where to click.
2. **Outcome and proof.** Primary action: "Open the calculator" (the live Streamlit app). Proof: the route lit on the map with each point's real cost (1.4431 + 0.8494 + 0.9684 + 0.4348 = 3.6957 EUR/MWh) and real screenshots of the three tabs from a local run. Every calculated figure is asserted in `tests/`.
3. **Direction: Capacity Map** (Impeccable's pick, chosen by the user on the decision page; roll seed:76e84167d758e193, which had assigned "Marker Post").
   - World: the offset-printed transmission network map traders pin on the wall. Cool map-paper white (not cream), pipeline red only for the lit route and the action, operator blue for other pipelines, black ink, grey borders; a narrow workhorse sans in a map-legend register, not one of Impeccable's overused fonts.
   - First viewport: full-bleed map of the 15 countries, inline SVG drawn from the app's own `data/map/countries.geojson` and `core/map_points.py`; the BG > RS > HU route lit in red with its four points labelled by operator and cost; a legend box top left with the headline, the "for gas traders" line and the red button; a route-total plate bottom right with 3.6957 EUR/MWh.
   - Signature interaction: on load the route draws itself border by border, each point's cost appears, and the total adds up last; hover or focus on a point shows its operator; static under reduced motion.
   - Below the fold, in the map's sheet furniture: legend panels for the one-line problem and before/after; three inset panels (one per tab) with a real screenshot and its example; Try it; Why trust the numbers; What it does not do; an imprint-line footer (course, year, GitHub; no name).
4. **Scope and boundaries.** One static page, `docs/index.html`, with its CSS, fonts and images in `docs/`; the Streamlit app is untouched; no video or slides links until they exist. Anti-goals: generic SaaS hero with feature cards, warning-tape styling, invented users or claims, cream paper.
5. **States and ranges.** Fixed text, nothing loaded at runtime. Desktop and projector 1280 to 1920 wide; on a 390 px phone the map crops to the route region and the legend stacks under it. The map reads without JavaScript.
6. **Interaction and layout.** The button is unmistakable in the header and in Try it; the route animation runs once (about 2 to 3 s); points are keyboard-focusable; one spacing rhythm.
7. **Constraints.** GitHub Pages from `/docs` on `main`, no build step; fonts served from `docs/`; the map pre-rendered to SVG by a small script from the repo's GeoJSON (Natural Earth, public domain); nothing personal.
