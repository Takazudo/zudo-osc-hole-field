# MC04-S7 Revision 2: the block set on the held JL-L02 scene, and the partition probe

```sh
S=scripts/stack/studies; D=$S/mc04_s7_r2
python3 -B $S/mc04_c4_blocks/blocks.py --current \
  --move K:K:U1415,U4324,U4417,U4433,U4524,U4526,U4527,U4623,U4635,U5110,U5209,U5210,U8409,U4341 \
  --move JL:K:U1417,U2218:_PROTECTED,ISO_MID --move JL:K:U2119 \
  --move JR:K:U4347:_PROTECTED,ISO_MID --move JR:K:U4348,U8318 \
  --local JL:U1318,D2243 --local JR:U8314 --output $D/blocks.json          # about 6 minutes
python3 -B $S/mc04_c5_crossing_nets/nets.py --source $D/blocks.json --output $D/nets.json
python3 -B $S/mc04_s1_budgets/budgets.py --source revision_2=$D/nets.json --output $D/budgets.json
python3 -B $S/mc04_s1b_indicator_loops/loops.py --source revision_2=$D/nets.json --out $D/loops.json
python3 -B $D/partition_probe.py --source $D/blocks.json --output $D/partition-probe.json
```

The scene is the committed link gate with JL-K-JL-L02 held at its retained slot (link-gate-options.json
`slot_holds`). `partition_probe.py` evaluates the io-partition checker with the moved block members assigned to the
core region, without changing any source. The findings are in
`circuit/orchestration/campaigns/osc-stack-20261114/mc04-s7-r2-report-20261122.md`.

| File | sha256 |
| --- | --- |
| blocks.json | 353b66b8f7645a7f267a77b68b78f5a6f0ba5ab241225e3bed4c229bf4c05d77 |
| nets.json | ef046859d091c2650f4dbcafd15f5d60e88483f1b5f1cae2f2c37f7f8db32999 |
| budgets.json | 8def579af0055dc22b1d980338511b83bf685d621336ff1b35417c436aa191fa |
| loops.json | fda805471ba56a7d4ef0d732c1f4c1b0f9d69a2971afe3e389866c00e83a9044 |
| partition-probe.json | 054a96574fa23370d9a4f1ddb3dd668ed3bafdc0d44ffc26e884a601060dd4ce |
