# Conditional paired-row feed proposal

**SOURCE PROPOSAL ONLY — NOT APPLIED, NOT ADOPTED, NOT PHYSICAL FIT.**
This is a concrete six-wire, twelve-collet, four-rail arrangement with continuous
10 mm withdrawal envelopes and joined electrical arithmetic. It is owned by the
integration coordinator; the mechanical and power lanes' frozen producer inputs
are unchanged. All source inputs are locked to `29140d4e` in `source-lock.json`.

The current power contract specifies F.Cu at both new endpoints. This alternative
uses **KA B.Cu → KB F.Cu**. F/F was a provisional generator choice, not a fixed
user or connector requirement. This reversible proposal is permitted under the
epic without a new user permission question; the historical power contract is
unchanged pending source-owner reconciliation. See the
[provenance and tolerance correction](face-provenance-and-tolerance.md).
Neither source review nor this face choice authorizes native execution or physical
changes. The proposal does not prove every other permitted arrangement impossible.

## Concrete arrangement and comparison evidence

`offset-proposal.json` contains all twelve exact terminal IDs/lands, six bulk
reserves, the KB monitor reserve, 52 clamp/arm solids, formulas, three example
poses, source checks and negative gates. `preview.svg` shows the 0/5/10 mm poses.
The existing wire order and IDs remain +12V, −12V, +5V, AGND1/2/3.

Free anchors form two three-wire rows: KA X23/40/57, Y15.5/24.5 mm; KB is offset
52 mm in X. Their heights are 1.5 mm into the inter-board gap. Lands are centred
where straight continuation of each fixed tail reaches its board face; their
6×6 mm reservations are checked against retained source obstacles. The deep
alternative uses KA front/back −100/−101.6 mm, KB front/back −126/−127.6 mm.
KB moves rearward by 0…10 mm. Fixed non-core placements and canonical copper are
unchanged. Bulk/monitor reservations have explicit XYZ envelopes; no new MPNs
or electrically realized terminal instances are claimed.

Each wire has a 64 mm cubic Bézier and two straight 2 mm clamping tails. The
endpoint directions are fixed through withdrawal. Alternating Y bows
`[+,-,+,+,-,+]` prevent the collision found with all-positive bows. Two straight
land bridges add 5.498249 mm, consuming that amount of the 10 mm preparation
allocation. The 78 mm cut ceiling leaves 4.501751 mm for other preparation.
Solder, stripping and insulation transitions still require qualification.

Each collet grips tail arclength 0.75…2 mm, outer radius1.7954 mm. Its PCB-facing
stem joins a short X dogleg, a Y stub and a shared near-face rail. `clamps.py`
defines their actual boxes and collet axes, including intended contacts. KA
rails join the fixed carrier; KB rails join its **moving carrier**. The X−1.5 mm
rail end is an attachment interface, not a qualified fastener or enclosure joint.
Solder carries neither board weight nor the carrier attachment load.

| Construction | Evidence / result |
| --- | --- |
| Conventional F/F U-loop | Minimum πR =81.392 mm before tails/preparation; fails the existing full-copper-allocation cut certificate. This rejects that construction, not all F/F routes. |
| Shared-XY facing rows | With R≥25.908 and gap24.4, the short-curve chord bound permits ≤1.006 mm axial travel, insufficient for10 mm. |
| Free circular offset arc | Sufficient bend radius, but clamp tangents rotate35.419°; rejected as a fixed-clamp construction. |
| Fixed-tangent, all-positive bows | Adjacent wire centreline separation2.216598 mm <2.5908 mm OD; actual collision. |
| Fixed-tangent alternating bows with explicit carriers | Positive nominal continuous bounds below; conditional face/cut/copper/qualification gates remain open. |

The first two constructions' reproducible rejection arithmetic is in
`check.py`/`proposal.json`; those files retain their own deliberately rejected
shared-XY coordinates. `offset.py`/`offset-proposal.json` is the current alternative.

The rejection theorem is explicitly restricted to a fixed-length centreline
L≤πR. Project its tangent onto the midpoint tangent: the curvature limit bounds
the angle by |s−L/2|/R, giving chord≥2R sin(L/(2R)) after integration. For a fixed
XY offset and axial gap g→g+δ, the squared chord increase is2gδ+δ². Combining the
installed lower chord bound with the withdrawn chord≤L gives the necessary
condition `L² − [2R sin(L/(2R))]² ≥ 2gδ+δ²`. It does not establish an unrestricted
impossibility theorem for longer curves or different service motions.

## Positive nominal margins

