# MC02 selected cable source update

Date: 2026-11-17. Coordinator: Codex, x0x WSL. Manufacturer drawing review:
`retained_fh12_review`, including full-page visual inspection. This supersedes the
historical blanket statement that none of the five selected codes has an available
exact manufacturer tolerance drawing. It does not adopt a cable or prove a fit.

## Acquired bytes and exact applicability

The four PDFs name Shenzhen Lianxian Electronics (深圳市连线电子有限公司).
They were downloaded through existing distributor source links and ordinary
published PDF redirects, with headers retained. No denied endpoint, expired signed
URL, authentication or access protection was bypassed. Raw bytes and renders stay
in the ignored source/coordinator cache, outside published assets.

| Selected code | Source and drawing applicability | Bytes / SHA-256 |
| --- | --- | --- |
| C81339 | [Manufacturer drawing via distributor](https://datasheet.lcsc.com/datasheet/pdf/3e54240f3b48533cb541481b94442091.pdf?productCode=C81339). Actual customer code,8P,40mm,same-side confirmed. Drawing2018053109,A1,2018.05.31. |188301 / `2549f2f79ecbb7fdad0fc25c8e4480adb2bcfcd4bafe32b6925275c3a22fac9b`|
| C68390 | [Manufacturer drawing via distributor](https://datasheet.lcsc.com/datasheet/pdf/b7a7b49c23b427c5d4d53f566b8c6681.pdf?productCode=C68390). Actual customer code,14P,50mm,same-side confirmed. Drawing2018053109,A1,2018.05.31; a shared drawing number alone is not identity. |189290 / `93f731b7083d21c2bc5279adfd0037184c91c1ea07296ca71f767901ca9bfb4e`|
| C29534 | [Manufacturer drawing via distributor](https://datasheet.lcsc.com/datasheet/pdf/7d62c4f163a28ea01bb945ee64a37fd4.pdf?productCode=C29534). Actual customer code,8P,50mm,same-side confirmed. A/0,2019.09.12; drawing-number blank; A771 is the customer field, not a transferable identity. |308621 / `23fff3c7a1fc0cb63ccea9ee542d442c1c2da9edbb6d591f80211f10173b699e`|
| C26618 | [Associated generic drawing](https://datasheet.lcsc.com/datasheet/pdf/ccb31f6dba53cb95289e29e400c08f64.pdf?productCode=C26618). PH0.5 same-side family,A1,2023.04.12; customer code/count/length not selected. Does not establish exact40P50mm applicability. |336193 / `1866c1e6ca5591efe2aa1d1ccfcf58a3384c620ee7db50b9019a2974d30d62a8`|
| C32128 | [Associated generic drawing](https://datasheet.lcsc.com/datasheet/pdf/ccb31f6dba53cb95289e29e400c08f64.pdf?productCode=C32128). Public reader failed, but ordinary public HTML linked this PDF; normal download succeeded without access denial. Bytes are identical to C26618-associated family sheet, with no exact26P60mm binding. |336193 / `1866c1e6ca5591efe2aa1d1ccfcf58a3384c620ee7db50b9019a2974d30d62a8`|

All four documents have one physical page, index0. C29534 prints1/1; the other
pages have no printed page label. Exact dimension locators are the specification
or STRUCTURE/DIMENSION tables and adjacent plan/longitudinal section. Same-side
construction was read from both ends and support tapes, not inferred from suffix
A or B. Blank approval fields are not signed acceptance or lot evidence.

## Source-backed specification differences and unresolved mappings

Comparator is retained Hirose FH12 catalog SHA-256
`9f056f58ff000739633cc3cb7697ba185967083dcf1429b7ab10783b3f55bac5`.
Printed page2/index1 gives adaptive FFC contact requirements; page11/index10 UPPER
horizontal FFC drawing gives recommended dimensions. Do not transfer vertical
contact numbering or label every recommended dimension a guaranteed requirement.

| Quantity, mm unless noted | C81339 | C68390 | C29534 | FH12 comparator |
| --- | --- | --- | --- | --- |
| Insertion thickness interval |0.253–0.353|0.253–0.353|0.27–0.33|Required0.25–0.35|
| Total width interval |4.42–4.58|7.42–7.58|4.42–4.58|Recommended4.43–4.57 for8P,7.43–7.57 for14P|
| Exposed length at each end |3–5|3–5|2.5–3.5|Recommended minimum3.5|
| Reinforcing/support length |6–10|6–10|4–6|Recommended minimum4.5; end-support datum mapping must remain explicit|
| Contact finish |Not established|Not established|Tin, minimum1μm|Gold-plated adaptive contact specification|
| Stiffener thickness |Nominal0.225, tolerance absent|Nominal0.225, tolerance absent|Nominal0.225, tolerance absent|Recommended minimum0.188; nominal alone cannot establish guaranteed lower bound|

The two0.353mm maxima exceed the connector thickness limit by0.003mm; do not
dismiss this as assumed rounding. All three cable width intervals extend beyond
the recommended interval. Strip minima are too short; C29534's nominal3mm strip
is itself below3.5mm. Its supporting-end minimum also falls short if the reinforcing-tape length maps to Hirose's supported-end datum. Its explicit
tin finish differs from the mating gold specification. These are differences
between declared specifications, not a finding that every delivered unit fails.
No manufacturer clarification, measurement-based acceptance, waiver or replacement
selection has been performed.

C26618 and C32128 link the same generic page, containing family formulae but no
selected strip/support nominals or exact binding. Neither may inherit values from
other order codes. No bend-radius, folded-life, contact-1 placement or mounted
access proof follows from these drawings. C81339/C68390's unspecified finish
remains open even where dimensional intervals agree.

## Fastener source cross-check

The pinned resource catalog blob6032a3160f7a9d1c56f11fb03390af266dca72fe was also
re-inspected. Printed page132 confirms Keystone4708,M3,steel/nickel plate and
5.50mm hex width, but gives no nut-height dimension. Its washer table describes
shoulder washers, not the needed plain washer. ST-08's nut-height and
washer-thickness gaps remain UNSOURCED; four-site protrusion is not established.
No generic washer or nut was adopted to close the arithmetic.

## Next work and holds

The deterministic five-code interval audit is implemented at
`7e01f63367956a44b0b7c798684a972397b2fa93` and independently reviewed:12 tests
and30 actual comparisons pass as arithmetic checks. See
[scripts/checks/mc02_cable_contract](../../../../scripts/checks/mc02_cable_contract/README.md).
It rejects promotion of generic source scope and explicitly reports unbounded
stiffener thickness as UNSOURCED. This is not a compatibility PASS.
Source/transport/review/result archive index SHA-256:
`ef126968bede3b63a49b1983d5679d0b8d5d8e38518ffe4668f759e5f4ee237c`.
Actual drawings or manufacturer dispositions remain needed where requirements
conflict or applicability is unresolved. Source work does not release DRC, fill,
formal hardware adoption, manufacturing or the independent five-check gate.
