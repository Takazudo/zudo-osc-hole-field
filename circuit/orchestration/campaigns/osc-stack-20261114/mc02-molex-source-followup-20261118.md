# Received Molex drawing and source-to-model disposition

2026-11-18 JST, Codex coordinator on x0x WSL. The previously empty handoff is
resolved: two files were inventoried, settled, signature/hash checked, retained
in ignored storage and visually reviewed in full by independent reviewers.

| Delivered file | Bytes | SHA-256 | Actual identity |
| --- | ---: | --- | --- |
|1st one.pdf|445146|`4c311098a1a05e163fc33c19d2c35f01a51ad18b0ff14edb32429e347bef2419`|Molex SD-15020-001,PSD/001,revisionF,two sheets; drawn2025-10-30,checked/approved2026-02-16|
|2nd one.pdf|336193|`1866c1e6ca5591efe2aa1d1ccfcf58a3384c620ee7db50b9019a2974d30d62a8`|Previously retained generic LX same-side0.5mm drawing,A1,2023-04-12; byte-identical to two retained copies|

The drawing-template revisionA/date2023-02-21 is not Molex document revisionF.
The user reported downloads2/3 were identical; only two files were delivered,
so no independent third-file comparison is claimed. The generic LX sheet has
blank customer/order/drawing-number and selected N/L fields. Its receipt does
not newly bind exact C26618/40P50mm or C32128/26P60mm applicability. Do not ask
for another copy of this same generic sheet.

## Exact candidate binding and interval result

Molex sheet1 explicitly locates150200075 at N8 /51±2mm/typeA. The lower type
illustration identifies same-side contacts. The filename150200175 alone was
never the binding proof. Other51mm/typeA table entries14P150200141,
26P150200273 and40P150200427 are observations, not additional selected variants.
The active candidate scope stays exactly28existing C29534 links, with no BOM or
geometry substitution.

| Quantity | Molex declared data | Compared FH12 condition | Result and limit |
| --- | --- | --- | --- |
|End thickness|0.30±0.05mm|Required0.25..0.35mm|Declared interval contained, not full compatibility|
|8P width|4.50±0.10mm|Recommended4.50±0.07mm|Not contained:0.03mm excess each side|
|Contact exposure|4.00±0.80mm|Recommended3.5mm minimum|3.2mm minimum is0.3mm short|
|Support length|6.00±2.00mm|Recommended4.5mm minimum|4mm minimum is0.5mm short IF drawing datums correspond; mapping not established|
|Stiffener polyester|0.155mm nominal; tolerance absent|Catalog recommended0.188mm minimum|Nominal is below recommendation; no guaranteed interval invented|
|Finish|Au plating drawing label|Gold contact category|Name agreement only, not plating/contact qualification|

Molex conductor width0.30±0.03mm is not its end thickness0.30±0.05mm. The Hirose
basic pitch/true-position datum scheme is not equivalent to Molex scalar pitch/
span tolerances; terminal positional/datum conformity remains NOT_ASSESSED.
A declared interval difference does not prove every delivered unit fails.
Required limits and manufacturer recommendations remain distinct.

Candidate audit `f4e5263dcf0fe28cf6e01f622d5c15c35459e581` passed11fixtures and
independent review. Current source-only result SHA-256
`2adb51984d0c845bbd3b92882ac469e69155bd309a3bc49e180418628d482005`.
It retains the earlier51mm result and explicitly refuses product qualification.

## Why a further length-only run is not product verification

Molex specifies0.10mm copper nominal versus retained LX-model0.035mm; no copper
thickness tolerance or general linear tolerance is provided. Polyester/adhesive
layers0.086mm and stiffener0.155mm are also nominal-only. The old51mm result
varied nominal length with unchanged legacy material inputs. It neither covers
49..53mm nor binds the new product's material behavior.

Model-input audit `5137b6528b5141800cbf455193f9174eb8705664` traces actual source
consumption: capacitance uses zero-thickness coplanar strips; partial inductance
uses width/thickness nonlinearly and solves return distribution; DC resistance
uses separate S-FLEX50mm bounds65.3..106.4mΩ scaled by length. Changing a thickness
field therefore does not update DC evidence. The dielectric sweep does not
establish finite-thickness applicability. Full response/ground-sharing extrema
cannot be certified from49/53 endpoint samples without a justified method.

The audit retains `R=rho(T)*L/(w*t)` in SI units, with only conditional geometric
factor `[49000/33,53000/27]`1/mm when t is assumed exactly0.10mm. This is not a
finite guaranteed product resistance interval. Product bounds and qualification
remain null. Eleven fixtures, independent review and actual lightweight source
audit pass; result SHA-256
`2d868c8fd8ed6d862d087126af7342c41b2627e5461e7a5c95f5fec4eec6817a`.
Both current outputs are retained with implementation metadata in the ignored
received-source receipt directory. Component validation passes84manual lines,
445declared placements unverified. No electrical solver or native execution.

## Public specification cross-check and next boundary

An ordinary read of the [official150200075 page](https://www.molex.com/en-us/products/part-detail/150200075)
on2026-11-17UTC corroborates8contacts/typeA/51mm/gold and lists0.5A per contact,
60VAC and-40..105°C. These listing fields do not supply resistance, dielectric,
conductor-tolerance or contact/temperature applicability needed by the model.
The page also displays limited-catalog-information text. No procurement,
simultaneous-rating qualification or production availability is inferred; no
supplier contact or protected endpoint retry occurred.

Independent disposition: do not prioritize another49/51/53 legacy-model sample.
The exact candidate already has recommendation differences and unbound material
parameters; that run would not close an acceptance question. Further candidate
work needs a dimensional/conformity disposition or a fully specified compatible
variant, copper/rho(T)/dielectric/end-contact evidence and physical datum/access
verification. The current two PDFs have been fully used; none is still awaited.

Completed native32-case, aggregate, source-bound logic and documentation results
stay attached to their original inputs and are not rerun. DRC,zone fill,formal
adoption,manufacturing and held main/CI acceptance remain unchanged. This is a
precise source/application dependency boundary, not hardware-project completion
or a routine Moya approval wait.
