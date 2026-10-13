# Read-only baseline result snapshot

Source `852ffac7f85aff4bb436eb25f7ce993cee48146b`, request `ef0213b3b38f4de23804ad192043b082d8e1b2be3086c5e20e4343afea4052d6`.

TERMINAL; terminal exit=0. Completed ledger units 148 / authorized maximum 148. Verified coupled combinations 12/12; finite states 30/30.

Numerical full baseline complete: **True**. **Electrical acceptance: false.**

Integrity errors: 0; unreadable/in-progress ledgers: 0.

Phase/count diagnostics: [{"phase": "service", "observed": 1, "expected": 1, "status": "MATCH"}, {"phase": "reduce", "observed": 24, "expected": 24, "status": "MATCH"}, {"phase": "dpoint", "observed": 111, "expected": 111, "status": "MATCH"}, {"phase": "couple", "observed": 12, "expected": 12, "status": "MATCH"}, {"phase": "all", "observed": 148, "maximum_authorized_units": 148, "status": "WITHIN_CEILING"}].

Actual service subset: {"partial": 59, "supported": 151, "unmapped": 194, "unserved": 21}.
Included signed board/net currents (A): {"KA": {"+12V": 0.09416, "+5V": 6e-05, "-12V": -0.09416, "AGND": -6e-05}, "KB": {"+12V": 0.07744, "+5V": 0.00118, "-12V": -0.07744, "AGND": -0.00118}}.

| Net | Case | Depth | Verified states | Missing states |
| --- | --- | --- | --- | --- |
| +12V | nominal-average | uniform-dielectric | all-present | none |
| +12V | sensitivity-thin | uniform-dielectric | all-present | none |
| +12V | legacy-conditional-requirement | uniform-dielectric | all-present | none |
| -12V | nominal-average | uniform-dielectric | all-present | none |
| -12V | sensitivity-thin | uniform-dielectric | all-present | none |
| -12V | legacy-conditional-requirement | uniform-dielectric | all-present | none |
| +5V | nominal-average | uniform-dielectric | all-present | none |
| +5V | sensitivity-thin | uniform-dielectric | all-present | none |
| +5V | legacy-conditional-requirement | uniform-dielectric | all-present | none |
| AGND | nominal-average | uniform-dielectric | all-present, remove-W4, remove-W4-W5, remove-W4-W6, remove-W5, remove-W5-W6, remove-W6 | none |
| AGND | sensitivity-thin | uniform-dielectric | all-present, remove-W4, remove-W4-W5, remove-W4-W6, remove-W5, remove-W5-W6, remove-W6 | none |
| AGND | legacy-conditional-requirement | uniform-dielectric | all-present, remove-W4, remove-W4-W5, remove-W4-W6, remove-W5, remove-W5-W6, remove-W6 | none |

Verified electrical results (copper resistance includes the modelled path; no full source-path acceptance):

