UNREBASED; NATIVE NOT RUN. This changed D7504 alternative uses outer layers only and one via at(411.4,176.35), with9objects,zero removals. The previous34-object/two-via native candidate preserved R7505 but split R7530; this is a new geometry, not an accepted repair.

Wait for JR37925027262 to finish, inspect its actual receipt/artifact and reconcile accepted copper. Then run:

.circuit-cache/route-venv/bin/python circuit/routing/issue189/jr-d7504-outer-avoid/rebase_proposal.py --accepted-sha256 ACTUAL_PUBLISHED_SHA256

The helper requires every prior full copper block unchanged, allows only the known233-object pending delta or no change, rejects UUID and clearance conflicts, and fails closed on any unexpected subset. Inspect generated plan/rebase before adding workflow choice d7504-outer-avoid and dispatching exactly one JR writer. Full native gates remain mandatory.
