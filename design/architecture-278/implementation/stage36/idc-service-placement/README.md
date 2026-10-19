# IDC service placement revision

This is a reversible source-only revision of [the standard IDC candidate](../standard-idc-assembly/README.md), baseline `2f30e91eaaea012dbf6eca5bff67ff088ba31d39`. It removes the two previously identified known-obstacle conflicts under the same planning allowances, and an additional package/grip overlap found by a broader screen. **It does not establish integrated fit, cable serviceability or a qualified grip.** All proposals remain outside canonical CAD; fixed front hardware, board outlines/planes, historical evidence and panel artwork are unchanged.

[Placement diagram](placement.svg) · [Complete coordinates and screens](candidate.json) · [Final review](REVIEW.md) · [Verification](VERIFICATION.md).

## Actual connector arrangement

Three ordinary ribbon links join local boards to the middle board. C-SIG uses D2510-6002-AR headers and 89110-0101 sockets (10 ways), J-PWR D2508-6002-AR/89108-0101 (8 ways), and J-SIG D2514-6002-AR/89114-0101 (14 ways). All are proposed 2.54 mm two-row, center-keyed assemblies. The sockets omit optional strain relief, so external cable support remains necessary and undesigned. Matching numbered contacts, polarity and every spare NC are unchanged; generated pad coordinates move with their connector. The mating face reflection, source dimensions and unresolved maximum/socket seating data remain bound to the previous candidate.

The ribbon links do not prescribe board spacing. The existing proposed board surfaces remain control z10–11.6, jack z35–36.6, middle z48.4–50 and core z74–75.6 mm. Separately, middle-to-core direct links use Samtec TSW-108-18-L-D / SSW-108-01-L-D for rear signal, and TSW-104-18-L-D / SSW-104-01-L-D for K-PWR, with proposed 970240321 spacers and a **24 mm face-to-face gap**. The prior conditional engagement4.55–6.13 mm remains unaltered; no extra spacing is needed to remove the two source obstructions. K-PWR remains +12V/−12V/AGND, without +5V.

| Reference / link | Previous center XY mm | Revised center XY mm | Rotation |
|---|---|---|---|
| J17901 control C-SIG | 218.5,297.5 | **218.5,299** | 0° |
| J17902 middle C-SIG | 274,286 | **274,165.5** | 0° |
| J17903 jack J-PWR | 212,170 | **212,171.5** | 0° |
| J17904 middle J-PWR | 292,154 | **292,152** | 0° |
| J17905 jack J-SIG | 208,108 | unchanged | 90° |
| J17906 middle J-SIG | 258,154 | **258,152** | 0° |

Only internal connector proposals move; no front jack, pot, switch or LED moves. This is not a routed-board ECO. Copper routing, connector lands and signal integrity must be designed before adoption.

## Resolve known obstructions without reducing allowances

**Middle C-SIG:** previously its expanded projection overlapped the core starting at y174. The 15 mm axial withdrawal trial allowed only8 mm installed assembly height, below the conditional assembly reference. Move J17902 ahead of the core instead of requiring core removal first. Move the other two middle headers2 mm toward y142 to open room. Including the subject's1 mm allowance plus2 mm grip width and the neighboring headers' own1 mm allowance, the open feasible Y interval for J17902 is **164.7122 < y < 166.6439** at fixed x274. Choose165.5. It clears the neighboring occupied connector columns by0.7878 mm in Y and the core projection by1.1439 mm, after the stated allowances. The 15 mm grip/withdrawal height ceiling becomes39 mm from the existing inner cover z105. Actual assembly height remains unknown, so this is a necessary source screen, not a fit pass.

**Control grip:** the old symmetric grip box reached x205.4289..231.5711 and intersected the side members ending atx206/startingx231. For y289..307 only, offset the existing proposed3 mm-wide members1 mm outward: leftx202..205, rightx232..235. Upper/lower portions retain their prior X locations. This leaves0.4289 mm on each side after the existing1 mm allowance and2 mm grip reservation. The joined-frame segments retain2 mm transverse overlap at each butt junction; joint details, stiffness and50 N capacity are not established.

