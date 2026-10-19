# Stage47 work scope

Parent explicitly selected the Stage46 next decision: a disposable local reroute
of retained signal copper around R8270, beginning with In3.Cu 1_PROTECTED.
Preserve footprints, netlist, stackup, front hardware and contact assignments.
Acceptance is exactly R8270:2/main AGND merge117→116, no other partition change,
zero new native rule/parity errors and fresh refill/DRC replay. No canonical
adoption or manufacturing action is authorized. All earlier stages remain intact.

Input: Stage44 B1+B2 owned board d1f79d02…; repository/PR head checked at
9e01349b8ff94d92d88c4095220938210ddc2c3c, draft. Latest issue comments are the
completed Stage45/46 reports; PR has no conversation comments or competing work.
Portable bootstrap was already fully consumed in this chat; not rerun.
`pnpm circuit:check` passes before edits, retaining68manual lines/0placements.
No full historical replay or canonical regeneration is duplicated locally;
exact-head CI supplies repository-wide coverage, as in the approved prior stages.

Proposal replaces only e5c9ec98-084e-5361-a6f6-d8875087ae94 by four 0.2mm
In3.Cu segments between its original endpoints, plus one 0.7/0.3mm AGND through-via
at native(270.3,133.3). B.Cu LED_K stays unchanged. New signal routing stays in
the rectangle x270.4–271.025,y131.6–135.9; no broad relocation is needed.

First native directory was accidentally one level deeper than baseline.
The same board proposal yielded116opens/0ruleerrors/0parity but199capped
lib_footprint_issues warnings from unresolved relative library paths. Preserved
as .circuit-cache/stage47/trial1; not accepted. Repeat uses a fresh flat owned
directory .circuit-cache/stage47-trial2 with the original library path depth.
No rule threshold or dependency is changed to hide the setup failure.
