# Front and shared-middle source evidence

This independent source investigation supports further candidate implementation on PR286. It does not change the retained circuit, assign missing MPNs, establish manufacturer qualification, or supersede earlier hash-bound reviews. Reproduce `front-evidence.json` with `python3 scripts/architecture278/implementation/front_evidence.py`; use `--check` for deterministic comparison. Input hashes, exact inventory owner records, retained source IDs/URLs/hashes/locators and local hardware pad coordinates are embedded in that report. No network acquisition or native run was performed for this report.

## Inventory and feasible whole-package groups

The retained non-rear inventory has 95 packages: 57 front-jack, seven front-control, one octave-selector and 30 shared-reference packages. Multi-unit packages are counted once. All eight jacks and eight controls retain their panel UIDs; the extraction asserts hardware footprint numbered-pad equality, including NC mechanical lugs.

The following groups preserve actual packed amplifiers and their local circuits. These are electrically feasible grouping constraints, not placed/clearance-qualified board shapes:

| Group | Complete package members | Count |
|---|---|---:|
| 1V input | J101, U1101, R1101–R1104, DO1101, C1121–C1122, U1118, C1140–C1141 | 12 |
| FM/PWM/SYNC inputs and SIN output | J102–J105, U1102–U1104, R1105–R1116, DO1102–DO1104, C1123–C1128, RB1102–RB1103, U1116, C1150–C1151 | 33 |
| TRI/SAW/PUL outputs | J106–J108, RB1104–RB1109, U1117, C1152–C1153 | 12 |

U1116 contains three input followers and the SIN output amplifier, so four independent per-jack clusters cannot each own that package. U1117 contains three output amplifiers plus a grounded spare; U1118 has the precision 1V follower plus three grounded spares. Keep supply units and local bypasses with the complete package. Front output feedback remains at its front amplifier and must never be transported through the rear link.

Use `Decouples` keys, scoped to instance/owner, for the front bypass mapping. Several capacitor display names are stale: C1140/C1141 belong to U1118 (`IO_EXTRA_18`), C1150/C1151 to U1116 (`PACK_OPA4196IDR_4`), and C1152/C1153 to U1117 (`PACK_OPA4196IDR_5`). Shared-reference package keys repeat O1 keys, making an unscoped global dictionary unsafe.

The seven control packages are RV104–RV108 and SW102–SW103; SW101 remains its separate stepped octave-selector assembly. No receiver or wiper buffer is moved onto these passive controls.

The complete shared-middle group is U1601–U1604, R1601–R1616, RV1601 and C1601–C1609. Keep all 30 together initially: U1602 contains +5 V, −5 V and gate-reference stages plus octave0; U1603 buffers octave1–4; U1604 contains octave5 and ladder endpoint/feedback stages. Their whole-package overlap prevents dividing octave and other reference functions into independent IC groups. Shared local feedback and ladder nodes must remain on middle, with no remote sense loop.

## Exact identities and evidence limits

The map resolves manufacturer plus full MPN to exactly one inventory/manifest record and only that record's source IDs. Available retained primary metadata exists for ADG5412FBRUZ, BAT54S,215, OPA4196IDR, OPA4197IPWR, REF5050AIDR, the Bourns panel pots and Alps selector. This statement describes evidence metadata; it does not renew downloaded-byte verification or close the record's open domains.

Qingpu WQP518MA is not an exact manufacturer-qualified mechanical model: the owner bundle explicitly retains distributor identity/family drawing evidence and an unavailable exact manufacturer drawing. Dailywell 2MS1T1B1M2QES-5 and 2MS3T1B1M2QES primary sources remain unavailable; retained mirrors do not become primary evidence. Murata GRM188R71H104KA93D has a later retained manufacturer catalog record alongside its unavailable older datasheet record; inspect the separate lifecycle and electrical coverage before claiming part acceptance.

Twenty-four packages still have no exact source MPN: R1102, R1104, R1106, R1108, R1110, R1112, R1114, R1116; C1602; R1601–R1603; R1605–R1616. Do not infer identities from nominal values or family naming rules. Existing full MPNs also retain their owner bundle procurement/fit/electrical open domains.

Committed `design/connectors/jst-gh.json` supplies 3-, 7- and 8-way geometry. This investigation additionally read the exact 2/4-way rows in its retained manufacturer PDF, hash `b1dcb317b6b9a4fbbedd2dbf42c64c95306a252d23de8933b85fcf161240b722`, and visually inspected the top-entry land drawing. The new report adds candidate-only 2/4 geometry without editing canonical connector data:

