# Bounded collet clearance result

This source calculation closes two **conditional local geometry checks** for
the reconciled58mm-offset family. It does not qualify the full feed, carrier,
manufacturing process or physical hardware. No native operation is involved.

The proposed outer collet is a flat-ended finite cylinder of radius2.0mm,
covering tangent arclength1.0…2.5mm from the raised anchor. The bore/material
split does not change the outer support bound. Any flange, screw head, lug or
other exterior feature falls outside this shape contract and needs its own
collision check. This calculation does not choose such features or a supplier.

For anchor height `H`, outward unit-axis normal component `v`, grip start `s`
and outer radius `R`, the exact distance to the datum plane is

`H + s*v - R*sqrt(1-v*v)`.

The minimum occurs at the minimum accepted height, grip start and normal-axis
component. The C1 direction requirement permits an angular cone of
`asin(0.01)=0.572967°`; the actual collet axis must independently qualify inside
that cone and align with the straight gripped wire. Position tolerance alone
does not establish axis alignment.

| Bound | mm |
| --- | ---: |
| Minimum anchor height |1.950000 |
| Exact bare-cylinder gap, including axis cone |0.797966 |
| Outer-profile closure |0.050000 |
| Local board warp |0.100000 |
| Thermal displacement |0.050000 |
| Retention motion |0.050000 |
| Full independent registration allowance |0.100000 |
| Remaining board gap |**0.447966** |
| Required residual |0.250000 |
| Margin over requirement |**0.197966** |

Full registration is retained even though the measured anchor-height control
may overlap it. No cancellation credit is taken. The capsule enclosure alone
would leave only0.136177mm and fail to establish the criterion; that insufficient
enclosure bound is not evidence of actual contact. The finite-cylinder support
calculation resolves this distinction without moving canonical hardware.

The second check covers all twelve collets against2,430 retained/new source
reservations, without a broad phase. It uses conservative XY boxes containing
the complete axis cone and cylinder, then expands for0.25mm of collet profile,
registration, retention and thermal closure and0.10mm of source profile closure.
All KA-B/KB-F source courtyards, supports, tool columns and loom reservations are
included, along with six retained bulk reserves and the reconciled KB monitor.
Even the opposite-face monitor is checked in XY. The minimum remaining gap is
**3.233304mm**, between KB collet3/6 and the moved monitor reserve. Because this
is an XY separation, it holds throughout axial withdrawal independently of Z.

The evidence binds `process-budget.md`, the reconciled overlay, robust curve,
frozen producer lock and historical bulk-reserve inputs by SHA256. Regenerate
the evidence after changing any bound input. The calculation uses analytic
support/coordinate bounds with ordinary floating arithmetic; it is not a
certified directed-rounding or manufactured-tolerance certificate.

```sh
python collet_clearance.py --check
python -m unittest test_collet_clearance -v
```

Run from this directory. Tests include sampled cylinder surfaces inside the
axis cone, the insufficient capsule certificate, omitted closure protection,
invalid inputs, and preservation of negative physical/native gates.

Still open: actual axis and exterior-shape qualification; bore retention and
insulation; revised arms, joints and load path; wire-to-collet/arm clearance;
complete feed sweep; actual continuous C0/C1/C2 wire shape; all100 adjustments;
physical and native acceptance. The two conditional local passes do not turn
any of those gates true.