Bounds cover 200 withdrawal intervals ×512 Bézier parameter intervals, plus
both tails and land bridges. They use derivative/position boxes, not just three
display poses. Source obstacles include courtyards, through-loom reservations,
tool columns, supports, protection and new bulk/monitor reservations. Broad-phase
completeness is asserted against every wire/arm envelope. Full source polygons
must be rectangles; a malformed polygon is rejected rather than silently boxed.

| Quantity | Conservative lower bound, mm |
| --- | ---: |
| Bend radius |26.266221 (margin0.358221 above25.908) |
| Wire to source/new reservation |0.254600 |
| Wire to another wire |3.710872 |
| Wire to clamp/arm, excluding its own collet bore |0.145325 |
| Clamp/arm to source/new reservation |1.663821 |
| Foreign collet to collet |2.710872 |
| Wire to enclosure XY |0.338967 |
| Clamp/arm to enclosure XY |0.500000 |
| Raised free wire/tail to bare PCB |0.204600 |
| Collet capsule to bare PCB |0.113821 |
| Carrier arms to bare PCB |0.150000 |

The land bridges intentionally terminate at their own lands, so the raised-wire
bare-PCB bound does not apply to that termination region. The own-collet bore is
the only wire/collet contact exemption. A finite-radius exit proof across the
complete gap/handle rectangle prevents the free wire tube from clipping its own
flat-ended collet annulus. For t≤0.05 it bounds axial advance by mt and transverse
offset by Mt²/2, with m²−rM≥3478.051445; thereafter axial distance exceeds the
wire radius monotonically. A centreline-only half-space test would not suffice.
Foreign collet separation follows from the continuous wire-pair bound minus
the two0.5 mm shell increments.

These are floating numerical engineering bounds with explicit handle/arithmetic
padding. Independent96/192-point quadrature agrees within2.42e−13 mm; tests also
use adaptive integration and off-grid samples. This is not certified interval
arithmetic, manufactured tolerances, passive wire equilibrium or physical fit.

## Joined electrical budget

All18 existing main routes are recomputed from their frozen registered continuous
source curves, including fan/solder/adapter geometry. Their maximum upper cut
length with10 mm allowance is103.244852 mm; use a **qualified ≤104 mm main cut**.
The new feed needs **≤78 mm**. These are manufacturing requirements, not measured
cut lengths. The required global copper targets are **rail≤0.15 mΩ,
return≤0.20 mΩ**, counted once; these are stronger than the existing1/0.5 mΩ
ceilings and do not relax them.

Using0.013 Ω/m hot wire resistance,0.2 mΩ termination-pair resistance per
section, both main and new sections, and the full4.6 A on one return:

| Rail | Drop at proposed targets | Margin below20 mV |
| --- | ---: | ---: |
| +12V,2.1 A |19.7672 mV |0.2328 mV |
| −12V,2.0 A |19.4756 mV |0.5244 mV |
| +5V,0.5 A |15.1016 mV |4.8984 mV |

The counterchecks remain failures: existing full copper ceilings produce
22.9322 mV on+12V; a110 mm main cut with the proposed copper targets produces
20.2898 mV. No actual copper extraction, pad continuity, new plane realization or
resistance compliance is established by this allocation.

## Reproduction and open gates

Use the pinned numerical environment (numpy2.2.6/scipy1.15.3; the registered
main-route helper also uses the existing numerical requirements):

```sh
python check.py --check
python offset.py --check
python preview.py --check
python -m unittest discover -s . -p 'test_*.py' -v
```

Run from this directory. `offset.py` fails on frozen-input or numerical-version
drift. These are source calculations only and do not invoke KiCad or routing.
Independent Astra High review checked curvature/collision bounding, the corrected
negative-bow obstacle coverage, full land bridges, carrier geometry and budgets.

Remaining gates: producer face-contract reconciliation; terminal/collet/material/fastener and cut
qualification; tighter actual global copper extraction; complete peripheral
return model and all100 adjustment access; native/fresh/full-warning preservation
gates. `accepted`, `face_contract`, `clamp_assembly`, `actual_copper`,
`all_100_trim_access` and `native` remain false. The positive nominal clamp-envelope
gate is deliberately separate from full assembly qualification.

The smallest routing comparison is independently runnable after new parent
admissions: see `../minimum-native-request.md` and its exact JSON packet. It keeps
the29140d4e method epoch and compares O1/K1402 with O1/two-A. It is **not admitted
or run** by this source proposal. Incumbent K1402 remains selected; no PR merge,
canonical regeneration, fabrication, order or energization is authorized.
