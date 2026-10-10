# JR fixed-signal-landing rotation screen

This is a changed method after bounded single- and paired-translation failures.
Screen only the original nine movable, non-bypass resistors at90/180/270degrees
around their existing signal-pad centre:27cases on the identical JR134 native
dump f885375b and canonical board35b52972. The signal landing stays fixed;
all existing copper remains. An existing ground landing with copper contact
requires a full0.3mm additive bridge, checked against the unchanged copper and
rotated pads. Source outline/component/connector courtyard checks and0.25mm
copper clearance remain. No fixed part, electrical net, face or panel changes.

This only generates virtual proposals. Existing source translation support does
not implement rotation; a positive result would require explicit
source rotation support, native geometry/source synchronization, settled/fresh
DRC/parity/topology/warning/retention gates and all existing physical constraints.
No source or canonical board is changed. Do not submit a virtual pose as a PCB.

Result:27cases,zero static candidates. Four source-legal poses collide with copper; the complete blocker inventory shows pads/vias or more than three tracks in every case. No small track-only restoration scope exists within this bound. Native routing/source rotation support was not run or implemented because no proposal qualified. Guarded screen PASS2s and blocker inventory PASS1s. The first screen attempt caught existing1nm source conversion; its corrected integer check matches all nine saved centres exactly, without widening geometric tolerances. Preserve these negatives; do not repeat the same bound unchanged.
