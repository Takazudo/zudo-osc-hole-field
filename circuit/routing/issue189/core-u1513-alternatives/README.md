UNREBASED; NATIVE NOT RUN. On identical saved native1441 input, outer-layer restriction produces26B.Cu segments/no vias at weight1; weight2.5 yields34segments/no vias. The prior31-object/one-via native candidate was rejected for three ground splits. This changed geometry is not an accepted fix.

The selected26-object alternative has2.4844459391092233mm minimum geometric gap to the pending143-object power batch. Wait for sole core37925863664 to finish, inspect actual receipts/native groups and reconcile accepted copper. Then run:

.circuit-cache/route-venv/bin/python circuit/routing/issue189/core-u1513-alternatives/rebase_proposal.py --accepted-sha256 ACTUAL_PUBLISHED_SHA256

The helper preserves every original full copper block, permits only the known143-object power delta or no change, fails closed on unexpected subsets, checks collisions/gaps, and pins actual accepted input. Inspect generated plan/rebase before adding a workflow replay choice and submitting one core writer. Full native gates remain mandatory; no physical/electrical constraint changes.
