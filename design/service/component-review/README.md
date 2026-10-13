# Issue 248 component-gap review

**COMPONENT_REVIEW_READY:** all 23 existing trimmer MPN gaps have individual,
source-linked dispositions in `review.json`. This means the component review is
complete; the production MPN gaps remain open. No device has been selected,
substituted, purchased, qualified or adopted in circuit/PCB source.

The immutable source is main
`65cefd41fc39e064d38319115ad96016a1c6b71c`. The review maps current source
specifications through `scripts/schgen/core.py:designator` and independently
compares every reference, value, role and blank MPN with the committed
`schematic/boards/osc-core.net`. Hashed inputs are listed in `review.json`.

## Same-value options

| Existing gap | Count | Manufacturer candidate | Actual total resistance with ±25% tolerance | Endpoint upper bound at maximum total |
| --- | ---: | --- | --- | --- |
| Oscillator HF | 5 | Bourns TC33X-2-203E | 15–25 kΩ | 500 Ω |
| VCF BASE and AR RISE/FALL BASE | 15 | Bourns TC33X-2-503E | 37.5–62.5 kΩ | 1.25 kΩ |
| VCF RES_MAX | 3 | Bourns TC33X-2-504E | 375–625 kΩ | 12.5 kΩ |

These are manufacturer-ordering-table options at the existing nominal values.
The complete identifiers are assembled from the documented ordering grammar,
resistance code, rotational-stop indicator `-2` and `E` reel suffix. The table
supports the identities; it does not itself demonstrate available factory stock.
They use the TC33X-2 package variant already represented by the existing 1 kΩ
and 10 kΩ exact component records. No different value is proposed.

The endpoint numbers are calculations from the manufacturer's maximum of 2% of
actual total resistance for parts above 1 kΩ and the upper tolerance bound.
They do not promise zero resistance or exact full-range tuning. The 50 kΩ parts
remain in series with the existing 300 kΩ reference feed; RES_MAX remains in
series with its existing 330 kΩ feedback resistor. Required calibration span,
frequency/time/resonance accuracy and behavior over temperature need circuit and
bench evidence. The HF part is wired as three independent terminals; no circuit
response direction is inferred from the manufacturer terminal names.

## Primary evidence and drawing review

The [Bourns TC33 manufacturer PDF](https://www.bourns.com/docs/product-datasheets/tc33.pdf)
was freshly downloaded on 2026-10-11. Its SHA-256 matches the already committed
`circuit/sources/ic-library/TC33X.pdf`:

`b13258ee9f777b70198554ad4ed43cab2167b2bdf31bdcbe52c4956bfff1adbf`

The document footer gives **REV. 08/19**. The component pages have no printed
page number; use physical PDF indices 0 and 1, never the existing owner fact's
incorrect printed-page assertion as a locator.

- Index 0, right-hand **Product Dimensions / TC33X-2** drawing: visually reviewed
  plan, side, underside and terminal diagram. Body width is 3.0 mm;
  terminal-inclusive plan width/depth are 3.6 × 3.8 mm; overall height is
  1.2 mm. The general drawing tolerance is ±0.3 mm. A conservative independent
  axis bound is therefore 3.9 × 4.1 × 1.5 mm; it is not an installed tolerance
  stack.
- Index 0, **Electrical Characteristics / Physical Characteristics** and
  adjustment-tool footnote: 270° ±20° electrical adjustment, ±25% total
  resistance tolerance, 1.7 mm cross-slot tool recommendation and force below
  4.9 N. Index 1 **How To Order** distinguishes TC33X-2 rotational stop from
  TC33X-1 continuous rotation. Do not force the stop.
- Index 1, **Standard Resistance Table** rows 203/503/504 and **How To Order**:
  same-value identity and suffix basis. Index 1 **Cautions** and reflow profile:
  manufacturing-process review remains necessary.

The byte-locked receipt and exact per-claim locators are in `review.json`.
Response headers and a temporary page render are local under
`/tmp/issue248-component-cache/`; the committed PDF is the durable raw source.
No new redistribution or component catalog publication is introduced.

## Supplier identity boundary

The exact DigiKey product headers and order-code rows were read using the web
tool:

- [TC33X-2-203E](https://www.digikey.com/en/products/detail/bourns-inc/TC33X-2-203E/2566887):
  TC33X-2-203ETR-ND, TC33X-2-203ECT-ND, TC33X-2-203EDKR-ND.
- [TC33X-2-503E](https://www.digikey.com/en/products/detail/bourns-inc/TC33X-2-503E/612862):
  TC33X-503ETR-ND, TC33X-503ECT-ND, TC33X-503EDKR-ND. The absence of `-2`
  in these distributor codes is observed, not a manufacturer MPN change.
- [TC33X-2-504E](https://www.digikey.com/en/products/detail/bourns-inc/TC33X-2-504E/2566902):
  TC33X-2-504ETR-ND, TC33X-2-504ECT-ND, TC33X-2-504EDKR-ND.

Raw-page acquisition encountered HTTP 403 for all three pages. Therefore the
review records these as observations, keeps retained supplier evidence UNSOURCED
with the zero-hash sentinel, and makes no stock/allocation, lead-time, LCSC
C-number or JLCPCB assembly claim. Manufacturer primary evidence independently
supports the same-value candidate ordering grammar. A supplier byte lock and
current factory allocation remain separate follow-up work.

## Architecture and service consequences

There is no selected nominal package-envelope change relative to the existing
TC33X-2 1 kΩ/10 kΩ family. The existing family footprint and accepted pads/copper
remain unchanged. Its courtyard spans 5.3 × 3.9 mm in footprint coordinates;
a dimension comparison alone does not validate alignment with the manufacturer's
body centroid, the solder land pattern, the mirrored back-face installation or
neighboring parts. The receipt already labels fit as provisional.

Every candidate needs top access by an actual suitable tool on the populated
back face. Shaft/hand space, harness sweep, removed-core handling, neighboring
board planes and installed stack clearances are unknown. The manufacturer's
body envelope does not include that access volume. Architecture lanes should
consume both the nominal and conservative component bounds and carry tool
clearance as NEEDS BENCH. A larger or multi-turn alternative would change the
envelope and require a new exact-component review; it is not silently permitted
by this report. Fixed panel hardware and non-core poses remain fixed.

CW/CCW terminal labels are manufacturer pin identities only. They do not justify
rotation-direction arrows or establish how frequency, time or resonance changes
in a calibrated assembled instrument. The annotation lane must keep direction
UNKNOWN until circuit/installed-orientation/bench evidence exists.

## Verification and open work

The inexpensive focused comparison passed for all 23 source/netlist gaps,
including the five `RVO` oscillator references. The fresh primary PDF byte lock
matches the retained source and the mechanical drawing was visually inspected.
The parent lane owns the inventory builder/tests and canonical evidence checks.

Native KiCad, populated calibration, physical fit/tool access, electrical range,
assembly-process qualification and procurement allocation are **NOT RUN** here.
Native work is outside this research lane's assigned slot. No primary component
fact alone closes these later gates. Candidate adoption requires its own
explicitly scoped component-evidence workflow and preserved production source.
