---
name: component-passives-family
description: Use whenever an exact part identity, supplier code, manufacturer, pinout, package, role, source gap, or substitution for this bundle is relevant. Resolve retained evidence for the exact shortlist resistor and capacitor series representatives; no pseudo family MPN or per-value MPN expansion.
---

# Exact component evidence owner

Run `pnpm circuit:check`, read every local JSON record, and cite fact/source IDs with conditions and exact locators. Keep each record aligned with the matching inventory line and direct-routing fixture. Do not infer procurement, physical fit, system safety, or circuit qualification from a component datasheet or a provisional family model.

## Human component reference

[rec-r-general](/docs/components/records/r-general/) is the published landing record. The other ten exact shortlist representatives remain full owner/inventory records in this bundle but are not selected as separate catalogue pages.

See the [component catalog](/docs/components/catalog/) and [cross-component rules](/docs/components/integration/). Generated component pages project only the records included by `circuit/publication/selection.json`; these JSON files remain the evidence source.

## Open review points

- Stock, lead time, consignment acceptance and assembly allocation remain dated project-state gaps unless a retained source says otherwise.
- Package preview geometry is provisional family geometry. Confirm body, height, optical path, footprint and fixed-layout fit before hardware use.
- Every pin map leaves board nets unassigned; the manual inventory provider does not bind schematic pins or placements.