| Positions | Header (label suffix LF/SN explicit) | Header A / B mm | Housing | Housing A / B mm |
|---|---|---|---|---|
| 2 | BM02B-GHS-TBT(LF)(SN) | 1.25 / 5.75 | GHR-02V-S | 1.25 / 3.75 |
| 4 | BM04B-GHS-TBT(LF)(SN) | 3.75 / 8.25 | GHR-04V-S | 3.75 / 6.25 |

Exact rows and label note are on physical PDF page2, printed3. Physical page1, printed2 defines the mounting-surface top-entry view: pin1 is rightmost; signal pads are 0.6×1.7 mm at `x=A/2−(pin−1)×1.25, y=0`; hold-down pads are 1×2.8 mm at `x=±(A/2+1.85), y=3.35`. Two-way signal centres are ±0.625 mm and hold-down centres ±2.475 mm. Four-way signal centres are 1.875/0.625/−0.625/−1.875 mm and hold-down centres ±3.725 mm. Pitch tolerance is ±0.05 mm nonaccumulating. These nominal lands reproduce the existing3-way coordinates; they do not prove an actual mated assembly. Candidate courtyard margins are copied from the retained geometry policy and explicitly classified as project choice.

The same page identifies SSHL-002T-P0.2 for AWG30–26 and insulation OD0.76–1.00 mm; the drawing warns SSHL-003 contacts cannot be used with GH. Wire/insulation/crimp compatibility and fitted bend/strain relief still require implementation checks. The HARTING 09032966824/09031966922 selected-pair evidence and remaining exact face/force gaps stay in `revision-connectors.md` and `connector-source-receipt.json`. Neither GH nor DIN supplies the strict main return resistance budget.

## Actual front pad datums

`front-evidence.json` records every pad from the committed footprint, not a hardware-centre surrogate. Coordinates are local unrotated CAD coordinates; the candidate must apply its actual side and rotation:

- WQP518MA barrel-axis origin: S=(0,−6.48), TN=(0,−3.38), T=(0,4.92) mm. TN stays NC. The sleeve and signal terminals differ by 11.4 mm and cannot share one zero-length origin.
- PTV09A shaft-axis origin: pins1/2/3=(−2.5,7)/(0,7)/(2.5,7) mm; mounting lugs4/5=(−5.3,0)/(5.3,0) mm remain NC. A raw wiper starts at pin2, seven millimetres from the control centre.
- SRBV160803 selected common pins1 and10 lie at (5,9.15) and (5,−9.15) mm and are electrically joined. Six throw paths use distinct pads2–7. Retain both common terminals and the separate stepped support geometry.

Dailywell toggle pad coordinates and all dimensions/drills are extracted alongside these. These coordinates support source routing calculations only; inherited footprint/family uncertainty and installed fit remain OPEN.

## Complete-path and return requirements

Replace each centre-based 10 mm front allowance with actual front signal endpoint→header pad paths. Inputs begin at the front buffer output pad; rear-to-front shaped outputs terminate at the front output-amplifier input pad. Their jack-tip protection/output paths remain additional local circuits, rather than being silently included in a nominal remote allowance. Raw controls start at the actual wiper/switch pad. Include each header's pad-to-contact path, actual wire length, both mating paths and any supported terminal conversion, middle copper, DIN path and rear endpoint copper. Shared-net branching must use the union of segments for capacitance and common-edge resistance; per-branch distance maxima cannot establish aggregate loading.

The nine shared reference nets need explicit middle source endpoints: U1602 outputs pins1/7/8/14 drive REF5/REFN5/GATE_REF/OCT0; U1603 pins1/7/8/14 drive OCT1–4; U1604 pin1 drives OCT5. Feedback pins on the same net are also retained in the report and must stay local. Model all five receiver equivalents, not merely the O1/O2 geometry comparison. Switched 1 kOhm/100 nF receiver demand is distinct from the aggregate <=1 nF direct octave parasitic requirement.

Pair each front signal path with its actual AGND conductor, header pads, middle return corridor and adjacent DIN b-row contact where applicable. Reference endpoints, power common edges, bolted straps, PCB spreading/vias and core/front load returns need a separately connected graph. Retain supplemental parallel ground branches without assuming equal current sharing or crediting them toward <=0.5 mOhm combined branch+K return. Rails <=1 mOhm, hot drop <=20 mV, full source/rail/return <=0.20 V and GH <=0.5 A/contact remain unchanged.

Actual route capacitance, leakage, load/settling, startup/fault maxima, source regulation, stability, partial-power injection and ground error remain OPEN. Physical and native ERC/DRC checks are NOT RUN. Further placement must re-evaluate the near-300 mm allocations rather than inherit their earlier pass.
