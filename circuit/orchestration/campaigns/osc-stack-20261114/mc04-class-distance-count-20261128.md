# MC-04 class-distance count: no S12 verdict rests on the clause; S15's U8409 screen left 206 moves untested

2026-11-28. Issue #367 (MC-04 paper gate). Design authority under DS-03 (Fable design agent at high effort, model
`claude-fable-5-2`). Written at head `d313db18` of `local/cloud-engineering-20261127`. Read-only count, asked for
by the coordinator after Ruling P8 of the S16 brief (DS-208).

Count only. No search domain was widened, no scene was built and no replay was run. Nothing is adopted. Every
board and schematic stays an unvalidated draft, check 5 stays NEEDS_DESIGN and #318 stays HOLD. No file of the
S16 run, its cache or any study was written.

## What was asked

Ruling P8 found that 13 recorded links have a member site farther from the connector centres than its class
distance. S12 and S15 applied that distance to every moved slot. The question: for those links, how many moved
slots did S12 and S15 reject by the class-distance clause **alone**, and does any negative verdict for U5110,
U5209, U5210 or U8409 rest on it?

Two limits are counted:

- **class limit:** the rule as S12 and S15 applied it (PRECISION 40 mm, ANALOGUE 45 mm, LOGIC and WIPER 55 mm);
- **no farther than the record:** per site, the larger of the class limit and that site's distance at the link's
  record slot. For a link whose record meets the class limit, this is the class limit.

## Per IC: only S15's U8409 verdict depends on the clause

| IC | Link it needs | S12 verdict rests on the clause alone | S15 verdict rests on the clause alone |
| --- | --- | --- | --- |
| U8409 | P-K-P-L03.01 | **No.** 0 of 630 slots at either limit | **Not shown, and not excluded.** The clause alone removed 482 distinct single moves, 206 of them no farther than the record. None was replayed |
| U5110 | P-K-P-L12.02.01.02 | **No.** 0 of 65 slots | **No, as far as the record gap goes.** The link's record meets the limit. The clause as ruled removed 21 distinct single moves, never replayed |
| U5209 | P-K-P-L13.01.01.02 | **No.** 0 of 766 slots | **No.** 589 distinct slots fail only this clause, and none is legal with the other links at their record |
| U5210 | P-K-P-L13.01.01.01 | **No.** 0 of 623 slots. The S12 verdict is `BOUNDED` for another reason | **No.** 504 distinct slots fail only this clause, and none is legal with the other links at their record |

"Rests on the clause alone" means: a slot exists that the study rejected by this clause and that passes every
other rule the study applied before a replay. For S12 those rules are 2 to 6 (T1 and T2 included). For S15 they
are 2 to 4, after which S15 replayed each legal single move.

## Only two of the 13 links were ever searched

S12 searched eight links and S15 six of them. Of the 13 links, only P-K-P-L03.01 and P-K-P-L08 are among them.
The other eleven had no moved slot in either study, so nothing was rejected for them.

| Link | Site over the limit at the record | Excess (mm) | Searched by |
| --- | --- | --- | --- |
| P-K-P-L03.01 | P-K-E3 (52.075 against 45) | 7.075 | S12, S15 |
| P-K-P-L08 | P-K-SUB-O2 (59.713 against 55) | 4.713 | S12 |
| JR-K-JR-L01 | JR-K-4 | 12.064 | none |
| JL-P-K-JL-L01 | JL-K-X4 | 9.293 | none |
| P-K-P-L04.01.01.01 | K-P-3 | 8.450 | none |
| P-K-P-L04.01.01.02 | K-P-5 | 8.450 | none |
| P-K-P-L04.02.01.01 | K-P-10 | 8.450 | none |
| P-K-P-L01.02.01 | P-K-E4 | 8.419 | none |
| JR-K-JR-L06 | JR-K-17 | 7.734 | none |
| JL-K-JL-L02 | JL-K-18 | 5.950 | none |
| JR-K-JR-L03 | JR-K-14 | 5.950 | none |
| JL-K-JL-L04 | JL-K-21 | 4.495 | none |
| P-K-P-L06.02 | K-P-99 | 0.483 | none |

Each link has one site over the limit. None of the 13 was placed by way 2, the only place where the generator
applies this distance.

## Counts for the two searched links of the 13

Raw counts are census candidates on the 2.0, 0.5 and 0.25 mm grids together, as S12 counted them. Distinct counts
are distinct (slot, direction) pairs.

