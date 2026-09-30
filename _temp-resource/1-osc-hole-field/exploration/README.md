# Planning exploration reports

Nine research reports written on 2026-09-28 while planning the OSC Hole Field epic. Each was produced by an independent read-only explorer; claims are marked verified or `UNVERIFIED` inside the reports.

They are reference material. Where a report and a sub-issue disagree, the sub-issue wins.

## Reconciliations made after the reports were written

The explorers worked in parallel and could not see each other's results. These points were settled afterwards:

| Topic | Report statement | Settled value |
| --- | --- | --- |
| Sitemap | Report 07 recommends `sitemap: true` | **Off.** Report 05 ran it: runtime 0.1.0 `scan` fails with `[PUBLICATION_POLICY] sitemap has entries` |
| KiCad version for design files | Report 05 suggests the framework's 9.0.9 image | **10.0.6.** The 9.0.9 image cannot open the sibling projects' files (report 09). The framework keeps 9.0.9 for footprint previews only |
| `import pcbnew` in the 10.0.6 image | Report 09: unverified | **Verified** after the report: image pulled, `kicad-cli` 10.0.6, `pcbnew` imports, ngspice 44.2 inside, no Java inside, opens sibling KiCad 10 boards |
| Headless autorouter | Report 09: not present | Container `ghcr.io/freerouting/freerouting:2.4.1` resolves; release of 2026-09-03 |
| Hosting config dialect | Reports 05 and 06 say `doc/wrangler.toml`, report 07 says JSONC | **`doc/wrangler.jsonc`**, inert until the deferred deploy |
| Cloudflare adapter | Report 04 lists adding the adapter | **No adapter.** The site is fully static (reports 05 and 07) |
| Where module circuits live | Report 02 puts them on the core board, report 03 on the interface boards | Decided by the board-partition sub-issue from the real netlist |
| Panel thickness | Report 01 says 2.0 mm, report 09 says 1.6 mm provisional | 2.0 mm as a `PROPOSAL` parameter |

## Files

| File | Subject |
| --- | --- |
| `01-handoff-geometry.md` | Coordinate system, grid schema, block layout, artwork inventory, board domains |
| `02-handoff-blocks-electrical.md` | Per-module contracts, signal standards, size estimate, rail current, open issues |
| `03-handoff-parts-research.md` | Component candidates, CAD availability, geometry conflicts, gap list, interconnect |
| `04-handoff-docs-installer-rename.md` | Installer behaviour, the 45 pages, rename blast radius and reference script |
| `05-upstream-zudo-circuit-doc.md` | Framework packages, initializer, workflow contract, overlay failures |
| `06-sibling-zudo-led-lamp.md` | The model project: doc conventions, CI, KiCad practice |
| `07-sibling-zudo-case-and-cloudflare.md` | Hosting recipe for the doc domain |
| `08-sibling-zudo-pd.md` | The supply: rails, connectors, mechanics, source lock |
| `09-kicad-toolchain-and-fab-limits.md` | Toolchain feasibility, proof-of-concept code, fabrication limits |
