# Source-supported partial load allocation

This revision refines the retained O1 load allowance into identifiable physical packages and supply paths. It does not replace the complete-state unknowns in `electrical-report.json` with quiescent values. Source circuit and worksheet are unchanged from `4fbbe9c28c10b2648bd1edd8e45e9ff8c5651212`; the proposed connection topology is reviewed separately. No operating-point, native simulation or physical measurement was run.

## Manufacturer-supported quiescent component

Texas Instruments OPA4196IDR (SOIC-14, C2057385) and OPA4197IPWR (TSSOP-14, C2057327) are distinct whole quad packages. The component owner facts `fact-op-audio-quiescent-current` and `fact-op-precision-quiescent-current` retain these values:

| Exact package | Typical, 25 °C, per amplifier | Maximum, 25 °C, per amplifier | Maximum, −40 to 125 °C, per amplifier | Four-channel full-temperature maximum |
| --- | ---: | ---: | ---: | ---: |
| OPA4196IDR | 0.140 mA | 0.200 mA | 0.250 mA | 1 mA |
| OPA4197IPWR | 1.0 mA | 1.3 mA | 1.5 mA | 6 mA |

All are **IO = 0 A** characteristics. They are not output-load, startup, missing-rail or short-circuit current bounds. Retained primary documents are SBOS869 (July 2017; no revision suffix), SHA-256 `d89dd6009d109bf18b349e77ff46e4df60bf7d4faaefd4c3ebe6ec0e2fc7793d`, and SBOS737C (March 2018), SHA-256 `27653a7d5e965cbb2d23f7998919ebd774efd5cd3e126b8f0881469ae91166fd`. Both locators are physical PDF page index 7 / printed page 8, Section 6.7 POWER SUPPLY, IQ row. Owner records: `.claude/skills/component-ti-opa4196idr/` and `.claude/skills/component-ti-opa4197ipwr/`; retained PDFs: `circuit/sources/ic-library/OPA4196.pdf` and `OPA4197.pdf`.

`interface-contract.json.parts` provides exact Ref/unit/supply-pin and proposed-owner attribution. Count each Ref once, including unused grounded-follower channels. Every listed package has pin 4 on +12V and pin 11 on −12V. Its quiescent current flows from the positive supply to the negative supply; equal rail magnitudes must not be added and described as the actual AGND current.

| Owner | Exact refs and packages | Typical 25 °C contribution per analog rail | Full-temperature maximum IQ contribution per analog rail |
| --- | --- | ---: | ---: |
| O1 front jack | U1116, U1117: OPA4196IDR; U1118: OPA4197IPWR | 5.12 mA | 8 mA |
| O1 rear core | U1109–U1111: OPA4197IPWR; U1112–U1115: OPA4196IDR | 14.24 mA | 22 mA |
| O1 total | Six audio quads, four precision quads | 19.36 mA | 30 mA |
| Shared reference, once | U1602–U1604: OPA4197IPWR | 12 mA | 18 mA |
| O1/O2 plus shared reference | Two O1-equivalent sets plus one shared set | 50.72 mA | 78 mA |
| All five plus shared reference | Five O1-equivalent sets plus one shared set | 108.8 mA | 168 mA |

These are supported **partial load components**, not supported complete load maxima. Existing retained whole-package partition keeps U1118's unused channels in the front package and U1109's VEE driver on the rear; neither may be dropped to improve the budget. The front/control pot board has no op-amp IQ in this allocation, but its resistive and signal load is not zero.

For the proposed mixed arrangement, positive-source current reaches each front package through source/inlet protection → distribution → middle local rail zone → front supported copper rail strap and its two bolted interfaces → front trace/decoupling → pin 4. The matching negative-supply path runs pin 11 → front trace → negative rail strap and its bolted interfaces → middle negative rail zone → distribution/source. Rear package paths substitute the separately supported rear copper straps, their two bolted interfaces and rear traces. The DIN signal connector is not the qualified bulk rail path. Shared reference packages have their own local middle supply branches. Local decouplers close high-frequency loops locally but do not erase supply trace/contact resistance. Signal output currents into grounded loads additionally traverse the corresponding AGND return; those loads cannot be derived from IQ. Reference signal returns must not be silently reused as bulk power-return contacts. All source, inlet, middle, front/rear connector, trace and return terms still belong in the complete-path model.

