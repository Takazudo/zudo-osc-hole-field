---
name: component-alfa-rpar-as3340d
description: Use whenever an exact part identity, supplier code, manufacturer, pinout, package, role, source gap, or substitution for this bundle is relevant. Resolve retained ALFA RPAR AS3340D evidence for its identity, pinout, package, operating guidance and role; preserve orderability, electrical-suitability and physical checks.
---

# Exact component evidence owner

Run `pnpm circuit:check`, read every local JSON record, and cite fact/source IDs with conditions and exact locators. Keep each record aligned with the matching inventory line and direct-routing fixture. Do not infer procurement, physical fit, system safety, or circuit qualification from a component datasheet or a provisional family model.

## Human component reference

[rec-vco](/docs/components/records/vco/) is generated from this exact component record.

See the [component catalog](/docs/components/catalog/) and [cross-component rules](/docs/components/integration/). Generated component pages project only the records included by `circuit/publication/selection.json`; these JSON files remain the evidence source.

## Open review points

- No complete factory/supplier order code, current stock, lead time, consignment acceptance or assembly allocation is verified.
- The source gives SOIC-16 planform and pitch, but the local WRL is provisional family geometry. Exact body height, land-pattern fit, fixed-layout clearance and physical fit remain open.
- The manufacturer source confirms all 16 pin functions. Every pin map leaves board nets unassigned; the manual inventory provider does not bind schematic pins or placements. Project supply, oscillator behavior, start-up, calibration and current remain unvalidated.
