The native cut pilot37911267983 did not invoke A*: its12mm allocation held
U2105.2 but excluded all copper of the other component aroundR2119.1/R2120.1.
The old generic `unknown` diagnostic concealed that missing goal.

The saved native cut dump is replayed with identical electrical rules,0.025mm
raster and300000expansions/window in frame-comparison.py/json. The original
frame now reports `no_goal_in_search_bounds` in2.107876s. The complete-component
24.7x49.8mm frame invokes A* and reaches its300000 expansion limit in4.495113s.
Both restore the victim in raster and fail the target. GuardPASS; no new native
validation or canonical adoption is claimed. Empty source/goal masks now produce
specific diagnostics without dropping native obligations or crashing on empty
coordinate reductions. The synthetic regression covers both directions.
