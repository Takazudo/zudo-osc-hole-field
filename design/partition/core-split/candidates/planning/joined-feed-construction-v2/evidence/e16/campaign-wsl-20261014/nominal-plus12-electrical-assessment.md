# Trustworthy first corrected coupled result — scope and next intervention

Execution source `9f69cd8a2e7b80cba813a5bd66546c4d5ac705ec`, attempt 4, request `e61a727361ad1a2fd0418d6d95c0cdae109a536d8b62a99654970685c0819c87`. Scope here is **+12V, nominal-average, uniform-dielectric, all-present only**. Other cases/nets were still running when inspected; this is not a global baseline PASS or postrun integrity certificate.

Read-only JSON/gzip extraction, no production import, pickle load, solve or source change. Output `/home/takazudo/.cache/zudo-e16-runs/coupled-approved-9f69cd8-4b95b6c8/coupled-+12V-nominal-average-uniform-dielectric.json.gz` hashes to `d637c087615d367d932bdb8d27165e53219362f6abe6f2972242889e2f18d5c2`, exactly matching adjacent `.json.gz.numerical.json`. Solver, assessment, service and exact request-bound `evidence/e16/continuation-20261013b/coupled-network-config.json` hashes also match. The older sibling config is not the request config and was not substituted. Machine-readable extraction is `nominal-plus12-electrical-extraction.json`.

Numerical criteria all pass at unchanged 1e-9 limits: global KCL 8.350158171748052e-11; maximum free-node KCL 1.1921328699180337e-11; driving-point residual 2.850814388399312e-10; energy/load-work residual 2.4050789107440344e-12. Nonnegative energy true. These validate the declared reported accuracy for this result; the receipt explicitly retains `electrical_acceptance: false`.

## Electrical facts supported by this completed result

| Quantity | KA | KB |
| --- | ---: | ---: |
| Included +12V subset load | 94.16 mA | 77.44 mA |
| Energized +12V pads | 76 | 40 |
| Evaluated driving-point pads | 275 | 250 |
| Copper resistance range | 1.078513–5.174020 mΩ | 2.156023–6.480953 mΩ |
| Paths over existing 1 mΩ copper requirement | 275 / 275 | 250 / 250 |
| Worst energized-pad copper resistance | U2111.4, 5.003294 mΩ | U7105.4, 5.992145 mΩ |
| Most negative model rail potential | U1310.4, −0.117419 mV | U4339.4, −0.288468 mV |

This is a trustworthy **negative modeled copper-resistance result** despite small voltage shifts at the declared subset loads. Do not lower loads or change targets to describe electrical success. Worst all-pad resistance is KA C2141.1 (passive zero DC) and KB U7405.4 (whole package excluded because its other required supply path is missing). The energized-pad maxima above avoid misrepresenting those as supplied devices. No finite path is missing among the already selected whole-device +12V load rows; that does not erase the baseline 59 partial, 21 unserved, or 194 unmapped packages.

Held KA source injection is 171.599999986 mA; W1 carries 77.439999959 mA to KB. The rail potentials are referenced to ideal held +12V source supports, not absolute 12 V readings and not the device's rail-to-local-ground error. No AGND result is included in this scope. ±12 V op-amps without an AGND pin must not acquire an invented nearest-ground return. Full source/protection/branch and dynamic/output loading remain absent.

Total network dissipation is 31.640309 µW, including W1 bulk 6.626634 µW. KA copper dissipates 21.149607 µW: barrels 14.068585, inner foil 6.457531, face copper 0.623491 µW. KA terminations add 0.227744 µW. KB copper dissipates 3.408580 µW: barrels 0.568852, inner foil 2.382941, face copper 0.456787 µW; KB termination 0.227744 µW. Barrel contribution is 66.519% of KA copper dissipation and 46.262% of total network dissipation. Dissipation class is not a current rating or physical temperature qualification.

## What this says about the seven-via candidate

It supports prioritizing **KA barrel/access resistance as a class for investigation**. It does not establish that receiving land TP990026, or any other specific candidate land, dominates. The JSON has only board/class energy, aggregate source injection and pad driving-point results. It has no per-via losses, per-source-land currents, or isolated trunk metric. No absent trunk value was reconstructed from old numerical results or by loading reductions.

The model holds three +12 V KA lands at one ideal potential: TP990002 (`982d0043-2374-5b74-b189-fead016006b5`), TP990014 (`8ba40524-d0d5-50d2-9a63-f7a23aa882a4`), and TP990026 (`4837930f-294a-5712-878f-44a71b63bce6`). Two are JL/JR branch lands, not a proved physical incoming source. This conditional equipotential support can redistribute entry current and prevents attributing a physical P-to-KA source bottleneck from aggregate energy alone.

The existing seven-via candidate remains a justified bounded **hypothesis for a future comparison**, not a demonstrated remedy. Only its TP990026 added via is on +12V; its six other vias are on -12V/+5V/AGND, which this result does not evaluate. Candidate geometry already has exact preservation/census evidence, so reusing that existing candidate is better grounded than blind wider routing. Before calling it an improvement, obtain a fresh separately admitted variant coverage/solve comparison using unchanged loads, geometry-independent source assumptions and tolerances, with per-land/per-barrel attribution if needed. Compare copper resistance at the same pad identities, voltage and dissipation; reject newly unserved paths or unacceptable resistance increases from added antipads. No numeric improvement percentage is supported yet.

The stronger partial-device alternative remains U2314.11/C2342.1 closure, but the existing long-B route's 34.7 mΩ analytic screen is poor, and selective In3 annulus reconnection needs new adapter/geometry permission. Neither intervention is executed or adopted by this analysis. KEEP_K1402_INCUMBENT, canonical copper and panel positions remain unchanged; all board designs remain unvalidated drafts.
