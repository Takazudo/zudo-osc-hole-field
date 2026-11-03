# Stage54: decision-ready OSC power cleanup proposal

**Unadopted source and accounting proposal.** Canonical schematic, PCB, BOM,
placement, hardware and source choice are unchanged. Stage53 disposable routing
baseline and all historical stages remain intact. No zudo-pd repository edits.
Start head: `49ccc779195f1b27faebbb0a055127e51243d8f4`, draft PR287 / Issue278.

Owner direction: consider a modest component/cost revision of unfinished zudo-pd;
a separate premium supply is only an option if redesign/cost becomes substantial.
The current EXT contract remains a demand requirement, not a mandatory purchase
choice or a demonstrated zudo-pd capability. Cooling plates are planned, not
qualified; no thermal/derating credit is booked here.

## Verified easy cleanup

The current packing transform deliberately retains original package count by
adding empty batches (`io_partition.py`). Twelve fitted quads now contain only
48 grounded followers. Every follower's output/inverting feedback net has exactly
those two pins; no active user. Each package still draws from +12 V / −12 V.
All 24 associated capacitors are selected through current `Decouples` ownership,
not historical capacitor key names.

| Idle quads | Exact identity | Owned bypasses (+12 / −12 V) |
| --- | --- | --- |
| U112 / U212 | TI OPA4196IDR | C140/C141; C240/C241 |
| U113 / U213 | TI OPA4196IDR | C142/C143; C242/C243 |
| U116 / U216 | TI OPA4197IPWR | C128/C129; C228/C229 |
| U117 / U217 | TI OPA4197IPWR | C131/C132; C231/C232 |
| U118 / U218 | TI OPA4197IPWR | C133/C134; C233/C234 |
| U119 / U219 | TI OPA4196IDR | C144/C145; C244/C245 |

Bypasses are Murata GRM188R71H104KA93D, 100 nF. The proposal removes 12 ICs and
24 capacitors, reducing fitted IC count 650→638. This is a count reduction, not a
priced BOM saving. Nominal bypass capacitance falls 1.2 µF on each analog rail;
local rail layout/decoupling consequences still need review before adoption.

**Do not remove the original functional cells.** Their channels were repacked:
H1 U102 handles slew, U103 reference, U104 precision output, U106 input buffers
and two magnitude indicators, U110 output magnitude; H2 uses refs +100.
`proposal.py` filters only six verified idle package stems after refinement,
with their explicit bypasses. It retains all surviving Part fields, designators,
positions, pin nets, active channel signatures and panel bindings.

The baseline generator reproduces every committed master schematic byte before
filtering. Only the disposable shared sample_hold sheet changes. Fresh native
KiCad exports match the full spec on both sides: 20,434→20,218 pins; exactly 216
idle-package/bypass pins removed, all 20,218 retained pin nets unchanged. Exactly
48 private follower nets disappear. Native comparison is connectivity evidence,
not ERC/DRC, analog behavior or hardware qualification. The proposal and native
receipts are in `proposal.json`, `native-audit.json` and `evidence/`.

## Demand comparison

Retained TI primary tables support zero-output-current Iq allowances: OPA4197
1.5 mA/channel full-temperature maximum and OPA4196 0.25 mA/channel. Six quads
of each give **6×4×1.5 + 6×4×0.25 = 42 mA on each analog rail**. Typical model
reduction is 27.36 mA/rail. This removes component-Iq allowance, not a measured
42 mA saving or a complete load maximum. Conditions/hashes are in `sources.json`.
At nominal ±12 V, the Iq allowance corresponds to 1.008 W; both rails conduct
simultaneously, so it must not be halved.

A separate accounting error affects 20 dual-rail LM393BIDR clip-comparator
packages: A01–A06 have two each; M5A/B and M4A/B have two each. Native source
supply pins are +12/−12 V, yet typical worksheet allowance is 0.6/0.1 mA per
package. Keeping the same 0.6 mA model symmetrically corrects the negative typical
ledger by **+10 mA**. This is not a new guaranteed or measured LM393B rating.
The planning model is already 1/1 mA, so its correction is zero. Pullup and LED
sink loads remain separate. `accounting.json` lists every package and load row.

| Accounting scope, mA (+12 / −12 / +5 V) | Current | Proposed comparison |
| --- | --- | --- |
| Reported/assumed typical subtotal | 857.198 / 790.698 / 80.273 | 829.838 / 773.338 / 80.273 (Iq removal plus clip correction) |
| Master planning subtotal | 1505.819 / 1414.569 / 177.286 | 1463.819 / 1372.569 / 177.286 (Iq removal only) |
| EXT normal planning including allowances | 1534.819 / 1435.569 / 224.286 | **1492.819 / 1393.569 / 224.286** |
| Minimum continuous source requirement | 1700 / 1600 / 300 | **Unchanged** |
| Minimum transient source requirement | 2000 / 1900 / 400 | **Unchanged** |

