# Source-only native-parity compatibility repair

This checkpoint preserves the complete Stage17 source and RUN001/RUN002 receipts at
`6b8c54a08639bc4b3ba11f9851c56acff47b76f5`. RUN001 remains UNKNOWN; RUN002 export
succeeded but full parity remains FAIL. No new native command, version probe,
container, installation or admission is executed here. All CAD remains an
unvalidated draft. Source checks are not electrical acceptance.

## Bounded representation repair

`stage18_compat.py` parses the independently checked original schematic, packs
whole packages into 20-unit sheets, and regenerates a separate hierarchy.
Every symbol/pin UUID, reference, pin/net/NC assignment, value, identity, unit
property and population flag is preserved. The 118 references, 561 pins and
154 unit UUIDs include all 22 excluded non-BOM/non-board land annotations.
U7102 and U7106 no longer cross sheets. Shared immutable Stage17 libraries are
referenced by the new tables; native input preparation must retain this relative
stage17/stage18 directory layout. No canonical board or locked placement changes.

## Pinned exporter rules

The inspected KiCad 10.0.6 source URLs and byte digests are in
[exporter-source.json](exporter-source.json). CLI `--format kicadxml` selects
NETLIST_EXPORTER_XML with option zero. Its GNL_ALL output does not set BOM or
board filtering. In contrast, NETLIST_EXPORTER_KICAD forces GNL_OPT_KICAD,
which removes on_board=no components and pins. Generic XML should preserve
annotations and emit exclusion properties. This remains a source prediction
until a separately admitted native export verifies it.

Component representative selection is minimum UUID within a sheet; extra-unit
UUID collection is sheet-local. Properties come from that representative plus
sheet fields and exclusion flags. Fields use the distinct all-unit aggregation
algorithm: minUnit initially equals the representative's unit; each visited
unit overwrites existing custom fields only when its unit is below the running
minimum, and otherwise supplies only absent keys. Mandatory nonempty values use
a separate rule; this bounded verifier requires uniform mandatory values.

KiCad's EE_RTREE iteration is spatial, not file, UUID or numeric-unit order.
The verifier enumerates the at-most-five-unit permutations through that exact
algorithm and compares the **entire field dictionary** to one feasible result.
It does not select values independently by field, infer traversal from native
metadata, or require properties to equal aggregated fields. Traversal uncertainty
is explicit; all unit metadata remains separately retained, including metadata
not observable in a component-level aggregate. Native export cannot prove every
unexported per-unit field; preserved source hashes and unit checks cover those.

## Strict observation and reversible names

`stage18_observation.py` parses generic XML E, requiring the exact 10.0.6 tool
string (this is format checking, not proof of execution). It rejects missing or
extra references, pins, NC endpoints, unit UUIDs/slots/library pins, duplicate
keys, rewiring, identity/metadata changes and population-flag changes. Every
source NC must be present as a unique unconnected singleton with a no_connect
marker; omission is not silently accepted. RN7102's unused ends and both EP9
AGND connections remain in the full contract.

Source net text is mapped through KiCad CTX_NETNAME and recursive UnescapeString
semantics. Both mapping directions and internal names are retained; collisions
are rejected before comparison. XML names are already decoded and are never
decoded again. Source and native duplicate names fail closed. Metadata field
names also reject decoding collisions. The comparator retains complete unit
metadata separately from both native channels.

## Source-only commands

```sh
python3 scripts/architecture278/implementation/stage18_compat.py
python3 scripts/architecture278/implementation/stage18_compat.py --check
python3 -m unittest discover -s scripts/architecture278/implementation -p 'test_stage18*.py'
python3 scripts/architecture278/implementation/check_source.py
```

The integrated source guard runs all prior stages and the new checkpoint.
The baseline guard already failed because Stage17's broad source-discovery glob
now sees six helpers added after its original report. The Stage18 predecessor
check accounts for exactly those six at the baseline commit, verifies the old
guard hash at the Stage17 publication, and compares every other report field
and review binding unchanged. Historical reports are not regenerated. The new
preservation check protects every pre-existing tracked file except WORK.md and
the reviewed check_source.py integration. No aggregate/native regeneration is permitted in this increment.
Synthetic XML tests are not native evidence. See [NEXT-NATIVE-REQUEST.md](NEXT-NATIVE-REQUEST.md)
for the proposed next action; it requires fresh approval and live admission.

Nineteen passive MPNs remain unresolved. DIN/land footprints remain
UNBOUND_SCHEMATIC_ONLY. These are procurement/PCB blockers, not reasons to omit
logical coverage or fit excluded annotations. No ERC, DRC, routing, simulation,
physical qualification, architecture adoption or electrical acceptance. PR286
stays draft/unmerged; PR260/277/285 and KEEP_K1402_INCUMBENT stay unchanged.
