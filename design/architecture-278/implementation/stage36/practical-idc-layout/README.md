# Practical IDC layout — 16-pin power and 14-pin signals

**Recommendation:** use a standard shrouded **2×8 power connection** and a separate standard shrouded **2×7 signal connection**, both accessible from the rear after removing the cover. Use flat ribbon and standard strain relief; disconnect both before core removal. No custom guard/collar. This is an unadopted architecture proposal, not a whole-instrument fit result.

This supersedes the previous comparison's custom guard recommendation and its unsupported universal wrong-port acceptance requirement. The parent requests protection proportionate to ordinary internal maintenance, with residual risk shown for decision. Fixed panel, canonical circuit/BOM/CAD, earlier stage receipts, both viewers and coupon remain unchanged. The standalone coupon is unordered/deferred and unnecessary for this proposal. Extra depth is allowed; 5 mm is neither a limit nor target.

**Research checkpoint:** paused on owner instruction in favor of the panel appearance editor. Nominal CAD arithmetic was independently reproduced; the complete proposal, map and termination conclusions have not received final review. Do not implement this hardware from this note.

## Exact standard parts and termination

| Function | Header | Cable socket, with strain relief | Ribbon candidate, 1 m raw length |
| --- | --- | --- | --- |
| PWR16 | Würth 61201621621 | Würth 61201623021 | Würth 63911615521CAB |
| SIG14 | Würth 61201421621 | Würth 61201423021 | Würth 63911415521CAB |

These exact variants exist in the maker's active catalog, with explicit header/socket pairing and downloadable dimensioned drawings and STEP models. The 14-pin option is real, not extrapolated from a family formula. The raw ribbon is 28 AWG, 7×0.13 mm tinned copper, 1.27 mm pitch and 0.9±0.1 mm thickness; widths are 20.32 mm (16) and 17.78±0.2 mm (14). The 16-pin width has no explicit adjacent ± value; apply its drawing's general tolerance only after interpreting the stated standard, not the 14-pin tolerance by analogy. No bend-radius or repeated-flex guarantee was found for these cables.

Use the maker WR-TOOL press 600600282800, base 600600282801 and WR-BHD die 600612282804. Its instructions identify the socket family and require cable guidance, planar placement and complete closure. The maker ribbon catalog links the 2.54 mm cable-side family under “Use with”; selected pitch, construction and counts are compatible at family level. This does not supply an exact cable/socket assembly acceptance drawing or a finished harness MPN. The proposed harness is two IDC sockets pressed onto the stated raw ribbon, 1:1 continuity, strain relief fitted. CAD pin-number/stripe inspection and an ordinary unpowered continuity/short check establish assembly correctness; no standalone component qualification program is proposed.

