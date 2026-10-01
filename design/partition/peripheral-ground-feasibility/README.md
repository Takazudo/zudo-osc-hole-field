# Bounded O and EL ground prerequisites

These six unselected source definitions support issue 38's complete return
network. They do not complete the downstream octave/optical PCB issues or
accept contact, manufacturing, current, resistance or voltage requirements.
No full operator is scheduled by this source.

O1–O5 retain three source footprints, one locked selector and seven GH grounds
each. EL retains 144 source footprints, twelve fixed optical hardware objects,
60 own-load grounds and twelve GH grounds. All original outlines, holes,
reservations, coordinates, rotations, pad geometry and pin/net assignments
remain. Exact source contacts are reconciled independently between the netlist
and partition/physical-package crossings. No track, via or keepout exception
is added by this initial proposal.

The two explicit 35 um nominal foils retain the original 1.6 mm O and 0.4 mm
EL totals. Positive dielectric gaps are 1.53 and 0.33 mm respectively. These
are source-defined nominal geometries, not manufactured copper or stack
interval guarantees. Actual enabled foils and native depth must agree.

The complete PCB project is derived before native loading from the retained
canonical JL PCB-project template plus each original schematic-only project.
It preserves the target schematic sheets/text variables and all unrelated
template values. The template's cached JL top-level-sheet entry is replaced
by the empty PCB-only target cache; the actual target schematic is separately
copied and checked by native parity. Declared changes are filename, three source net classes and
four rail/ground patterns; the related global minimum track width increases
from the template's 0.1 to the source's 0.2 mm. The 0.5 mm copper-edge gate and
all other global rules remain exact. Default/Rails/Ground widths are
0.3/0.4/0.5 mm and all class clearances are 0.25 mm. The project format version
is the retained complete template's version 3; the original version-1
schematic project remains unchanged. No custom keepout waiver is present.
Copied schematic/rule and derived project bytes are checked before/after
native validation and before receipt publication, never rebound to output.

The fresh native BOARD constructor serializes its pinned Default-only class
record and empty patterns during initial synchronization. That intermediate
project has its own deterministic expected bytes and is checked in full.
The loaded board then receives the declared source classes before saving,
adding any ground fill or running DRC. The final companion must return to the
original complete source-derived expectation. Only the exact retained 10.0.6
constructor record is accepted; no arbitrary native JSON delta is ignored.

The first O stage adds only source-owned F/B AGND fill and requires native
rules/parity zero and all seven grounds connected. Empty isolated fill remains
empty; no numerical connection is invented. EL initially exports bare source
geometry for planning and is explicitly model-prohibited, even if rule/parity
checks pass. Any eventual full EL candidate must connect all 72 source grounds
and pass the same native/source/companion gates. Missing rail/signal routing
is retained as complete named prerequisite omissions, not final PCB acceptance.

Generate each definition with:

```
python3 -m scripts.pcbgen.generate_peripheral_ground \
  design/partition/peripheral-ground-feasibility/proposal.json \
  osc-octave-1 design/partition/peripheral-ground-feasibility/osc-octave-1.json
```

A fresh native build uses the reviewed `build_peripheral_ground.py` under the
machine heavy guard and pinned `scripts/kicad/run.sh`. The six native jobs run
serially after source review. Actual EL/O numerical entry remains prohibited
until a separately reviewed mandatory entry gate admits a successful complete
native prerequisite and its exact current source epoch.

Before baseline capture, the new two-foil stack is serialized with exactly the
four editor defaults that pinned KiCad 10.0.6 adds on resave: epsilon_r 4.5,
loss_tangent 0.02, copper_finish None and dielectric_constraints no. The source
serializer requires the exact original stack, inserts only these fields and
records before/after board and stack hashes. They are editor metadata, not
material, finish or process evidence, and are not used by the DC conductor
model. Every physical band and all other setup bytes remain unchanged. The
shared plane-preparation preservation gate stays strict.