Complete typical load, guaranteed whole-instrument maxima and measured source
capacity remain unknown. Every existing unknown reason is retained. The remaining
conditional EXT planning figures exceed historical unmeasured zudo-pd targets
1200/800 mA by 292.819/593.569 mA on the analog rails. Cleanup alone therefore
does not establish adequacy of that old target; neither does this comparison select
a premium supply. Source redesign, exact cost and capacity belong to the separate
parent review. No continuous/transient requirement is lowered automatically.

## The 233 mA pools: overlap exists, no blanket rebate

| Coarse pool | Allowance per analog rail |
| --- | --- |
| Five oscillators | 5×17 = 85 mA |
| Shared reference | 8 mA |
| Three filters | 3×12 = 36 mA |
| Six envelopes | 6×12 = 72 mA |
| Four mixers | 4×8 = 32 mA |
| Total retained | **233 mA** |

The oscillator 17 mA is original 12 mA plus an explicit 5 mA reference increment;
original reference overlap is not allocated. Existing fanout branch calculations
conditionally bound local output load at 4.119989/4.057177 mA per oscillator.
Replacing only the explicit 5/5 increment could tighten the instrument allowance
by 4.400054/4.714116 mA under the same assumptions. This optional refinement is
**not booked**, is not hardware saving, and gives no credit against the original
12 mA pool or shared 8 mA pool.

Actual overlap candidates are identifiable: filter BP/LP mirror feeds and RES/DRY
servo branches reach OTA IABC pins through 22 kΩ; envelope RISE/FALL mirror feeds
reach IABC through 22 kΩ; MIX4's servo feeds IABC through 10 kΩ. The separate
LM13700 package allowance says it includes bias, while these coarse pools include
converter/servo loading. But the duplicated amount has not been partitioned among
package supply, IABC injection, mirror/reference branches and dynamic behavior.
The MIX4 nominal 0–500 µA command is not a guaranteed corner bound. `accounting.json`
retains the exact live branch refs, values and pin nets. No numerical rebate follows
from those overlaps yet.

Real loads must remain: four ±5 V 10 kΩ trim tracks per filter, two per envelope,
and one per MIX4 total **26 mA nominal through-current on both analog rails**.
These are identified contents of reserves, not another charge to add. OSC BASE
and SINE trims similarly each conduct 1 mA nominal; the existing tolerance model
uses up to 10.05 V / 7.5 kΩ = 1.34 mA before wiper load. Feedback networks, signal
pots and separately allocated external loads are not assumed redundant.

## Simultaneous power and a separate protection option

Quiescent current and resistor paths between bipolar rails load both rails
simultaneously. Clip LED paths also return to −12 V. In contrast, maximum source
and sink currents of a bipolar output or magnitude indicator can describe opposite
signal states. Summing independent rail maxima is a conservative envelope, not an
established simultaneous operating point. Do not halve all bipolar allowances;
source per-rail sizing still needs each limit. A future state-by-state load model
must trace actual return paths and compatible signal/control states.

There are 110 fitted ADG5412FBRUZ packages in the current ledger. Grouping compatible
input-protection channels into fewer packages is a **separate architecture option**,
not part of this removal. It requires an exact channel assignment respecting jack
board boundaries, signal integrity, shared enable/fault behavior, supply/return
paths, package dissipation, fault isolation and physical service/layout. Reuse of
unused channels cannot be assumed across incompatible boundaries. No grouping,
placement change, channel sharing or numerical savings is implemented or booked.

## Decisions and next work

1. Parent may authorize canonical implementation of this exact idle-package cleanup
   later, including generator/BOM/worksheet/allocation updates and board-specific
   routing/decoupling review. This study itself does not adopt it.
2. Correct clip typical accounting in a separately reviewed canonical update;
   source requirements remain unchanged until whole-load closure.
3. Replace coarse pools with a branch/state ledger, beginning with conditional
   oscillator reference refinement and OTA IABC/mirror attribution; retain unknowns.
4. Parent compares a modest zudo-pd revision against these remaining requirements,
   exact component/cost implications and thermal/startup evidence. Planned cooling
   plates are not qualification. Premium supply remains a contingent option.

Before energisation or release, the selected source still needs continuous/transient
rail, startup/retry, protection, cable/contact drop, return current and loaded thermal
qualification. Those are future gates, not instructions to power hardware now.
No order, fabrication, energisation, merge or further routing experiment performed.
Stopped after this bounded plan for parent review.
