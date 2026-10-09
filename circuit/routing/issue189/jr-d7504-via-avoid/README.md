Native NOT RUN. The34-object alternative moves the first via from(410.375,177.85) to(409.5,176.2); the second stays(409.95,180.525). This change is motivated by saved native ground-fill loss, not proof of acceptance. No geometry or electrical requirement is relaxed.

Wait for JR37920931258 to finish, inspect its receipt/artifact/native groups and integrate only its reviewed delta. Then run:

.circuit-cache/route-venv/bin/python circuit/routing/issue189/jr-d7504-via-avoid/rebase_proposal.py --accepted-sha256 ACTUAL_PUBLISHED_SHA256

The helper pins original main199input72a24ee996ae454c099ed165de1bd857721c42bef37861907a98ba5a4bf39d0c, proves all existing full copper blocks survive, permits only the known50-object delta (or no change), rejects UUID conflicts and checks new-to-new clearances. Inspect generated plan/rebase before adding a workflow replay choice and submitting exactly one JR writer. Full native gates are mandatory. The wide-exclusion and two-site-exclusion negative screens must not be repeated unchanged.
