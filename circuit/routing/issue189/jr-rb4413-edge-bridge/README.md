# RB4413 actual pad-edge landing repair

The first movement pilot37986929982 is native-rejected: AGND gains one join but the original X34EC684E00B004F73024 group splits, leaving track34f3b8b3-14db-5078-9909-c5d7b4d35488 dangling. It landed at the old pad edge(385.7,92.7), which a bridge between old/new pad centres did not preserve. Total native edges remain134. All51177old copper objects survive; DRC/parity0 and fresh agreement do not override that rejection.

This changed proposal adds a full0.2mm signal segment from(385.7,92.7)to(385.7,92.4), inside the translated pad. Minimum static foreign-copper clearance is0.605mm on the exact rejected native candidate. It retains the first proposal's six segments/one via, yielding seven segments/one via and zero cuts. Prepare.py records the native landing and immutable geometry. Native verification remains mandatory; static clearance is not acceptance.

Pilot/reconciliation preserve the same source/physical/native gates and never publish. Source regeneration is still NOT RUN. Run only after the first pilot is terminal/reconciled; this is a changed landing method, not an unchanged retry or relaxed verification.