[Maker header catalog](https://www.we-online.com/en/components/products/WTB_WR_BHD_BOX_HEADER_2_54MM_MALE_PCB), [socket catalog](https://www.we-online.com/en/components/products/WTB_WR_BHD_BOX_HEADER_2_54MM_FEMALE_CABLE_SIDE), [ribbon catalog](https://www.we-online.com/en/components/products/WTB_WR_CABLE_RIBBON_FLAT_CABLE). Exact PDF/STEP URLs and hashes are in [sources.json](sources.json). These are established standard catalog parts, but **current stock/region/lead time is not verified**: maker availability requires login, distributor access failed. Do not call them immediately stocked or order-ready. No login, enquiry, cart or purchase was attempted.

## Proposed numbered map

View **into the board header mating face**, with key opening nearest the reader/bottom of the diagram: odd pins run left-to-right on the near row; even pins on the far row. The cable socket mating-face drawing is mirrored when facing the header; do not reuse its front-view XY as board XY. Mark pin 1 on both boards and both sockets. Both harness ends join equal pin numbers; fold orientation is specified by that continuity, not by visual stripe alone.

| PWR16 pins | Proposed net |
| --- | --- |
| 1, 2 | −12V |
| 3, 4, 5, 6, 7, 8 | AGND |
| 9, 10 | +12V |
| 11, 12 | +5V |
| 13, 14 | NC (conventional CV positions unused) |
| 15, 16 | NC (conventional Gate positions unused) |

This uses the conventional rail ordering shown by [Doepfer's module connector drawing](https://doepfer.de/a100_man/a100b_e.gif), with pin numbering bound to the selected header's marker. A 10-pin power cable does not carry +5V and is not a replacement. This is an internal A01 connection, not a claim that the complete instrument can plug into arbitrary Eurorack power supplies. Multiple ground/power conductors do not prove equal sharing or a larger fault limit. Bonding these pins changes the proposed inter-board harness topology only after adoption; the canonical circuit is untouched.

| SIG14 pin | Proposed net | Existing GH J-SIG pin |
| --- | --- | --- |
| 1 | /A01/REF5 | 1 |
| 2 | AGND | 2 |
| 3 | /A01/REFN5 | 3 |
| 4 | /A01/IN_BUFFER | 4 |
| 5 | /A01/OFFSET_BUFFER | 5 |
| 6 | /A01/SUM_NEG | 6 |
| 7 | AGND | 7 |
| 8–14 | NC, no added grounds or signals | — |

REF5 and REFN5 remain references, never +5/−5 power rails. Retaining the seven existing signal assignments avoids inventing return paths. Stripe means **pin 1** on both ribbons; only on PWR16 does that also mean −12V. Label both ends **PWR16 / −12V PIN1** or **SIG14 / SIGNAL ONLY**. The [A01 current ledger](../a01-current-ledger/README.md) remains conditional; the header/socket/cable ratings are not an upstream fault-current bound.

## Actual mating geometry and practical separation

Maker header lengths: 27.98±0.20 mm (16), 25.44±0.20 mm (14). Socket lengths: 25.00±0.15 and 22.46±0.15 mm. Both use the same 2.54 mm grid. Nominal pin spans are 17.78 and 15.24 mm. Body key opening is 4.5±0.15 mm; socket key width 3.70±0.15 mm. These ordinary keys address orientation, not every possible wrong cable.

A CadQuery inspection imports the **unmodified maker STEP models**. Header seating plane is z=−4.675; inner floor −2.075; mouth +4.425. Rotate socket 180° about Y and translate z by +4.925: its mating face z=7 then seats at the header floor. Matched 14/14 and 16/16 plastic-body intersection volumes are zero. Nominal insertion to the floor is 6.5 mm; this is a geometric seating construction, not a maker force/contact-travel specification.

The full supplied socket model then reaches **18.3 mm above the board seating plane**. Its termination cap/strain relief are supplied in an open state; 18.3 mm describes that modeled state, **not a verified closed mated height**. Retain this conservative planning envelope instead of falsely shrinking it. Header CAD Y extent includes protrusions and is 9.175 mm, not just the 9.0 mm nominal drawing body. Model solids, transforms, bounds and Boolean results are recorded in [cad-report.json](cad-report.json); a zero intersection is neither tolerance closure nor physical verification.

Propose a **74×30 mm accessible service bay** on each relevant board's rear-facing edge, with separate PWR16 and SIG14 positions. Along the 74 mm edge, maximum header lengths plus a **12 mm clear gap** and **4 mm ends** total 73.82 mm. Use local centres (18.09,15) and (57.00,15) mm. These are proposed service-bay coordinates, not edits to locked panel coordinates. The retained A01-middle outer envelope is 82 mm wide, so the strip fits that outer width arithmetically with 8.18 mm spare; populated routing, carrier, foreign boards and fastener clearance are **not inferred** from this. Separate cable paths on their own sides, label at the mating faces, and expose both sockets completely before disconnecting. The 12 mm gap is a practical grip allowance to preview/check in the integrated mock-up, not a measured ergonomic result.

Reserve **32 mm board-to-obstacle depth** as a layout starting point, using the supplied 18.3 mm CAD envelope, a **10 mm assumed flatwise service bend**, 0.5 mm half-thickness and a **2 mm proposed combined placement/bow margin**: 30.8 mm. Neither 10 mm radius nor 2 mm alignment allowance is a maker guarantee or measured fact. With cover removed, a **36 mm open withdrawal column** covers 18.3+15+2=35.3 mm. The 15 mm travel is retained service planning travel, not a new connector specification. These reservations replace the failed narrow cassette concept and must be placed in the complete model; they do not certify present enclosure fit. Cable runs remain flatwise, without hard creases or twisting at IDC exits. No cut length is fabricated from absent endpoint geometry.

## Required checks versus optional misuse protection

**Required for normal assembly/service:** approved net-to-pin map and both-end 1:1 continuity; no rail shorts; polarity checked at the pin-1 markings; REF5/REFN5 kept separate; correct socket/header identity; complete IDC closure and strain relief; mechanically supported board and socket-body grip. Keep existing current/protection limitations explicit. These checks do not require an impossible guarantee against every external cable.

**Residual maintenance risk for parent decision:** the two supplied harnesses have different counts, conspicuous labels and separate accessible locations. Geometry makes a normal swap conspicuous, but does not establish universal physical impossibility:

- A centred 16-pin socket cannot fully seat in the 14-pin header in the nominal model: body interference is 17.364 mm³.
- A centred 14-pin socket body can enter the 16-pin header, but its pin rows are displaced by 1.27 mm from header pins. Shifting ±1.27 mm to align contacts conflicts with the normal key (3.715 mm³ modeled plastic intersection). This is evidence against normal full seating, **not proof against partial contact, forcing, bent pins or damaged/unkeyed replacements**.
- A conventional external 10-pin power socket may fit the larger 14-pin signal header centrally with aligned contacts. It must not be introduced as a signal replacement; its −12V pair could reach SIG14 pins 3/4. This is a real residual risk, not a new universal-protection gate.

Optional future protection is a genuinely different signal family if the owner wants stronger physical differentiation. Do not add a custom guard/collar by default. The decision here is whether labelled, count-distinct internal cables and controlled maintenance are acceptable; no residual risk is silently called eliminated.

## Service sequence and short alternative

Remove the rear cover and support the core/board frame. Inspect labels, disconnect and park PWR16, then SIG14, gripping housings with adjacent board support. Both are accessible without removing load-bearing retention. Remove the core through its 40 mm path only after both ribbons are free. For jack-board access, lift out the disconnected harness/ordinary removable clips before exposing fasteners. Reassemble in reverse, then perform the required unpowered pin-map/short/polarity checks. No cable supports a moving board. One integrated unpowered access mock-up checks grip, routing and fastener/core clearance; no standalone coupon purchase or endurance campaign.

**Short alternative:** internal-only 2×4 power (61200821621 / 61200823021, raw ribbon 63910815521CAB) plus the same SIG14. It saves 10.16 mm of header length but loses conventional power-harness replacement and needs a separately reviewed internal power map. Smaller sockets may enter larger headers; it is not inherently safer. Prefer this only if the 74 mm service bay cannot be arranged. A different signal connector family would improve differentiation but adds a separate termination/spares system; no additional architecture is recommended without an owner reason.

The next useful implementation is one source CAD placement of this bay and its two cable paths, with the proposed pin map reviewed against the circuit. Required remaining inputs are actual endpoint/routing geometry for cut lengths and the intended local availability before parts are selected. Source work can continue without physical measurements; actual assembly/access is checked once in the integrated unpowered mock-up. No circuit/BOM adoption, manufacturing or procurement is implied.
