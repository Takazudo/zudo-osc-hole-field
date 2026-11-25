# MC04-S10 Revision 2 feasibility decision

The owner returned Revision 1 at `32580f77c9d0aa9c6067cbad965a6f701050ca5d`. The selected WSL parent model for thread `01a210e0-6940-7e71-adae-314d5ddf1e9b` is recorded by the local CLI as `gpt-6.2-astra`. This prospective decision admits one arithmetic feasibility check before considering a changed generator contract. It preserves the Revision 1 protected-node rule and the DS-147 maximum. No search or changed hold is admitted by this decision.

## Inputs and bounds

Use the K paper poses at `8243acdf4ef76b18741ce3bcca4794e2abf3fee2` in `design/partition/adopted-placement-pins.json` (SHA-256 `9e827879ebcccea57d247e433a496db71ee1213c87af27b90c81fada2d1218b2`), the gate replacement rows and io-partition nets at that commit, and S9-A2 result SHA-256 `9d524988de302e6d0052ab26b503bf24c71ce5f2c693f30b111e66955cc348d2`. Evaluate the single fixed endpoint pair once, on one CPU, with 256 MiB address space and 30 seconds wall time. Keep every cable, board, panel centre, connector and existing hold fixed. Stop before candidate enumeration if any required distance is impossible independently of link position.

## Result and decision

R5257 had no pre-S10 gate displacement. Its pins carry /W1/F2_OUT and /W1/F2_SUM. A newly displaced R5257 would itself trigger Revision 1. U5210 must return to its paper position without displacement. The two required B-face endpoints are (174.66, 199.89) and (180.97, 204.70) mm. Their separation is approximately 7.934242245 mm.

With coordinates expressed in hundredths of a millimetre, compare 631² + 481² with 793². The squared distance exceeds the squared cap. A different connector slot, direction or cable leaves these endpoints unchanged. Testing a different S9-A2 pair under these conditions cannot cure the failure. The feasible search domain for the unchanged electrical and movement constraints is empty. Stop before a geometry run. The original candidate also moves six protected-node passives and has a separate inherited U5113 acceptance discrepancy.

A prospective engineering option would require substantiating a no-growth rule for R5257 at its exact paper distance with the feedback layout and electrical evidence. Another would permit moving one endpoint and re-evaluate its feedback geometry. Both change an express condition; neither is adopted here. Even an approved change to R5257 would leave the protected passive and locality problems to solve. Preserve the unstarted DS-149 study and its three individual fallbacks.
