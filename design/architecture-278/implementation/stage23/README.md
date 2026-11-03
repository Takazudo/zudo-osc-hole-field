# Stage23: exact JLC sourcing for the 19 passive candidates

Owner direction on 2026-10-17 was “follow JLC to continue”: use JLC-supported
sourcing and assembly, without separate manual population. This stage follows
that route and preserves Stage22 commit 12a48ff5. It proposes exact candidate
identities; it does not apply selections, alter CAD or authorize an order.

## All nine exact identities are listed for JLC SMT assembly

Direct JLC product pages were retrieved on 2026-10-17 UTC. Each reports an Extended
library part, SMT Assembly, and Economic and Standard PCBA. These are explicit
catalog service declarations, not project/order acceptance. The stock column is
the exact product's dated `overseasStockCount`; it is not reserved inventory.

| References | Exact manufacturer / MPN | JLC code | Observed stock |
|---|---|---|---:|
| R7101, R7102, R7108, R7112, R7114 | YAGEO RT0603BRD0710KL | [C95204](https://jlcpcb.com/partdetail/C95204) | 2,061,632 |
| R7103 | YAGEO RT0603BRD0722KL | [C469656](https://jlcpcb.com/partdetail/C469656) | 47,361 |
| R7106, R7110, R7115, R7119 | YAGEO RT0603BRD071KL | [C110776](https://jlcpcb.com/partdetail/C110776) | 1,766,450 |
| R7113 | YAGEO RT0603BRD07100RL | [C122970](https://jlcpcb.com/partdetail/C122970) | 429,277 |
| R7116, R7120 | YAGEO RC0603FR-0710ML | [C114606](https://jlcpcb.com/partdetail/C114606) | 1,051,899 |
| R7130, R7131, R7132 | YAGEO RT0603BRD075K6L | [C179095](https://jlcpcb.com/partdetail/C179095) | 13,195 |
| R7135 | YAGEO RT0603BRD0722K1L | [C723484](https://jlcpcb.com/partdetail/C723484) | 26,283 |
| C7104 | KEMET C0603C100J5GACTU | [C2167326](https://jlcpcb.com/partdetail/C2167326) | 1,015 |
| C7105 | KEMET C0603C103J5RACTU | [C5360746](https://jlcpcb.com/partdetail/C5360746) | 6,190 |

The last three C-codes close the prior unresolved JLC identity gaps. The six earlier
codes were refreshed rather than treated as current stock. No sourcing-driven
replacement is justified: the original exact candidates have a public JLC route.
A failed search or HTTP 403 remains a lookup limitation, never evidence of absence.

`retrieval.json` retains exact URLs, UTC retrieval timestamps, byte counts and
SHA-256 hashes. `inventory-input.json` retains normalized observations, original
manufacturer ratings and their Stage21 evidence hashes. Raw HTML and the inspected
JLC frontend script remain in ignored `.circuit-cache/sources/stage23/`.

## Assembly declaration is separate from order readiness

The previous raw `assemblyComponentFlag=false` observations remain unchanged.
Inspection of JLC's current frontend shows that flag selects the Mechanical
Assembly badge; it is not an SMT eligibility boolean. The validator now checks
`assemblyMode=smtWeld` and the explicit visible Assembly Type label together.
It also checks `componentProductType` against the visible PCBA Type label.
Unknown or conflicting service information fails rather than becoming approval.

The exact product records also retain minimum/reel/attrition fields without
inventing an order quantity. No prototype quantity, final BOM/CPL, account stock
or accepted order is available. Accordingly all 19 proposals retain unconfirmed
order eligibility and `allocation_confirmed=false`, even with positive stock.
Extended library and service declarations do not establish a fee-free assembly
or guarantee a particular lead time.

[JLC sourcing guidance](https://jlcpcb.com/help/article/pcba-parts-sourcing-instruction)
distinguishes public-library and private sourcing routes. If public stock changes,
[JLC-managed global sourcing](https://jlcpcb.com/help/article/how-to-use-jlcpcb-global-sourcing-parts-service)
is a possible fallback within the chosen assembly route: assembly support still
requires review, and parts must reach JLC's warehouse. This is not an instruction
to buy parts elsewhere or manually populate them. No fallback order was placed.
[Component matching guidance](https://jlcpcb.com/help/article/component-matching-guidelines-for-pcba-orders)
requires warehouse availability and matching confirmation. None of those later
steps is claimed complete. Lead time is not guaranteed by this research.

## The candidate patch preserves electrical and physical requirements

`candidate-selection.patch.json` is a deterministic, unapplied proposal. Each of
its 19 operations records the old blank selection, proposed exact manufacturer,
MPN and JLC code, full unit records, pin/net identities and a complete source-package
hash. It is deliberately not a production BOM or an executable patch. All operations
remain `ready_to_apply=false`, with per-reference unresolved requirements retained
from Stage22. No reference, pin, unit, value, placement or annotation is omitted.

Manufacturer evidence is reused from the exact Stage21 sources and Stage22 role
analysis. Since no MPN changes, nominal values, tolerance, dielectric, dimensions,
ratings and assembly characteristics are unchanged. The replacement guard rejects
value, tolerance, power, voltage, temperature, TCR, dielectric or dimensional
substitution rather than treating a supplier's “similar part” label as approval.
This guard is an initial rejection screen, not a general equivalence certification.
A future substitute needs new primary evidence and role-specific review.

- The RT resistors retain 0.1% tolerance, 25 ppm/°C and 0.1 W at 70 °C, with the
  Stage22 70–155 °C derating curve. RC 10 Mohm parts retain 1% and their distinct
  primary ratings. Nominal load and conditional fault calculations remain Stage22
  results; stock cannot establish installed thermal or fault qualification.
- R7101/R7102 still permit about 10.010 mV initial ratio error against the retained
  2 mV complete static target. Resolving sourcing does not fix the error budget.
- C7104 remains 10 pF, ±5%, 50 V C0G. Its frequency-dependent center leakage and
  finite-amplifier stability remain engineering requirements, not stock decisions.
- C7105 remains 10 nF, ±5%, 50 V X7R. The control-filter dielectric classification,
  effective capacitance, aging and required settling remain unresolved. It is not
  silently reclassified as bypass or replaced with C0G.
- All parts remain 0603. Exact manufacturer body/tolerance evidence is retained;
  this does not make the captured generic pads qualified. The YAGEO process-specific
  reflow pattern and KEMET density proposal in Stage22 still require a reviewed
  land-pattern implementation and installed process qualification. JLC SMT support
  does not approve the current footprint, mask, paste, temperature or solder profile.

The JLC route removes the mixed-source/manual-population proposal for these 19
references. It does not establish JLC acceptance of the entire instrument's DIN,
panel hardware, wiring or other selected components. The 24 unbound physical records
and all 22 excluded source-land annotations remain intact. Serviceable wiring has
not been selected, and no hand-soldered wiring default is adopted by this stage.

## Next bounded step

Continue source-only engineering with the now-resolved JLC codes: close the negative
reference and manual-control error allocations, classify the C7105 filter, and
prepare exact reflow land-pattern changes against the Stage22 manufacturer drawings.
Keep the original values and retained primary limits unless a separately reviewed
change is necessary. The unresolved AC null-bandwidth and settling choices do not
block the sourcing results delivered here; ask the owner only when a concrete
functional alternative requires those choices. Wiring serviceability likewise stays
open until the termination proposal is ready.

Before any later order, establish prototype quantity, complete the BOM/CPL and
board/package review, refresh exact stock and confirm actual JLC matching and
assembly scope, including externally completed wiring. No purchase or supplier
contact was performed or authorized here. The next native request is **NONE**.
Canonical boards, locked placements, decision.json, KEEP_K1402_INCUMBENT, parked
PRs and all historical evidence remain preserved. PR286 stays draft and unmerged.
No architecture adoption, fabrication release or electrical acceptance is claimed.

## Reproduce

- `python3 scripts/architecture278/implementation/stage23_jlc.py --check`
- Add `--check-cache` to verify all retained raw hashes and reparse exact product pages.
- `python3 -m unittest discover -s scripts/architecture278/implementation -p 'test_stage23_jlc.py'`

The default check uses committed normalized evidence; it does not pretend to refresh
stock offline. The cache check requires the ignored receipts. Independent review
binds the final source and output hashes.
