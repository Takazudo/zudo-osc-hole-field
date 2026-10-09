# Bounded additive raster evidence

`probe.py` compares one U7506.11 supply escape on the exact saved JR153 native
input, at 0.025 mm resolution with the same 300,000 expansions/window budget.
`result.json` records identical two-segment full-width proposals: full raster
25.169316 seconds; 12 mm bounded frame 2.375470 seconds. This is a single-case
allocation/search comparison, not a general performance claim or a new native pass.

The initial bounded attempt failed in `island_mask` because an original via
outside the search frame was indexed directly. The correction bounds-checks via
indices without deleting native island members; the regression covers negative
index wrapping and large out-of-range indices. Six bounded-raster tests and
81 other affected tests pass (87 total).

All original geometry and native island members remain in the input. The bounded
frame is a conservative computational fence and cannot change the physical board
outline. Rip-up is explicitly rejected. Every proposed transaction still needs
whole-board native DRC/parity, original group and warning preservation, and an
independent fresh check before promotion.

`../core1441-bounded-screen/comparison.json` compares the same 24 nets, bounds,
source and budgets at 0.025 and 0.05 mm: five paths in187.959573 seconds versus
three in155.845891 seconds. Neither resolution dominates: two coarser paths were
not found by the finer run. These are raster results; accepted edges are unknown
until native receipts finish. The first fine U1513.9 transaction is submitted in
run37907147442; all other screen proposals remain unpromoted.
