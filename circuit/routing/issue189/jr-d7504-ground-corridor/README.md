# Preserve the D7504 front-ground corridor

One diagnosed search-only alternative blocks new F.Cu tracks/vias in x408–414mm,y171–184mm around the repeatedly split R7505.2/R7530.2 ground returns. D7504.1 is on B.Cu, so the search retains B.Cu/In2.Cu paths toward existing signal copper outside the corridor. It retains the prior via exclusion and all original native memberships/rules. No board keepout is added.

The bounded0.025mm,300000-expansion search found no route; guarded run passed in4s. This is a negative local result, not a native validation or accepted board. Do not rerun this unchanged configuration. Prior failures and this corridor failure support evaluating coordinated local copper repair rather than another unchanged additive signal retry.
