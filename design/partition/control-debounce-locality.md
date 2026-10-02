# Envelope debounce placement proposal

The source moves all thirty complete envelope debounce triplets (ninety
non-panel passives) beside their existing SN74HC14DR input pins. Each triplet
contains the contact pull-up, series resistor and input-to-ground capacitor.
All six Schmitt ICs, their bypass capacitors, panel hardware, headers, net
assignments and component identities stay unchanged.

The prior first-fit packing placed the thirty capacitors 30.127–144.626 mm
from their corresponding input pads, with a median of 93.580 mm. The proposed
source placement has a maximum of 7.665 mm and median of 4.039 mm. These are
straight-line pad distances, not routed lengths or a functional result.

The 8 mm capacitor-to-input and 4 mm resistor-to-neighbor limits are project
layout targets. They are not manufacturer limits. Input identities use the
retained `fact-schmitt-pinout` / `src-schmitt-datasheet` evidence for Texas
Instruments SN74HC14DR, SCLS085 revision L. The source helper derives each
complete triplet from actual IO pin/net records and refuses changed input
identity, incomplete groups, fixed hardware moves, courtyard conflicts or
out-of-bounds positions.

The source courtyard study preserves the existing board and support geometry.
Fresh native construction and all 418 reference placements pass with zero
DRC/parity findings. Native comparison covers all 1,740 pads: exactly the
180 passive pads move, while all other pads and every pad identity, net,
shape and layer remain unchanged. The bare layout still has 872 open edges.
Compatible-copper rebuilding starts at 199 open edges; separately checked
routing batches reduce this to 43, retaining all 344 grounds, 77 source
AGND copper objects and sixteen local bypass pairs after independent refill.
The previous 72-open-edge checkpoint remains the recovery source in git.
Old routes to moved pads are not accepted for this proposal. Current/resistance, protection, component qualification and
installed fit remain open; no fabrication or order files are generated.
