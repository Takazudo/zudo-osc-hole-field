# Same-input finer core ground screen

One bounded24-group comparison uses the identical native core1441 dump, same current router code, full ground dimensions and300000-expansion cap. Coarse0.025mm yields C1343.2/C1548.2 (seven objects);0.0125mm additionally yields C1535.2/C2234.2 (twelve objects total). Timings and immutable hashes are in comparison.json. The old coarse output used another router revision, so coarse_control.py was rerun on the current code before drawing this comparison. Both guarded executions passed; none of these finer results is native accepted.

C1548 is already in active core143 run37925863664. Do not duplicate it, rebase alternatives or dispatch another core writer. Wait for the actual native result, reconcile every accepted object, then explicitly select only still-open groups and recheck compatibility on the accepted output. Finer raster proposals are not proof of completed ground connectivity or a speedup.

The next two 48-group batches completed: six positive groups/85 objects and ten positive groups/87 objects. All are raster-only. Core143 run37925863664 subsequently rejected; accepted core remains1441. Its143 additions are not present and do not need preserving in a new candidate. Rebase only against the accepted hash and select still-open groups.

Third48-group batch completed all48 in314.38s (guardPASS315s), yielding five groups/25objects. Across168groups the positive total is25groups/209objects. The combined selector excludes one12-object transaction due to0.025mm between proposed via centers, leaving24groups/197objects. Still no native acceptance.

The fourth48-group batch completed all48 in393.09s (guardPASS394s):6positive groups/73objects. The final36 completed in325.34s (guardPASS326s):8groups/112objects. All252non-main native AGND groups were covered, with no large-frame skips. Total39positive groups/394objects; pair-spacing selection excludes one12-object transaction, retaining38groups/382objects/38vias. No native acceptance or future rebase is claimed.