The wider package screen also finds that the original control grip reaches RV1308's same-board courtyard endingy291.1. Move J17901 down1.5 mm to y299. Move the proposed mounting bridge fromy306..310 to307..311 and its two posts/holes from(213,308)/(224,308) to **(213,309)/(224,309)**; do not move the existing front pots. Bridge dimensions and z18..20 remain the same, as do6.4 mm posts and the proposed control tab endingy312. Hole diameter3.4 mm gives only0.3 mm bridge-edge ligament and1.3 mm board-edge ligament nominally; these are geometric observations, not strength approval. The open control center interval is **298.4561 < y < 299.6439**. At299, the grip clears the pot courtyard by0.5439 mm and bridge by0.6439 mm. The grip/withdrawal height ceiling becomes77.4 mm; measured height and real grip still remain unresolved.

**Additional first finding:** expanding the screen to all populated same-board courtyards identifies original J17903 grip overlap with R7105/R7107/R7108/R7109/R7135. Their furthest Y is163.64. Move J17903 down1.5 mm to171.5. Its open necessary center interval is170.9961..176.6439 mm (package/grip lower bound, board/body upper bound). Other same-board package, retained terminal-land and mounting-tool/body screens are empty at all six revised positions. The opposite-side pot courtyard is conservatively occupied even though a physical height model might later refine it.

Rejected alternative retained: rotating the control header90° at(218.5,292.5) would overlap RV1308's courtyard and through-hole area. It is not a clearance solution. No threshold or allowance was reduced to make the chosen revision pass.

## Service sequence and remaining boundary

Proposed sequence is remove the rear cover, support the local/middle PCB, grip the housing, and withdraw each ribbon socket axially15 mm into its individual reservation. Grip only one housing at a time: adjacent grip reservations may overlap. Each screen reserves the other connectors’ bodies plus their own1 mm allowance, not simultaneous hand volumes. The new C-SIG position removes the specific need to extract the core first. Release or reposition the yet-undesigned cable support without loading the IDC terminations; park the loose end before board removal. Fastener-tool access is checked against connector bodies, not assumed simultaneous with the larger hand/grip reservation. Housing grip geometry, force, actual disengagement travel, cable motion and parking are still unevaluated physically.

Moving middle C-SIG approximately120.5 mm invalidates its old short route; the endpoint-to-endpoint projected span increases substantially. The prior C-SIG route is **not reused** and no cable cut length, bend radius or service slack is invented. The shifted J-PWR/J-SIG endpoints likewise invalidate their exact old routes. New paths need actual exits, exact ribbon constraints and neighboring occupied volumes. Moving the obstacle out of the housing sweep does not prove the cable can follow it.

Unknown neighbor projections remain occupied. J17902 now projects over **J1610/J1710**; their exact installed rear seating, tails and attached harness Z are needed. J17901/J17903 have no hits against the retained unknown XY list, but that list is incomplete for harness motion. The side-carrier revision still projects over RV1408 and other retained supports over unknown pot/switch installations. Source positions alone cannot clear them. All unknown support hits are retained in JSON. Source-only calculation does not establish registration, bow, load path or50 N strength.

Minimum independent inputs remain the exact closed/mated height and exit datum for each socket count; ribbon static and repeated-flex/straight-exit/termination limits; bounded registration/bow; actual rear extents for the listed overlapping neighbors. No new owner choice is needed to record this reversible source proposal. Adoption, strength, cable routing and full assembly/removal stay blocked on those specific facts. No order, manufacture, energized check or front-position change occurred. The prior [unpowered checklist](../standard-idc-assembly/README.md#unpowered-mock-up-decision-checklist) applies with these revised coordinates and the corrected service sequence; its old two rejected placements remain historical evidence.
