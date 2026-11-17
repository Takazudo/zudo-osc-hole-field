# Exact Molex150200075 candidate source contract

Source-only comparison of an **unadopted**8P,51±2mm,typeA same-side candidate.
SD-15020-001 revisionF sheet1 explicitly binds150200075 in that row/column.
The URL filename150200175 and drawing-template revisionA do not identify it.
Both transferred PDF pages were visually reviewed; raw bytes stay ignored.

```sh
python3 -B scripts/checks/mc02_molex_candidate/audit.py
python3 -B -m unittest discover -s scripts/checks/mc02_molex_candidate -p 'test_*.py'
```

The exact28 retained C29534 link IDs define candidate scope only. No existing
cable assignment, geometry or BOM changes. The comparator preserves FH12
required0.25–0.35mm end thickness versus recommended width, strip and support
figures. Thickness matches the declared interval; width4.40–4.60 exceeds the
recommended4.43–4.57 by0.03 at each end. Strip3.20–4.80 has minimum below3.5.
Stiffener length4–8 versus minimum4.5 is conditional on accepted datum mapping.
The0.155mm polyester stiffener is nominal-only, below recommended0.188 nominally,
with no guaranteed thickness interval. Gold name agreement is not contact/plating
qualification. Conductor width0.30±0.03 is distinct from end thickness0.30±0.05.

The drawing's0.10mm nominal copper differs from retained0.035mm model input.
No tolerance is supplied for copper, polyester/adhesive0.086mm layers or0.155mm
stiffener: blank general linear tolerances cannot be invented. The existing
capacitance kernel assumes coplanar zero-thickness strips. An eps_eff sweep does
not establish coverage of finite-thickness geometry at0.10mm. Dielectric,
resistivity/temperature, contact/end-equivalent and folded material properties
remain unbound. The prior51mm result SHA8768bb1c... is preserved and verified;
it varied nominal length only with unchanged LX-based material parameters.
It does not cover49–53mm tolerance or establish exact product applicability.

No electrical study, native, DRC, fill, substitution, formal adoption or
manufacturing is performed. The tool reads pinned sources and writes stdout;
retain outputs under ignored cache. Next work needs a reviewed material/model
applicability contract or manufacturer dimensional disposition; this audit does
not automatically authorize a53mm study, waive recommended dimensions or make
an all-units-fail claim. Data sources include verified Molex4c311..., Hirose
catalog9f056... and EDCc325...; EDC is retained context, not a replacement for
the catalog's explicitly labeled requirements/recommendations.

Terminal positional/datum conformity remains NOT_ASSESSED: Hirose EDC sheet3's
basic boxed0.5 pitch and nX true-position0.05 relative to datumZ are not equivalent
to Molex's0.50±0.05 pitch and0.5(N−1)±0.10 span. Matching nominal pitch supplies
no scalar GD&T comparison or physical conformity result.
