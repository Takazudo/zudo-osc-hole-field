# Bounded JR paired-movement experiment

Canonical JR input is SHA25635b52972dd70b4186cf3f3b7ee2ac3d70432f3476c2f56c9fcf9c1c4d7d4d445;
saved native dump is SHA256f885375bc4a8ac5cc0ca879f841a4d3768a560876e43c023e2abe14e38a86c8a.
Single-resistor movement produced no surviving complete route after connector
preflight. This changes the method to joint movement of a target and one of its
two nearest eligible same-face resistor neighbors, preserving every old copper
object and every existing pad landing with additive full-width bridges.

Predeclared bounds: nine original target resistors, at most two peers each;
cardinal shifts of +/-0.1 or +/-0.2mm for both parts (64 joint cases per pair).
No rotation/face changes, fixed parts, bypass clusters, connector movement or
power-rail peer pads. The existing source translator must accept the final joint
placement, including connector courtyards. Copper clearance remains0.25mm;
signal landing bridges remain0.2mm and AGND bridges0.3mm.

If static candidates exist, compare at most12 candidates distributed across
pairs, direct AGND and plane modes, against the already saved identical-input
unmoved controls. Keep the original16x16mm frame,0.0125mm raster,300000expansion
bound,0.6/0.3mm via and -12V fill guard. Stop at the first complete virtual
transaction. Untested candidates are not claimed negative.

This is read-only proposal work. Any positive result still requires native
source regeneration, exact source/board synchronization, all physical/electrical
constraints, DRC/parity, warning, original-group, retained-copper and settled/fresh
gates. No source placement or canonical board is changed by these scripts.

Result: guarded static screen PASS78s,1152cases/40candidates. Guarded routing comparison PASS112s,24trials across12selected candidates,zero complete routes.18search_exhausted and6no_legal_via_site findings; maximum43623expansions, below300000. No native run was warranted. The remaining28static candidates are untested, not claimed negative. No placement, copper or canonical board changed. Do not repeat this bound unchanged.
