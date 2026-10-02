# Partial control-board copper checkpoint

`boards/osc-control/osc-control-routed-draft.kicad_pcb` is a reproducible,
**partially routed, unvalidated draft**. It preserves the current source
layout's 418 packages, 36 supports, 139 fixed controls, actual outline, stack
proposal and reservations. The canonical partition outline remains separate.

`copper.json` owns 1,605 track segments and 402 through vias, including all 150
main-terminal array vias. Coordinates are native integer nanometres. The
constructor appends only this copper and the source-defined ground pours to
the checked labelled layout, preserving every other input byte. Each main
array's complete annuli remain inside its owning 4 × 4 mm terminal.

Fresh KiCad 10.0.6 checks give zero DRC violations, zero schematic-parity
findings, **323 open edges** and **344/344 connected ground contacts**. All
**16 local IC/bypass rail pairs are connected**, with at most 2.535 mm between
supply-pad centres. Independent reload/refill retains the connectivity.
`ratsnest.json` contains the complete per-net inventory; the truncated CLI
DRC item list is not used as a connectivity count. A local bypass connection
does not establish its complete rail feed or current-carrying performance.

The current placement corrects twelve remote bypass capacitors by moving ten
complete IC/bypass groups (22 unfixed internal packages). All other component
positions remain unchanged. The earlier 366-edge checkpoint is retained in
git history. Its copper at the moved ICs is not reused as valid routing:
obsolete signal-net routes and incompatible/dangling copper were removed,
leaving 432 open edges. Sixteen local bypass connections and ten local signal
links then reduced that count to 406. Seventeen short signal links using
off-pad layer changes subsequently reduced it to 389. Source metadata records the removed
copper and new links. All failed local trials remain available in the cache.

A bounded continuation with all existing copper locked produced a timed-out
partial session. Only new copper was imported, with the source footprints
preserved exactly. An unfinished two-track stub was removed. The resulting
1,605-segment/402-via checkpoint preserves all 1,183 prior copper objects and
reduces native open edges from 389 to 323. Fresh DRC/parity and independent
refill pass with all 344 grounds and sixteen bypass pairs connected. The raw
autorouter timeout is retained; this is not complete routing.

The earlier recovery from a partial autorouter session corrected omitted
mechanical-footprint names and nanometre import rounding, then repaired four
ground islands exposed by fresh refill. Those are historical recovery stages,
not permission to reuse their electrical receipts for this source revision.
The current checkpoint is replayed from explicit copper without rerunning the
autorouter.

Run the complete check with the shared heavy guard and pinned oracle:

```sh
bash scripts/kicad/run.sh python3 scripts/pcbgen/check_control_copper.py
```

The check replays the underlying layout and copper, compares every generated
PCB/project/schematic/rule byte, checks all sixteen native bypass distances
and rail connections, audits the full ratsnest and ground-contact inventory,
and independently reloads/refills the board. A displaced native capacitor is
rejected by a negative control. Source/input immutability is checked. Failed
workspaces remain local. Native front/rear previews are bound to the exact
PCB and image hashes in `views.json`.

The source relocation passed aggregate regeneration. The rebuilt labelled
layout passed native replay with zero rule/parity findings and all 418 labels.
The copper cleanup and local-routing trials passed native DRC and independent
refill. Combined final replay, 26 targeted tests, documentation build and publication
checks passed in 83 seconds. Strict link checks retain the existing single
workbench exception. All 482 PCB tests and 281 source/check tests pass for the bypass-repair
checkpoint. Final replay, 26 targeted tests and publication checks for the seventeen
additional links passed in 81 seconds. Integrated CI is pending.

Current-source resistance/current analysis, global rail-distribution
compliance, protection, source/inlet selection, manufacturing and installed
fit remain open. The four-layer, 2 oz, 1.6 mm stack remains a proposal. No
historical ground/current receipt is rebound and no fabrication or order
files are produced.

Final combined native replay, 26 targeted tests, documentation build and
publication checks for the 323-edge continuation passed in 88 seconds. The
existing workbench link exception remains unchanged. Integrated CI is pending.
