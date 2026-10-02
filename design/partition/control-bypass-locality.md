# P-board bypass locality repair

A fresh native inventory of the partial control-board copper found all sixteen
assigned IC/bypass rail pairs disconnected. Twelve bypass capacitors were
22.53–171.01 mm from their own IC supply pads. The four previously compacted
slew-amplifier bypasses were within 2.30 mm. The existing generic capacity
packing did not enforce local P-board bypass groups.

The source now places the remaining ten complete IC/bypass groups together:
eight logic ICs with one capacitor each and two quad amplifiers with two each.
All twenty-two moved parts are unfixed internal B-side packages. All panel
centres, headers, supports, the other packages and the existing slew groups
remain unchanged. The source guard checks complete group membership, retained
geometry, courtyard clearance and all sixteen same-face supply-pad distances.
The source geometry puts the logic pairs at 2.535 mm and the analog pairs at
2.2975 mm. This 3 mm project screen is not a manufacturer qualification.

A disposable native placement comparison found zero rule errors and zero
schematic-parity findings for this candidate. It initially retained 42 silkscreen
warnings. Source-driven label regeneration then placed all 418 references
and the full native layout replay passed with zero violations. Obsolete
signal routes and dangling rail branches were removed. Sixteen local bypass
connections and ten signal links were added. The current partial copper has
854 segments, 246 vias and 406 open edges, zero DRC/parity findings, and all
344 ground contacts connected after independent refill. Combined final
replay, 26 targeted tests, documentation build and publication checks passed
in 83 seconds, with the existing workbench link exception retained. All 482 PCB tests and 281 source/check tests pass. CI is pending. The previous 366-open-edge copper checkpoint remains in git
history and is not evidence for the new placement. Current-source connectivity,
resistance/current limits, protection and physical qualification remain open.
No fabrication or order files are produced.
