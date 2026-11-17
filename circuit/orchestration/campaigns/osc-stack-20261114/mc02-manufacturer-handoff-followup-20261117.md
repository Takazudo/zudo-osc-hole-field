# Manufacturer handoff follow-up and project mapping preparation

2026-11-17. Active owner: Codex coordinator on x0x WSL. This follows
[#362 handoff6948020518](https://github.com/Takazudo/zudo-osc-hole-field/issues/362#issuecomment-6948020518)
and supersedes the catalog-only source-search boundary. No adoption or physical
access validation is claimed.

## Source acquisition state

The owner supplied both PDFs through the private artifact channel. Local PDF
signatures, byte counts and SHA-256 hashes match the handoff; all physical pages
were visually reviewed. Earlier ordinary official-URL requests returned403 and
were not retried or bypassed. The transfer dependency is resolved.

| Document | Verified local SHA-256 | Inspection |
| --- | --- | --- |
| Keystone DWG4708,2011-05-26 |`b31545f168c90a3bc2d44f06b0f0a3003a6aaeef002b4366e11a44230637af44`|172,371bytes; one unnumbered sheet; blank revision grid, CODE C is not a revision |
| Hirose EDC3-150229-11 |`c3257beed2331e5c95e176bc28441b04b804301a44c11b462e486fb5cc649d07`|1,059,562bytes; ten physical pages; DIS-F-00013152,20220401; printed sheets6/7 retain /9 |

The verified drawing gives4708 height2.40±0.25mm, M3×0.5, steel/zinc plate.
The older catalog explicitly says nickel; that historical finish/version/lot
question remains open. The current official product page agrees with zinc.
Hirose contact1 is left in both connector/PCB views, including40contacts; the
cable view differs and cannot establish assembled cable parity by itself.

## Independently completed project-source work

[Connector mapping tool](../../../../scripts/checks/mc02_connector_mapping/README.md),
commit1608824d115bc610c1e4bc29a9acb568accd7c4a:30source pins bind engineering2c53715;
61links/122virtual endpoints reproduce the retained field generator, including
boardBface,field-to-slot direction and logical conductor order. Seven fixtures and
independent extraction passed. Physical references, rotations and local/global
numbered-pad coordinates are absent from this virtual-field model and remain null.
A literalFH12name scan of10board files has0matches; this is not an exhaustive
identity analysis of arbitrary custom footprint names. Logical position1 is not
a verified physical contact1. A source drawing can support future coordinate
mapping, but cannot retroactively create physical footprints in this model.

[Fastener audit](../../../../scripts/checks/mc02_fastener_stack/README.md),
commit50d7171f923ec8b6e23c73fb7400feb52f98c9bd:the four fixed sleeves are U1/JL(74,28),
U2/JR(244,24),L1/P(93,276),L2/P(244,230). Plane-derived nominal grips22.2/20.2mm
match the retained threading record. The verified drawing update at e64e6b94d85cbb9e704204d6403097deb2ffa661
uses nut2.40±0.25mm in conditional arithmetic with the assumed25mm screw. Ten
fixtures and independent audit passed. Washer thicknessW plus required protrusionP
has conditional nominal capacity0.15–0.65mm at long sites,2.15–2.65mm at short sites.
All four remain NOT_SHOWN: screw/grip tolerances,washer identity/thickness,required
protrusion and finish/version discrepancy are unresolved.
Positive residual is not a guaranteed washer allowance or thread engagement.

## Source distinctions to preserve

- The retained20page catalog,hash9f056f58ff000739633cc3cb7697ba185967083dcf1429b7ab10783b3f55bac5,
  printedpage11/index10 upper horizontal recommended-dimensions block explicitly
  says stiffener thickness should be0.188mm minimum. Root visually rechecked this.
  It is a catalog recommendation, not a universal guaranteed material bound.
- The new10page engineering drawing shows188µm in a reference
  construction example onpage3. These are distinct source claims and contexts;
  retain both rather than replacing one with an unsupported general rule.
- Verified parenthesized open4.8mm and90° in parentheses are reference geometry, not guaranteed
  maxima. They cannot validate the existing assumed5mm open envelope or31access cases.
- Verified closed2.0±0.2mm must be reconciled with actual seating/placement; body
  height alone is not mounted clearance.
- Verified central manual actuator operation cannot be satisfied merely by a
  narrow tool-reach corridor. Manual approach,holding/support and thread/fold
  sequence remain separate evidence obligations.
- New4708drawing specifies steel/zinc; retainedcatalog sayssteel/nickel.
  Do not silently choose finish or claim version equivalence.

## Continuing work

Verified access evidence at7479022101c3f59afab022f9c5ffaf7d9c3d77f6 exposed
two actual procedure conflicts: steps7/12 permitted a plastic tool. Canonical
producer/renderer correction5620eea27dd2e3232f4ba81a4592660c3f439a26 requires
central hand-only operation. Focused regeneration and23tests pass; only two
instruction strings and two producer hashes change in the JSON. Geometry,
61links,122connectors,31NOT_SHOWN cases,12supporting-hand operations and maximum
17threaded ends are unchanged. Five consumer rebindings at bb01f7f235862844e217da82d42a96fb80134b3a pass57tests;
source/amendment/engineering attribution is explicit in actual reports.

Relative projection d3b0d24d025b9abffea66a6934aaf837ab101b32 supplies122conditional
contact vectors with8tests; actual field-to-pad-row registration, physical
rotation/pad1 and cable parity remain unknown. Continue source-derived envelope
and mapping preparation without inventing these missing physical placements.
Existing successful native aggregate remains bound to its original inputs and
is not rerun for these instruction/evidence changes. DRC,fill,formal adoption and
manufacturing remain held. The independent E5 room-exchange pilot is also being
reviewed; this received-source checkpoint is not a stopping point.


## Conditional land registration, not an observed CAD placement

Envelope audit 1d5f6833ffb193bac9420a99db9b31dcdb058389 and recommended-land registration audit ec4d6e1cdbbd3b8f9343f3349686c45e9c417108
passed independent review and9tests each. All122virtual endpoint rectangles are
source-bound. The nominal6.1mm field depth exceeds the verified maximum5.9mm body
depth by0.2mm total; a centered0.1mm residual is only a counterfactual.
Maintaining0.25mm per side at maximum would require6.4mm, not an adopted change.

A separate recommended-PCB-land model derives nominal Y[-0.65,4.35] and outer
interval[-0.7,4.6] from pad1.3±0.1,gap1.5±0.1,tab2.2±0.1. In the declared
row-midpoint frame and centered virtual field, zero extra edge clearance permits
row translation X[-0.2,0.2],Y[-2.35,-1.55]. At0.25mm extra per side, Y becomes
[-2.10,-1.80] but X is empty:[+0.05,-0.05]. This is because source Gmax leaves
only0.4mm total across the field. These are conditional robust land-only
constraints, not measured registration, exact GD&T optimization, a complete
body/terminal union, or proof of installed connector access. Actual and adopted
registration remain null. No field enlargement or CAD change is made.