| Net/case/state | Board | Evaluated / over budget | Max copper (mΩ) | Energized max copper (mΩ) | Worst source-relative potential (mV) |
| --- | --- | --- | --- | --- | --- |
| +12V/legacy-conditional-requirement/all-present | KA | 275 / 274 | 5.302948473130239 | 5.302948473130239 | -0.10246978427400129 |
| +12V/legacy-conditional-requirement/all-present | KB | 250 / 250 | 6.769985682480797 | 6.03536482317546 | -0.28078213161243754 |
| +12V/nominal-average/all-present | KA | 275 / 275 | 5.174020386507961 | 5.003293921822727 | -0.1174191720025504 |
| +12V/nominal-average/all-present | KB | 250 / 250 | 6.48095296289586 | 5.9921452927738486 | -0.2884677849337436 |
| +12V/sensitivity-thin/all-present | KA | 275 / 275 | 8.145953652090807 | 7.380137074493637 | -0.21779900005766334 |
| +12V/sensitivity-thin/all-present | KB | 250 / 250 | 9.89708281222026 | 9.261725770223796 | -0.4168724101266635 |
| +5V/legacy-conditional-requirement/all-present | KA | 24 / 24 | 23.05397731413559 | 23.05397731413559 | -0.0008893353680561395 |
| +5V/legacy-conditional-requirement/all-present | KB | 398 / 398 | 23.12979004915616 | 21.920533758999603 | -0.01007779407220919 |
| +5V/nominal-average/all-present | KA | 24 / 24 | 21.105600306546222 | 21.105600306546222 | -0.0009231465107792525 |
| +5V/nominal-average/all-present | KB | 398 / 398 | 21.204675563292895 | 20.534034276571568 | -0.009360121379243318 |
| +5V/sensitivity-thin/all-present | KA | 24 / 24 | 28.485241696866964 | 28.485241696866964 | -0.0015425840649669633 |
| +5V/sensitivity-thin/all-present | KB | 398 / 398 | 29.539192505917548 | 28.872050771399127 | -0.01216598289434462 |
| -12V/legacy-conditional-requirement/all-present | KA | 201 / 201 | 18.150621710368036 | 18.150621710368036 | 0.32541698541167796 |
| -12V/legacy-conditional-requirement/all-present | KB | 146 / 146 | 19.19272960431854 | 19.19272960431854 | 0.40207351000108105 |
| -12V/nominal-average/all-present | KA | 201 / 201 | 16.60692318739169 | 16.60692318739169 | 0.3116786499518488 |
| -12V/nominal-average/all-present | KB | 146 / 146 | 17.67366643151428 | 17.67366643151428 | 0.3925378383229593 |
| -12V/sensitivity-thin/all-present | KA | 201 / 201 | 22.39109621092611 | 22.39109621092611 | 0.45460670604336567 |
| -12V/sensitivity-thin/all-present | KB | 146 / 146 | 24.110590211550196 | 24.110590211550196 | 0.5388175383762542 |
| AGND/legacy-conditional-requirement/all-present | KA | 849 / 849 | 13.371337529647336 | 5.582133840838536 | 0.0005409375592861783 |
| AGND/legacy-conditional-requirement/all-present | KB | 995 / 995 | 17.18682173600259 | 8.431117714981827 | 0.0017480611625232208 |
| AGND/legacy-conditional-requirement/remove-W4 | KA | 849 / 849 | 13.371366251575374 | 5.58214100217328 | 0.0005263165948055729 |
| AGND/legacy-conditional-requirement/remove-W4 | KB | 995 / 995 | 17.221357245444075 | 8.461993012903356 | 0.00202029751471734 |
| AGND/legacy-conditional-requirement/remove-W4-W5 | KA | 849 / 849 | 13.37139973857765 | 5.582147759568734 | 0.0005009986657819679 |
| AGND/legacy-conditional-requirement/remove-W4-W5 | KB | 995 / 995 | 17.36107906838843 | 8.596787558819491 | 0.0028835373264634472 |
| AGND/legacy-conditional-requirement/remove-W4-W6 | KA | 849 / 849 | 13.371399738577054 | 5.582147759568602 | 0.0005591505002985196 |
| AGND/legacy-conditional-requirement/remove-W4-W6 | KB | 995 / 995 | 17.403425296848418 | 8.649274192478947 | 0.002929969359120404 |
| AGND/legacy-conditional-requirement/remove-W5 | KA | 849 / 849 | 13.37134192095785 | 5.582134480707017 | 0.0005391105148495605 |
| AGND/legacy-conditional-requirement/remove-W5 | KB | 995 / 995 | 17.22247979556277 | 8.466446425401276 | 0.0020225556597941426 |
| AGND/legacy-conditional-requirement/remove-W5-W6 | KA | 849 / 849 | 13.371399738576816 | 5.582147759568537 | 0.000608885163686138 |
| AGND/legacy-conditional-requirement/remove-W5-W6 | KB | 995 / 995 | 17.534129460956105 | 8.788127407123604 | 0.003082137997749384 |
| AGND/legacy-conditional-requirement/remove-W6 | KA | 849 / 849 | 13.371394693464813 | 5.582146197435719 | 0.000576847781570129 |
| AGND/legacy-conditional-requirement/remove-W6 | KB | 995 / 995 | 17.30366928731564 | 8.553267446711972 | 0.0021158200973699203 |
| AGND/nominal-average/all-present | KA | 849 / 849 | 12.431765681562034 | 5.441039073514381 | 0.0005034689879362809 |
| AGND/nominal-average/all-present | KB | 995 / 995 | 15.658680566026518 | 8.004346615204074 | 0.0016593771794571259 |
| AGND/nominal-average/remove-W4 | KA | 849 / 849 | 12.431790096797114 | 5.441045331706076 | 0.0004900511754698788 |
| AGND/nominal-average/remove-W4 | KB | 995 / 995 | 15.692890090762646 | 8.03521514242354 | 0.0019314422718568962 |
| AGND/nominal-average/remove-W4-W5 | KA | 849 / 849 | 12.431817990951764 | 5.441051147510942 | 0.0004671972060532288 |
| AGND/nominal-average/remove-W4-W5 | KB | 995 / 995 | 15.828809611121812 | 8.166698350798903 | 0.002790041203202319 |
| AGND/nominal-average/remove-W4-W6 | KA | 849 / 849 | 12.431817990951046 | 5.441051147510769 | 0.0005195474469583089 |
| AGND/nominal-average/remove-W4-W6 | KB | 995 / 995 | 15.866965560442974 | 8.21396076485898 | 0.002831894550890688 |
| AGND/nominal-average/remove-W5 | KA | 849 / 849 | 12.431769316793627 | 5.441039624026166 | 0.0005018361880759301 |
| AGND/nominal-average/remove-W5 | KB | 995 / 995 | 15.694182823500377 | 8.039552695633086 | 0.001933678355575117 |
| AGND/nominal-average/remove-W5-W6 | KA | 849 / 849 | 12.43181799095076 | 5.4410511475106835 | 0.0005642867781734202 |
| AGND/nominal-average/remove-W5-W6 | KB | 995 / 995 | 15.984386381278235 | 8.33869958655018 | 0.0029686015488067123 |
| AGND/nominal-average/remove-W6 | KA | 849 / 849 | 12.43181377736456 | 5.441049809529364 | 0.0005356099236138432 |
| AGND/nominal-average/remove-W6 | KB | 995 / 995 | 15.767079445904404 | 8.117468182392278 | 0.00201745387494348 |
| AGND/sensitivity-thin/all-present | KA | 849 / 849 | 17.26005362587183 | 8.174545759613846 | 0.0006980862051082339 |
| AGND/sensitivity-thin/all-present | KB | 995 / 995 | 20.94312140837007 | 11.521232688806766 | 0.0021250513293098908 |
| AGND/sensitivity-thin/remove-W4 | KA | 849 / 849 | 17.260089780420074 | 8.174555425368233 | 0.0006810368330862449 |
| AGND/sensitivity-thin/remove-W4 | KB | 995 / 995 | 20.996999211015964 | 11.570858878488393 | 0.002420017200537944 |
| AGND/sensitivity-thin/remove-W4-W5 | KA | 849 / 849 | 17.260132305736906 | 8.174564702887798 | 0.0006512245465410865 |
| AGND/sensitivity-thin/remove-W4-W5 | KB | 995 / 995 | 21.200512291806266 | 11.768622747836826 | 0.0033587903208210255 |
| AGND/sensitivity-thin/remove-W4-W6 | KA | 849 / 849 | 17.260132305735258 | 8.17456470288735 | 0.0007195576359733211 |
| AGND/sensitivity-thin/remove-W4-W6 | KB | 995 / 995 | 21.25038045890259 | 11.830336765624207 | 0.0034135201478484784 |
| AGND/sensitivity-thin/remove-W5 | KA | 849 / 849 | 17.260059199009465 | 8.17454665078336 | 0.0006959318692674003 |
| AGND/sensitivity-thin/remove-W5 | KB | 995 / 995 | 20.998227515369916 | 11.575954289857108 | 0.00242251932405233 |
| AGND/sensitivity-thin/remove-W5-W6 | KA | 849 / 849 | 17.2601323057346 | 8.174564702887132 | 0.0007778845879078453 |
| AGND/sensitivity-thin/remove-W5-W6 | KB | 995 / 995 | 21.403187331857215 | 11.992662747599626 | 0.0035914308585344697 |
| AGND/sensitivity-thin/remove-W6 | KA | 849 / 849 | 17.26012586466531 | 8.174562584888442 | 0.0007403007007298786 |
| AGND/sensitivity-thin/remove-W6 | KB | 995 / 995 | 21.093326069182748 | 11.677649241104643 | 0.0025317974598096584 |

Failed numerical checks: [].

Resource/process detail and exact numerical maxima are in summary.json. Independent owned-process cleanup is not inferred.

- Whole-device declared quiescent/static subset only; partial/unserved/unmapped package loads excluded.
- Source-relative rail potentials are not rail-to-local-ground error or full source-to-load voltage.
- Physical source/protection/raw-load bridge and branch loads remain unimplemented/external.
- GH conductor currents/compliance are NOT EVALUATED; no nearest-ground return is inferred.
- Board-class dissipation does not locate a particular via/land bottleneck.
- Trunk resistance is not present in these JSON outputs; no pickle values are reconstructed.
- No geometry variant, native DRC completion, fabrication or installed-fit acceptance follows.
