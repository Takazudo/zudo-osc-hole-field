# MC04-S7 Part A0: function blocks on the current scene, and the two cases for the input buffers

Regenerate (from the repository root, with numpy, shapely and scipy available):

```sh
S=scripts/stack/studies; D=$S/mc04_s7_a0
python3 -B $S/mc04_c4_blocks/blocks.py --current \
  --move K:K:U1415,U4324,U4417,U4433,U4524,U4526,U4527,U4623,U4635,U5110,U5209,U5210,U8409,U4341 \
  --move JL:K:U1417,U2218:_PROTECTED,ISO_MID --move JL:K:U2219 --move JR:K:U4347,U4348,U8318 \
  --local JL:U1318,U2217 --local JR:U8314 --output $D/blocks-function.json            # about 6 minutes
# variant: U4347 on the keep-front boundary too
python3 -B $S/mc04_c4_blocks/blocks.py --current \
  --move K:K:U1415,U4324,U4417,U4433,U4524,U4526,U4527,U4623,U4635,U5110,U5209,U5210,U8409,U4341 \
  --move JL:K:U1417,U2218:_PROTECTED,ISO_MID --move JL:K:U2219 --move JR:K:U4347:_PROTECTED,ISO_MID \
  --move JR:K:U4348,U8318 --local JL:U1318,U2217 --local JR:U8314 --output $D/blocks-u4347-keep-front.json
for v in function u4347-keep-front; do
  python3 -B $S/mc04_c5_crossing_nets/nets.py --source $D/blocks-$v.json --output $D/nets-$v.json
  python3 -B $S/mc04_s1_budgets/budgets.py --source $v=$D/nets-$v.json --output $D/budgets-$v.json
  python3 -B $S/mc04_s1b_indicator_loops/loops.py --source $v=$D/nets-$v.json --out $D/loops-$v.json
done
python3 -B $D/held_l02.py --output $D/case-b-held-l02.json                            # about 3 minutes
```

**Scene.** `blocks.py --current` reads the committed link gate (`capacity.current_scene`): the gate's own
displacement record applied to the current boards (421 accepted moves). The unresolved list is every record row
with no new position (23 ICs); no IC set is written in the code. The run refuses to start if any gate input has
changed since the gate was generated, and each result records the sha256 of every file it read
(`inputs_sha256`). The block assignment comes from the command line and must name each unresolved IC exactly
once. The pinned MC04-R1 studies (no `--current`) are unchanged.

**Blocks.** Same packing as Task C step 4 (raster 0.25 mm, 0.35 mm between placed parts, exact predicate except
the displacement cap), with K's blocks placed first. `--local` ICs stay on their own board and face and go to the
nearest pose that passes the exact predicate, at each 90-degree turn, after the moved blocks have left that board.

**Case (b).** `held_l02.py` reruns the unchanged gate with only JL-K-JL-L02 held at its retained slot
(121.5, 80) +x. The DA-03 c6 pass is skipped: its pin refuses a changed source record, and it reorders P-K
positions only, so it does not change any link placement or displaced footprint.

| File | sha256 |
| --- | --- |
| blocks-function.json | e7c3657820d069dbfdd4d51fa02f4818810de8ec8a83c70884b4c20d33ee9935 |
| nets-function.json | c88c3aaf992e017c03e8dd99e1f5306a904eabe3b405eb3a7bd0c2ba20e37abe |
| budgets-function.json | 626e86561dbfd7d41a49a392b7e3923b9332b2fe55a5a2a508ca299f2289d714 |
| loops-function.json | 5276c7055c37d6d65c84b84e6a56f5cd0b94ba03c99cdfcb7c80ac5539bfd665 |
| blocks-u4347-keep-front.json | 8b830daa1ac433db682517b2552a071dc47d42cc3b39c97a0956f7b0397d15eb |
| nets-u4347-keep-front.json | c1b22ba2b5ba5798d57eb6866df68dba559b12a1e0f3d8a6ae822e788fae4f7a |
| budgets-u4347-keep-front.json | fbe4b8ae59af613eaaf0e9dbb356f98f3238e525641f3e042c6fd5ac77eb6d0c |
| loops-u4347-keep-front.json | f5e7c17a9843a9151edcebaafa293d3ef5fa128ed3e56fc99996e4f524aac309 |
| case-b-held-l02.json | ad1405538115240fbcf4e878812ed5f0cfdd1798d8e88573a245bf9087aa4bc3 |

The findings are in
`circuit/orchestration/campaigns/osc-stack-20261114/mc04-s7-a0-report-20261122.md`. Room, count and paper
screens only: no routing, no allocation, no canonical write.