| Count | L03.01, class limit | L03.01, no farther than record | L08, class limit | L08, no farther than record |
| --- | --- | --- | --- | --- |
| Legal under rule 1 | 813 | 813 | 2189 | 2189 |
| Rejected by the class clause | 630 | 344 | 1402 | 1263 |
| Of those, pass the rest of rule 2 and rules 3 and 4 (raw) | 630 | 286 | 1402 | 139 |
| The same, distinct | 482 | 206 | 1098 | 107 |
| The same, distinct and legal with every other link at its record | 482 | 206 | 8 | 8 |
| Of those, pass T1 and T2 as well (S12's rules 2 to 6) | **0** | **0** | **0** | **0** |

In the two "no farther than record" columns, the second row is the slots still rejected under that limit, and
the rows below it count the slots the looser limit would let through.

What T1 finds on the distinct slots that fail only the class clause among rules 2 to 4:

| Link and limit | Newly displaces a protected part (class N) | Displaces only parts a searched link already displaces (class S) | Neither |
| --- | --- | --- | --- |
| L03.01, class limit | 461 | 21 | 0 |
| L03.01, no farther than record | 188 | 18 | 0 |
| L08, class limit | 1005 | 93 | 0 |
| L08, no farther than record | 51 | 56 | 0 |

For L03.01 the class S parts are the six it displaces today: R8420, R8444, U8411, C7205, U8409 and C8405.

## Counts for the other six searched links: the clause never decides alone in S12

These links meet the class limit at their record, so the second limit changes nothing for them.

| Link | IC it is needed for | Rejected by the class clause | Pass rules 2 to 4 otherwise (raw / distinct) | Distinct and legal at record | Pass rules 2 to 6 otherwise |
| --- | --- | --- | --- | --- | --- |
| P-K-P-L12.02.01.02 | U5110 | 65 | 65 / 44 | 21 | 0 |
| P-K-P-L13.01.01.02 | U5209 | 828 | 766 / 589 | 0 | 0 |
| P-K-P-L13.01.01.01 | U5210 | 623 | 623 / 504 | 0 | 0 |
| P-K-P-L13.01.02.01 | none | 1062 | 0 / 0 | 0 | 0 |
| P-K-P-L15.02.01.01 | none | 838 | 838 / 652 | 0 | 26 raw, 20 distinct |
| P-K-P-L07 | U1415 | 1201 | 1201 / 952 | 11 | 0 |
| P-K-P-L07 as a 26-way | U1415 | 3679 | 3679 / 2876 | 1759 | 0 |

P-K-P-L15.02.01.01 is the one link with slots that fail only this clause under S12's full rules: 20 distinct
slots. No IC needs that link, it already had 73 census survivors, and none of the 20 is legal with the other
links at their record. They would have widened its pool in S12's joint search. They cannot change a verdict that
rests on a census of zero for another link.

## S12: all four verdicts stand without the clause

- **U8409, U5110, U5209 (`NO CANDIDATE ON THIS DOMAIN (EXHAUSTIVE)`).** Each rests on a census of zero for the
  needed link. With the class clause removed entirely, the census of each needed link is still zero: every slot
  the clause rejected fails T1, or another clause, as well.
- **U5210 (`NO SCENE FOUND (BOUNDED BY THE POOL REDUCTION)`).** Its needed link gains no survivor either. The
  verdict was bounded before and stays bounded.
- U1415 is outside the question. For the record, L07 and L08 gain no survivor at either limit.

## S15: the U8409 screen is complete only with the clause in force

S15 dropped T1 and T2 in favour of its no-growth tests on the replay. So every slot that passes rules 2 to 4 and
is legal with the other links at their record was a single move to replay.

- **U8409.** S15 replayed 131 distinct single moves of L03.01, and all 131 failed A3. The class clause had removed
  482 more before that, by itself. Their excess over the limit runs from 5.646 to 18.874 mm. 206 of them are no
  farther from P-K-E3 than the record slot is, whose own excess is 7.075 mm. None was replayed, so what they
  would give is not known. 188 of the 206 would newly displace a protected part; 18 displace only the six
  parts L03.01 displaces today.
- **U5110.** 21 distinct single moves of L12.02.01.02 were removed by the clause alone. All 21 would newly
  displace a protected part. The link's record meets the limit, so this is the rule as DS-158 kept it, not a gap
  between the rule and the record.
- **U5209 and U5210.** No slot that fails only this clause is legal with the other links at their record, so the
  single-move screens lose nothing to it.

S15's verdict text, `NO SINGLE-MOVE CANDIDATE (COMPLETE SCREEN, OTHER LINKS AT RECORD)`, is therefore accurate
under its stated rules for all four ICs. For U8409 it is complete only because of a limit the link's own record
does not meet.

## The count reproduces S12's census on all nine entries

- **Method.** The S12 census loop was run again for the eight searched links and for L07 as a 26-way: same
  `World` at snapshot `6e5716e7`, same grids, same 35 mm radius, same placed index, same rule functions. The class
  clause was evaluated separately from the rest of rule 2, and the two were checked against `World.rule2` on
  every candidate.
- **Control.** For each of the nine entries the recount gives the same legal count, the same count of class
  rejections and the same counts after rules 2 to 6 as `census.json` (`92f6fded…dbda095e`).
- **Cached inputs read.** S12 `result.json` (`32532262…99da02ed`), S15 `result.json` (`e7fb8477…cf1610f3`) and the
  S15 screen cache `screen.json` (`76d2e8e5…3304152f`).
- **Cost.** One process at low priority, 4.5 minutes, about 300 MiB. The script and its output stayed in the
  session scratchpad and are not in the repository.

## What this count does not establish

| Item | Status |
| --- | --- |
| Whether any of the 206 (or 482) single moves of L03.01 passes S15's replay tests | `NOT RUN`: the task allowed no replay beyond the cache |
| Whether any of the 21 single moves of L12.02.01.02 passes | `NOT RUN`, same reason |
| "Legal with every other link at its record" as S15 computed it | not controlled: computed here with `links_gate.candidate` and every other live link placed; not compared with S15's own stage 2 code on its cached records |
| Whether a slot no farther than the record is electrically acceptable | not established: nothing on record answers it |
| Joint moves in S12 with the wider pool of L15.02.01.01 | `NOT RUN`: no joint search was repeated |
| Anything about the eleven links that were never searched | no data: neither study moved them |

## What follows for the open work

- **S12 needs no correction.** Its four verdicts do not depend on the clause.
- **S15's U8409 result carries one more condition.** It should be read as "no single move within the class
  distance". The S15 disposition accepted it as geometric evidence under S15's rules, and that still holds.
- **S16 is not affected.** It re-plans the link by site and labels the clause as exclusion e. Its reference census
  of the full 26-way set applies the same clause.
- **A follow-up exists but is not started.** Replaying the 206 single moves under S15's rules would take about 25
  minutes of replay time. It only means something if "no farther than the record" is accepted as a limit, and
  that is an electrical question for the owner, not a geometric one. No such run is proposed here.
