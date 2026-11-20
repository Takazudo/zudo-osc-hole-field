# All 55 new crossing nets classify ANALOGUE; the block boundary splits every protection and isolation pair

Task C step 5a, 2026-11-20. Paper classification of the nets that would newly cross the JR-K and JL-K
cables if the step 4 blocks (`../mc04_c4_blocks/result.json`, sha256 `be96eff6…cab3`, pinned) all move to K.

```sh
python3 -B scripts/stack/studies/mc04_c5_crossing_nets/nets.py --output scripts/stack/studies/mc04_c5_crossing_nets/result.json
```

`result.json` sha256 `29879937886fb3c15ed0ac379bd557a285b43eb8747b0c6ff34467be27576a5d`.

## None of the 55 is raw-sensitive or forbidden, and none is an allowed crossing kind today

| Source | Indicator LED drive | Isolation midpoint | Protected input node |
| --- | --- | --- | --- |
| JR (31 new) | 18 | 5 | 8 |
| JL (24 new) | 8 | 9 | 7 |

Every net classifies ANALOGUE under the retained `classify()` rules with no partition kind. No net is in
`local_raw_sensitive_nets` or `forbidden_crossings`. None has an allowed-crossing kind, so the partition
source needs a kind ruling before any allocation run.

## Every protected and isolation split comes from the one-hop block boundary

Each `*_PROTECTED` net would cross because the series resistor moves with the IC while the protection
device and input resistor stay (for example `/E3/SIG_PROTECTED`: R4308 moves; R4307 and U4302 stay).
Each `ISO_MID` net splits an RB pair. A block boundary that keeps those pairs on the front board would
remove these 29 crossings; it was not studied here.

## Scope

Paper classification only. No allocation, coupling, electrical review or canonical write.