## Reconciliation with the retained planning worksheet

The source rows are `design/reports/current/oscillator.json`, exposed without reinterpretation by `electrical-report.json.worksheet_loads` IDs below. Values are total contributions in mA, not per-package values to multiply again.

| Worksheet ID | Physical attribution | +12 V | −12 V | +5 V | Evidence class |
| --- | --- | ---: | ---: | ---: | --- |
| O1:0 | Six OPA4196IDR, four rear/two front | 6 | 6 | 0 | Guaranteed IQ component only |
| O1:1 | Four OPA4197IPWR, three rear/one front | 24 | 24 | 0 | Guaranteed IQ component only |
| O1:2 | U1101–U1104 ADG5412FBRUZ, front | 5.2 | 2.8 | 0 | Planning allowance; no complete state maximum |
| O1:3 | U1106/U1108 LM393BIDR, rear | 2 | 0 | 0 | Planning allowance |
| O1:4 | U1105 AS3340D, rear | 6.5 | 10 | 0 | Positive typical source at +15 V does not guarantee +12 V maximum; negative allowance |
| O1:5 | Four 10 kΩ jack loads, front output drivers | 2 | 2 | 0 | Normal load-envelope allowance, not short-circuit bound |
| O1:6 | Internal resistive/reference/shaper reserve, spans rear and controls | 17 | 17 | 0 | Planning reserve; includes 5 mA per analog rail added in #62 |
| O1:7 | HC14, comparator pullups and ADG enable conditioning | 0 | 0 | 6 | Planning reserve; front/rear net attribution required |
| O1 total | Existing allowance preserved | 62.7 | 61.8 | 6 | Partial normal-load planning |
| OCTAVE_REF:0 | Three OPA4197IPWR | 18 | 18 | 0 | Guaranteed IQ component only |
| OCTAVE_REF:1 | REF5050 and buffered tap/control loads | 8 | 8 | 0 | Shared reserve, once; excludes amplifier IQ |
| Shared total | Existing allowance preserved | 26 | 26 | 0 | Partial normal-load planning |

The O1 non-IQ remainder is 32.7/31.8/6 mA. It is already allocated in the rows above, **not spare headroom**. The shared non-IQ remainder is 8/8/0 mA and includes U1601 REF5050AIDR; adding that device again double-counts the reserve. U1105 VEE pin 3 receives local `/O1/VEE5` through the rear U1109 VEE driver, charged to the −12 V allowance; it is not an independent −5 V external supply. U1105 pin 16 uses +12 V and pin 12 uses AGND. U1107 SN74HC14DR pin 14 uses +5 V and pin 7 AGND. LM393B packages use pin 8 +12 V and pin 4 AGND. ADG packages use pin 13 +12 V, pin 4 −12 V, and pin 5 AGND.

This establishes useful normal-load attribution without assigning unsupported maxima. Independent source extraction already retains every package, unit and endpoint; this note does not introduce a second inventory or change those sources.

## State closure and later qualification

Normal settled operation has the IQ components above plus worksheet load allowances. Reference switching adds receiver charging and source/return disturbance: the aggregate direct five-branch 1 nF limit does not bound the charge in receiver filter capacitors behind series resistors. Full-scale control movement, simultaneous outputs and test probes must be included in the final source/load model. No quiescent table bounds those states.

Startup/ramp/brownout, missing positive/negative/5 V rails, off-state injection, wrong connection and simultaneous output shorts remain unbounded by this retained evidence. Do not set their maxima equal to the normal allowance or infer a fuse/protection trip threshold from it. #59 owns exact protection behavior; #57 owns physical supply qualification; #65 and #247 requirements remain preserved. The engineering next step is an explicit circuit protection/operating-state implementation and bounded source-to-load analysis, followed by current and rail/return measurements on the separately authorized unit. Measurements, energization and native numerical campaigns are **NOT RUN** in this revision.
