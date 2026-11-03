# Stage17: isolated A01 schematic and library source

This increment starts at `4c4b42267d435bea38bee8196910d48f9f43f202`. The owner authorized candidate schematic/library generation in isolation. **All generated CAD remains an unvalidated draft.** No KiCad executable, version probe, native netlist export, ERC/DRC, simulation, PCB generation/routing or hardware action is part of this increment. Prototype availability remains UNCONFIRMED.

## Regenerate and check with Python only

```sh
python3 scripts/architecture278/implementation/stage17_schematic.py
python3 scripts/architecture278/implementation/stage17_schematic.py --check
python3 -m unittest discover -s scripts/architecture278/implementation -p 'test_stage17*.py'
```

Generated outputs live exclusively in [stage17/generated](stage17/generated/). `a01.kicad_sch` is the circuit root, with eight child sheets, local `sym-lib-table` and `fp-lib-table`, `A01Candidate` and `A01Transport` symbol libraries and the isolated footprint library. A separate `transport-graph.kicad_sch` is a source allocation drawing; it is **not included in the circuit hierarchy**. No canonical source is regenerated. Unknown or extra generated files cause failure rather than silent deletion. Historical Stage16 evidence retains its original meaning. The integrated source guard now uses a Stage17 wrapper for the historical packet scanner: its recursive library discovery sees the two new libraries and any local Stage16 source-copy bundle. The wrapper checks the exact two additions and fully re-verifies every Stage16 export before allowing its copied symbols; every historical field and old hash must remain identical. Arbitrary extra library files still fail. Direct historical `check_packet.py` reports discovery drift in this expanded workspace; the integrated guard checks the unchanged other packet generators and this explicit comparison instead. No historical report is rewritten.

## What changed

| Before | After |
|---|---|
| Missing KEMET capacitor assets and symbol bindings | Derived polarized symbols and rectangular land/courtyard source footprints capture the frozen Stage13 geometry for C7101 T491C475K050AT and C7102 T491D226K035AT. Pin1 is positive; no land, pose or capacitor selection changed. |
| LT5400 footprint without symbol/unit binding | Per-reference LT5400AIMS8E-2#PBF symbols have four resistor units and a separate exposed-pad unit5. RN7101 and RN7102 retain all eight resistor pins plus EP9AGND; unused RN7102 ends remain explicit NC. |
| Distributed86-package candidate source | Deterministic isolated hierarchy captures86 circuit packages,291 physical pins,120 logical units plus two EP units. Every connected pin has a global logical-net label at its source-derived symbol tip; every NC has an explicit flag. |
| Captured generic library names could suggest an unselected MPN | Per-reference isolated symbols and schematic properties retain blank MPNs for the same19 unresolved passives. Values, identities, units and pin maps come from the frozen input. No procurement decision is made. |
| Transport graph only in prior JSON | The circuit hierarchy also captures eight GH headers, two96-pin DIN connectors and22 non-BOM source-land annotations. Together with the circuit, all561 graph pins are represented in118 references/154 units. A separate diagram displays all320 allocated edges; the complete node/edge contract remains `transport-source.json`. |

Schematic positions are document layout only. They do not alter frozen component/land/board coordinates. Retained footprints and available local model assets are copied into the isolated library with recorded derivations; inherited fidelity and fit uncertainties remain. New capacitor models are not fabricated. Full-land mask/paste source capture is not an assembly-process qualification.

## Independent source parity

The ten connector references are deterministic J17901–J17910; source-land annotations are TP17901–TP17922. These are schematic references for already specified transport nodes, not additional selected circuitry. DIN identities remain HARTING09032966824 (middle) and09031966922 (rear). GH footprints are copied from the frozen sources. DIN and source-land footprint fields are deliberately blank and marked UNBOUND_SCHEMATIC_ONLY; no hole/drill/land geometry is invented. Source lands are excluded from BOM and board population. Logical capture does not make the complete assembly procurable.

The independent checker parses the generated S-expressions, traverses the actual sheet hierarchy and embedded symbols, derives pin coordinates and label/wire connectivity, and verifies the86 circuit packages and32 transport representations, units, identity/value fields, complete561-pin/net/NC assignment and library bindings against frozen inputs. Circuit footprints and GH bindings are checked; only the explicitly identified DIN/land rows allow blank footprints. Independent transport expectations are reconstructed from the graph and retained mechanical identity evidence, not the emitter output. It does not trust a generator-produced netlist as its oracle. Mutation tests exercise incorrect labels, missing/changed pins and identities, library inconsistencies and missing source graph edges. Deterministic regeneration and file-membership checks cover the complete output set.

The separate transport checker compares actual drawn wire endpoints and endpoint labels against each source edge. The full JSON roster preserves all561 nodes, including NC nodes absent from conductive edges. The graph drawing verifies paths separately because logical same-net equivalence alone cannot prove a particular harness path. Unified logical connector pin capture is now present, but DIN/land footprints, PCB coordinate/face transforms, actual copper and assembly materialization remain separate work. The 86 circuit packages are not a complete procurable assembly BOM. Allocated millimetres are not routed copper.

`schematic-report.json` records exact input and output hashes, independent checker results, unresolved identities and preservation. Review receipts disclose authorship and bind reviewed files. Test success establishes source consistency only. Native parser acceptance, actual exported netlist semantics, ERC warnings/errors and electrical correctness remain unknown.

## Remaining decisions and next action

The same19 passive MPNs are unresolved: C7104,C7105,R7101,R7102,R7103,R7106,R7108,R7110,R7112,R7113,R7114,R7115,R7116,R7119,R7120,R7130,R7131,R7132,R7135. No substitute, resistor adjustment, protection or bleed element is added. The proposed factory procedure remains unadopted/unexecuted; manual OFFSET is continuous with no centre detent, and the existing2mV postfactory static/1mV same-setting load-change criteria are unchanged.

The next verification operation is an **admitted** exact KiCad10.0.6 netlist export of `stage17/generated/a01.kicad_sch` to a fresh ignored run directory, followed by independent native-observation parity. Before even a version probe, the operator must bind the actual commit/input/output hashes, exact argv and output location, runtime capability proof, resource enforcement and timeout under genuine exact-run admission. Stage16's execution contract lists proposals, not permission or enforced limits. ERC is a separate operation; no historical warning allowance transfers. WSL/Mac or Cloud must satisfy the same requirements. Source generation is runnable now with Python; no native readiness is claimed.

Canonical boards, locked placements, `decision.json`, KEEP_K1402_INCUMBENT and all prior evidence stay unchanged. PR286 remains draft/unmerged, and PR285/260/277 remain parked. This increment does not adopt architecture or authorize manufacturing/hardware.
