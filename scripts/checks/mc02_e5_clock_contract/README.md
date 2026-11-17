# E5 clock and READY source contract

This bounded source-only audit enumerates every generated contact on E5 CLOCK_RC,
CLOCK and READY, retaining physical reference, unit, pin, source role, exact MPN
(or blank), template symbol and owner pin function. It does not repeat the prior
128-assignment truth audit or any native/placement study.

Run from the repository root:

```sh
python3 -B scripts/checks/mc02_e5_clock_contract/audit.py
python3 -B -m unittest discover -s scripts/checks/mc02_e5_clock_contract -p 'test_*.py'
```

The frozen report has 3 CLOCK_RC contacts, 19 CLOCK contacts and 20 READY contacts.
CLOCK includes one HC14 output, a feedback-resistor terminal and 17 HC74 clock
inputs. READY has one HC74 Q driver, 15 HC74 clear inputs, 3 HC00 inputs and one
HC221 active-low reset input. Contact counts are not electrical fanout acceptance.
All contacts are source netlist bindings, not manufactured board verification.

The source declares R4533 47 kohm and C4509 1 nF C0G. Their exact MPNs are blank;
the 100 kohm/100 pF-looking generic symbol identifiers cannot supply exact values,
tolerances or qualified parts. C4509 is separated from CLOCK by R4533; it must not
be treated as a directly connected CLOCK output capacitance. No frequency is
calculated from these nominal proposals.

Retained TI PDFs were visually inspected at printed p5 (physical index4):
SCLS094F section6.5 gives HC74 Ci maximum10 pF at VCC2–6 V, TA-40–85 C;
SCLS085L section5.5 gives HC14 Ci maximum10 pF at VCC5 V, TA-40–85 C.
Both give typical3 pF only at25 C. The original supplemental observation has since been linked to its canonical
owner fact as described below. HC74 values are not borrowed for HC00 or HC221.
These device-input rows exclude routed capacitance, coupling and driver/network
behavior. The 50 pF switching-test fixture condition is not a project-load bound.

The evidence freezes source bytes and semantic contacts. `source_commit` identifies
the pre-implementation source snapshot; the local audit is separately SHA-pinned
and becomes part of a later implementation commit. The audit writes only stdout.
Any retained result must be stored under ignored cache by its caller.

Still required: exact RC part identities and tolerance/temperature/voltage bounds;
actual supply and operating range; complete routed clock/reset network and load
model (including other device inputs and parasitics); driver transition/load
applicability; measured/supported period, duty cycle, edge time and skew at each
receiver; asynchronous reset recovery/removal and startup/partial-power analysis.
Physical load, guaranteed clock frequency, edge bounds and READY timing slack
remain null. Source closure alone cannot establish them. Next work may acquire
missing exact-part and conditioned source data, then define a separately reviewed
model/measurement plan. No new placement, adopted RC parts, DRC, fill, formal
adoption or manufacturing follows from this report.

## Conditional receiver-only catalog sums

The source extension adds HC00 SCLS181H printed p5 section6.5 Ci10 pF maximum
at2–6 V/-40–85 C (typical3 pF at25 C), and CD74HC221 SCHS166F printed p7,
physical index6, upper HC CIN row10 pF maximum in the -40–85 C column.
HC221's VCC and row test-condition cells contain dashes: no numeric supply range
is inferred. The continued table header says input tr,tf=6ns; this context and
HC family block are retained rather than silently applying an HCT row or
assigning the adjacent propagation row's CL50pF to CIN. All owner JSON and both
additional retained PDFs are pinned. This checker does not modify owner facts.

The named ledger yields CLOCK17HC74 inputs ×10=170 pF; READY15HC74 inputs ×10
plus3HC00 inputs ×10 plus1HC221 reset input ×10=190 pF. These are sums of catalog
maxima under their individual recorded conditions. They are neither measured
loads, guaranteed project upper bounds, nor lower bounds. A sum above a switching
fixture's CL value does not prove actual timing failure. Shared actual operating
conditions are unestablished; HC221's missing numeric row supply is not filled
by the other devices' conditions. Each result carries full named receiver groups,
source conditions and separately listed driver/passive contacts excluded from
this arithmetic. CLOCK_RC's1nF capacitor remains behind47k and is not added.
Driver/network response, routing/coupling and other parasitics remain unknown.
All actual load and timing fields stay null/NOT_ESTABLISHED.


## Canonical Ci amendment

Source `2f3f7c8999f3dccecfe41597f23739483272afad` adds conditioned HC00/HC74/HC221
Ci facts and clarifies the existing HC14 fact. Engineering remains2c53715;
prior source commits/receipts are historical, not relabeled. Exactly11 consumed
owner fact/manifest/coverage hashes change; all other existing input pins remain
unchanged except this checker's own implementation hash. The report includes each
canonical fact ID, value, exact conditions/locator and OPEN electrical coverage.
The checker compares the supplemental maximum to that fact and rejects changed
conditions or cleared coverage blockers. Typical/dashed-cell observations retain
their PDF provenance. Conditional170/190pF arithmetic is not a canonical guaranteed
load fact; physical acceptance remains unestablished.
