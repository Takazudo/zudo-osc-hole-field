# Existing HF trim: exact source candidate and calibration boundary

Select **Bourns TC33X-2-203E / JLC C720648** for the existing O1 RVO1109
HF_TRIM in a separate source candidate inventory. No additional controls,
canonical BOM/CAD, geometry or historical files are changed. The complete original
candidate graph (250 packages, 806 pins, 329 units) is retained; only this package's
MPN, Manufacturer and LCSC attributes change. Stage26's separate A01 inventory
(118 references / 561 pins / 154 UUIDs) remains byte-identical and hash-bound.
This selection closes the exact candidate identity gap, not procurement release.
O1 is the inspected implementation; O1–O5 family intent does not authorize replication.

## Evidence and mechanical match

[evidence.json](evidence.json) retains dated source URLs, SHA-256, locators and
supplier observation; raw PDF, HTML and response headers stay in the ignored cache.
Bourns TC33, REV. 08/19 (current PDF includes a 05/26R legal page), page index0
characteristics/dimensions and index1 ordering table establish code203=20k and
-2=rotational stop. This is the same top-adjustment -2 mechanical variant used
by the existing 1k/10k trims. Pin2 is wiper, pin1 CCW, pin3 CW. Retain
1=HF_PIN, 2=LINEAR_REF, 3=AGND. Clockwise approaches the grounded end; no monotonic
frequency-response claim follows.

The drawing gives 3.8 by3.6 mm outline and nominal1.2 mm height, general±0.3 mm
except where noted. Existing pad sizes and relative centers correspond to the
recommended land pattern after rotation: end pads1.2 by1.2, wiper1.5 by1.6,
end spacing2.0 and longitudinal row separation3.25 mm. This is a source drawing
comparison, not native DRC, solder-joint or installed fit qualification.
RVO1109 remains rear-facing at the source origin(34.5,37.4) with a6 mm tool-diameter
reservation. Bourns calls for a1.7 mm cross-slot tool and shaft force below4.9 N.
A tool-tip dimension does not establish shaft/hand clearance through the enclosure,
seating support or freedom from nearby wiring. Confirm the actual rear access and
screwdriver approach on the assembled structure; never move locked hardware to fit.
The20-cycle rotational endurance test (TRS±10%) is not an unlimited-use front knob.

JLC's exact product lists SMT Assembly / Economic and Standard. This is a dated
catalog route, not an accepted project BOM/CPL or allocated stock. Bourns specifies
0.15 W at70°C and50 VDC maximum, whereas JLC lists100 mW. Preserve both observations;
do not silently normalize the catalog or qualify a delivered lot at150 mW. Actual
segment dissipation, ambient derating and delivered-lot/process conditions remain
open. Do not use full-track voltage alone to qualify a loaded wiper.
Reflow is recommended; aqueous cleaning and flow soldering are not recommended.
Flux exposure and shaft force need control. A mixed SMT/THT assembly must protect
this open-frame part during later soldering/cleaning; generic JLC support is not
that process approval.

## What source arithmetic establishes

The manufacturer±25% track tolerance gives15–25k total resistance. End resistance
is not ideal zero: for values above1k the maximum is2% of total (up to500 ohms at
25k); contact resistance variation is5%. Angular travel is270±20 degrees. The
unloaded ideal divider's maximum Thevenin resistance isR/4, up to6.25k; that
calculation is not the loaded HF node impedance or an adjustment-voltage guarantee.

The retained AS3340D primary document (2020 v.7, pages1–2) assigns pin7 to HF
tracking, pin13 to linear input, Rs to V/oct scale and RZ/RT to compensation.
The existing source has a20k track between HF_PIN and AGND with its wiper at
LINEAR_REF. That node also sees1.2M from+12V, the core linear input and470 ohms
plus10nF to ground. It is not an unloaded divider. At DC with an ideal open capacitor:

`(VHF − VW)/Rt + (12 − VW)/1.2M = VW/Rb + Icore13`

Here Rt is HF-to-wiper and Rb is wiper-to-ground. Both core input current and HF
output voltage depend on the operating point. The script checks this KCL and
segment-power expression `(VHF−VW)^2/Rt + VW^2/Rb` at explicitly hypothetical
points. The470 ohm/10nF branch matters dynamically. No inferred HF voltage, hertz,
cents span, endpoint coverage or measured tracking is reported.

Other existing controls provide nominal, source-derived adjustment authority:
BASE's±5V through1M corresponds to±5 microamps or±0.5V at the100k pitch input;
SCALE's1.5k+1k provides an ideal nominal1.5–2.5k interval; RZ's24k+10k gives24–34k.
These are conditioned arithmetic with nominal rails/fixed resistors, not guaranteed
as-built frequency spans. Pot end resistance, tolerances, source loading, core
spread and temperature remain. BASE shifts pitch; SCALE changes V/oct; HF corrects
high-frequency behavior. Final front TUNE/FINE tuning cannot fix scale/nonlinearity.
No new precision acceptance target is introduced; the owner's1 V/oct tracking intent
and Stage26's A01–A06 scope remain unchanged.

## Concrete next boundary and DIN/wiring recommendation

Stop source-only closure here. An assembled oscillator must demonstrate that the
existing BASE/SCALE/HF controls can reach the intended base and1 V/oct ratio and
retain useful high-frequency tracking after adjustment, with actual supplies,
component population, warmup and temperature recorded. Check interaction and
recheck low frequency after HF adjustment. Measure usable end margin and segment
loading; a nominal range calculation cannot establish unit/lot coverage. This is
physical qualification, not a request for a tighter musical precision target.
No prototype order, physical calibration or native run is authorized by this packet.

Reuse the unsent [Stage25 fabrication specification](../stage25/fabrication-request.md)
without repeating its completed audit. Practical first route remains a precision
fabricator/assembler able to accept the exact HARTING drawings, initially evaluating
JLC's tighter diameter option. Before physical binding, that process must explicitly
answer: finished plated versus drill diameter forØ1±0.1; theØ0.05 positional zone
and datum across96 pins (not±0.05 axis error); femaleØ2.8+0.1/−0 fixing-hole size,
plating and registration; thickness/seating/mating alignment; exact-part mixed
SMT/THT sequence and inspection. Tighter diameter alone does not close position
or the2.8 mm holes.

For wiring, prefer assembler-completed labeled harnesses/terminations with documented
pin-to-pin continuity, insulation, strain-relief and service access. The concrete
missing deliverable is an assembly drawing identifying wire gauge/insulation,
length/slack, termination method, anchor/strain-relief load path and inspection for
every retained connection at locked geometry. Do not invent wire lengths, substitute
connectors or assume hand soldering by the owner. If the process cannot accept the
existing drawings, an alternate fabricator is the first comparison; an adapter or
new connector arrangement requires a separate owner-approved architecture change.
No external contact has been made.

## Verification

The generator deterministically emits the complete source inventory and report.
Negative tests reject wrong20k variant, pin reversal, sourcing mismatch, ratings
substitution, omitted packages/units/NCs, shorts, metadata changes, invented physical
coverage and invalid ideal-endpoint arithmetic. The live guard protects every old
file except README/WORK/check entrypoint; the previous checkpoint executes in a
frozen worktree. Independent review binds source and generated bytes.
Native request **NONE**. Production CAD, placements, decision.json,
KEEP_K1402_INCUMBENT, historical FAIL receipts and parked PRs remain unchanged;
PR286 remains draft. Electrical acceptance remains open.
