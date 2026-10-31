# Bulk-capacitor replacement candidates (UNADOPTED)

**UNADOPTED PROPOSAL. Unvalidated draft.** This changes no BOM, schematic, footprint,
owner bundle or inventory entry. Prepared 2026-10-31. The receipt is
[`circuit/sources/bulk-capacitor/replacement-search-20261031.json`](../../circuit/sources/bulk-capacitor/replacement-search-20261031.json),
retrieved 2026-10-31T12:35:34Z.

## Current part: still stocked, but plannedDiscontinue

The fitted bulk part, Murata GRM21BR61E475KA12L, is 0805, 4.7 µF ±10 %, 25 Vdc, X5R.
On 2026-10-31 Murata's catalogue marked it `plannedDiscontinue` with
`recommendedStatus=false` (`src-c-bulk-murata-catalog-20261031`). It still had 27,909 in
stock at JLCPCB as C77077, an extended part.

Murata's suggested alternative is GRM188R61E475KE11#. That is 0603, so it is a footprint
change and is not considered here.

## Three Murata 0805 candidates are active; one leads

The target is the same 0805 footprint, at least 25 Vdc, X5R or a better dielectric,
and an active lifecycle.

| Candidate | Dielectric, range | Thickness (max) | Murata status | JLCPCB | Assessment |
| --- | --- | --- | --- | --- | --- |
| GRM21BZ71E475KE15L | X7R (Murata standard, not EIA), −55 to 125 °C | 1.25 ±0.2 mm | available, recommended=false | C437556 extended, 7,195 | Lead candidate. Better dielectric, same height. Size tolerance ±0.2 mm is wider than the current ±0.1 mm |
| GRM21BC71E475KE11L | X7S, −55 to 125 °C | 1.25 ±0.2 mm | available, recommended=false | C385038 extended, 197 | Stock too low to rely on |
| GRM219R61E475KA73D | X5R, −55 to 85 °C | 0.85 ±0.1 mm | available, recommended=false | C162298 extended, 0 | Same dielectric, thinner. No stock |
| Samsung CL21A475KAQNNNE | 0805 4.7 µF ±10 % 25 V (JLC description only) | not retained | **not checked** at the manufacturer | C1779 **basic**, 1,821,669 | Best stock and basic-library status. The Samsung lifecycle and datasheet must be acquired via Workflow C first |
| FOJAN FCC0805X475K250FT | 0805 4.7 µF ±10 % 25 V (JLC description only) | not retained | **not checked** at the manufacturer | C5137571 extended, 40,887 | Needs a primary datasheet |

The Murata rows are MANUFACTURER_PRIMARY catalogue fields. The JLCPCB rows are
DISTRIBUTOR_IDENTITY plus a dated stock snapshot, not reservations or quotes.

All three active Murata candidates also show `recommendedStatus=false`, so none of them
is a long-term recommended line.

## Same-family 0805 parts are excluded: also plannedDiscontinue

| Part | Reason |
| --- | --- |
| GRM21BR61E475MA12 | plannedDiscontinue, ±20 % |
| GRM21BR71E475KA73 | plannedDiscontinue |
| GRM21BC81E475KA12 | plannedDiscontinue |
| GRM21BR61E475KA73, GRM21BR6YA475KE11 | The catalogue search returned no result |

## Adoption needs DC-bias evidence and a role review

- **DC-bias evidence.** Retain a datasheet and DC-bias curve for the chosen part, then
  rerun every calculation that uses the bulk capacitance.
- **Role review.** Review each role where the bulk part is placed.
- **Samsung route.** Taking the C1779 basic-library route needs Samsung primary
  lifecycle and specification evidence first.
- **Owner path.** Adoption goes through the component-spec-audit new-component workflow.
  It is not a value swap.
