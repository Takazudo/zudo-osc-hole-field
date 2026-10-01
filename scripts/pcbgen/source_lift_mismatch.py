"""Independent vertical-source-lift floor for a frozen depth-constant trial.

One read-only source-support mesh audit and no solver construction. The premise is
structural and hash-bound: sheet repair changes only in-plane current, while
the exact one-face vertical lift and zero vertical potential derivative remain.
"""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import time

from scripts.pcbgen.observation_support_bound import upward
from scripts.pcbgen.regional_probe import sha, verify_hashes, source_lift_region
from scripts.pcbgen.potential_pair_localization import check_complete_mismatch


def lift_floor(profile, layer, rho, thickness):
    """Identical columns turn the exact cross interval into a diagonal bound."""
    if rho <= 0 or thickness <= 0:
        raise ValueError('positive scalar resistivity and foil thickness required')
    result = source_lift_region([profile, profile], layer, rho, thickness)
    lo, hi = result['cross_interval']
    if hi < 0 or lo > hi:
        raise ValueError('invalid identical-profile lift diagonal')
    return [max(0., lo), hi]


def intersect_floor(previous, floor):
    lo, hi = map(F, previous)
    a, b = map(F, floor)
    if min(lo, a) < 0 or lo > hi or a > b:
        raise ValueError('invalid mismatch or independent floor interval')
    lo = max(lo, a)
    if lo > hi:
        raise ValueError('independent source lift contradicts prior upper')
    return [-upward(-lo), upward(hi)]


def audit_source_support(sheets, profiles, stored_sources):
    """Whole exact-grid triangles; full signed density, including overlaps.

    A repaired RT0 field has constant in-plane divergence in each triangle.
    Its exact requested source is area times the density proved here, so the
    linear-depth lift cancels divergence pointwise, not merely in integral.
    """
    import numpy as np
    import shapely
    from scripts.pcbgen.sheet_flux import grid_area_twice
    rows = []
    for layer, sheet in enumerate(sheets):
        density = [{}, {}]
        areas = {}
        for k, profile in enumerate(profiles):
            for pl, patch, current in profile:
                if pl != layer:
                    continue
                denominator = grid_area_twice(patch)
                if denominator <= 0:
                    raise ValueError('empty finite source support')
                rectangles = []
                for part in shapely.get_parts(patch):
                    if not part.equals(shapely.box(*part.bounds)):
                        raise ValueError('rectangular exact-grid sources required')
                    rectangles.append([round(x*10**9) for x in part.bounds])
                covered = 0
                for i in sheet.tree.query(patch, predicate='intersects'):
                    if sheet.polygons[i].intersection(patch).area <= 0:
                        continue
                    points = sheet.metric_xy[sheet.triangles[i]]
                    grid = np.rint(points*10**9).astype(np.int64)
                    if np.max(abs(points-grid.astype(np.longdouble)/np.longdouble(10**9))) > 1e-15:
                        raise ValueError('current source triangle leaves exact grid convention')
                    if not any(np.all((grid[:,0]>=x0)&(grid[:,0]<=x1)&
                                      (grid[:,1]>=y0)&(grid[:,1]<=y1))
                               for x0,y0,x1,y1 in rectangles):
                        raise ValueError('partial current source triangle; lift premise not established')
                    a,b,c = grid.tolist()
                    area2 = abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
                    if area2 <= 0:
                        raise ValueError('degenerate source triangle')
                    covered += area2
                    areas[int(i)] = area2
                    density[k][int(i)] = density[k].get(int(i), F()) + F(current)*2*10**18/denominator
                if covered != denominator:
                    raise ValueError('current source patch coverage is not exact')
        expected = np.zeros_like(stored_sources[layer])
        if expected.shape != (len(sheet.triangles), 2):
            raise ValueError('retained source operand shape changed')
        records = []
        for i in sorted(areas):
            for k in range(2):
                expected[i,k] = float(density[k].get(i,F())*F(areas[i],2*10**18))
            records.append({'triangle': i, 'vertices_grid_pm':
                            np.rint(sheet.metric_xy[sheet.triangles[i]]*10**9).astype(np.int64).tolist(),
                            'twice_area_pm2': areas[i],
                            'signed_density_A_per_mm2': [str(d.get(i,F())) for d in density]})
        # This frozen pair has disjoint source/return rectangles. Retained
        # area_current rounds each rational per-cell source once; verify it.
        if not np.array_equal(expected, stored_sources[layer]):
            raise ValueError('retained source operands differ from exact signed cell density')
        rows.append({'layer': layer, 'source_triangles': records,
                     'retained_rounded_source_operand_exact_match': True})
    return rows


def run(manifest_path, output):
    started = time.monotonic()
    manifest_path = Path(manifest_path)
    raw = manifest_path.read_bytes()
    m = json.loads(raw)
    own = {str(manifest_path): hashlib.sha256(raw).hexdigest(),
           str(Path(__file__)): sha(__file__)}
    closure = {**m['input_sha256'], **own}
    verify_hashes(closure)
    out = Path(output)
    if out.exists() or not out.resolve().is_relative_to(Path('.circuit-cache').resolve()):
        raise ValueError('fresh ignored output directory required')
    capture = json.loads(Path(m['capture']).read_bytes())
    prior = json.loads(Path(m['localization']).read_bytes())
    capture_manifest = json.loads(Path(capture['manifest']).read_bytes())
    if prior['input_sha256'].get(m['capture']) != m['input_sha256'][m['capture']]:
        raise ValueError('localization does not bind this capture')
    if capture['source_pair'] != [['J900134', '2'], ['C107', '2']]:
        raise ValueError('unsupported frozen pair')
    if capture['trace_reconstruction']['trace_definition'] != (
            'exact V_start+t*(V_end-V_start) on each canonical sector; constant in foil depth'):
        raise ValueError('depth-constant canonical trial premise changed')
    for dependencies in [capture['input_sha256'], prior['input_sha256'],
                         capture['native_prerequisite']['dependency_sha256']]:
        for path, digest in dependencies.items():
            if path in closure and closure[path] != digest:
                raise ValueError('inconsistent dependency identity')
            closure[path] = digest
    verify_hashes(closure)
    import shapely.geometry
    profile_document = json.loads(Path(capture_manifest['profiles']).read_bytes())
    if profile_document['active_sheet_layers'] != ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']:
        raise ValueError('frozen active physical layer mapping changed')
    retained = profile_document['profiles']
    lookup = {(p['ref'], p['pad']): p for p in retained}
    if len(lookup) != len(retained):
        raise ValueError('duplicate finite source identity')
    reference = lookup[('TP990031', '1')]
    profiles = []
    for identity in capture['source_pair']:
        positive = lookup[tuple(identity)]
        if any(p['layer'] != 3 for p in [positive, reference]):
            raise ValueError('this proof requires the frozen same-face B.Cu sources')
        profiles.append([(p['layer'], shapely.geometry.shape(p['patch_geojson']), sign)
                         for p, sign in [(positive, 1), (reference, -1)]])
    # Exactly the immutable nominal model expression; no selectable new class.
    rho = 1.7241e-5 * (1 + .003947 * 50)
    thickness = .07
    import pickle
    import numpy as np
    print('source lift: read-only current-mesh source-support audit; no solve', flush=True)
    _, sheets = pickle.loads(Path(capture_manifest['current_mesh']).read_bytes())
    with np.load(capture_manifest['current_fields']) as archive:
        source_audit = audit_source_support(sheets, profiles,
            [archive['sheet_sources_'+str(layer)] for layer in range(4)])
    del sheets
    names = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
    rows = prior['regions']
    if len(rows) != 199 or len({r['id'] for r in rows}) != 199:
        raise ValueError('complete unique prior region partition required')
    updated = {r['id']: r['mismatch_interval_ohm'] for r in rows}
    foil_rows = []
    for layer, name in enumerate(names):
        identity = 'foil:' + name
        previous = updated[identity]
        floors = [lift_floor(p, layer, rho, thickness) for p in profiles]
        revised = [intersect_floor(previous[k], floors[k]) for k in range(2)]
        updated[identity] = revised
        foil_rows.append({'id': identity, 'prior_mismatch_interval_ohm': previous,
                          'independent_vertical_lift_energy_interval_ohm': floors,
                          'intersected_mismatch_interval_ohm': revised})
    sums = []
    for k in range(2):
        check_complete_mismatch([r[k] for r in updated.values()],
                                prior['global_canonical_mismatch_upper_ohm'][k])
        sums.append(-upward(-sum((F(r[k][0]) for r in updated.values()), F())))
    result = {
        'status': 'CONDITIONAL NOMINAL INDEPENDENT SOURCE-LIFT FLOOR; no hardware/common admission',
        'input_sha256': closure, 'source_pair': capture['source_pair'], 'foils': foil_rows,
        'complete_region_mismatch_lower_sum_ohm': sums,
        'global_canonical_mismatch_upper_ohm': prior['global_canonical_mismatch_upper_ohm'],
        'nominal_rho_ohm_mm': rho, 'foil_thickness_mm': thickness,
        'current_source_support_audit': source_audit,
        'premises': ['Frozen isotropic scalar foil resistivity and one-face finite sources.',
                     'Exact vertical source lift is unchanged by in-plane sheet and barrel repair.',
                     'Whole exact-grid current source triangles have the prescribed pointwise constant density; repaired RT divergence cancels lift divergence.',
                     'Canonical potential is depth-constant throughout each complete foil.',
                     'Squared mismatch splits orthogonally into nonnegative in-plane energy and the exact vertical lift energy.',
                     'No raw-sheet conservation assumption; no penalty on the unchanged vertical component.',
                     'Historical zero foil lower remains valid but loose; this is a separate interval intersection.',
                     'Overlap and signed source cancellation retained; diagonal lower comes from identical-profile cross evaluation.'],
        'runtime_sec': time.monotonic() - started}
    verify_hashes(closure)
    out.mkdir(parents=True)
    receipt = out / 'receipt.json'
    receipt.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'receipt': str(receipt), 'sha256': sha(receipt),
                      'runtime_sec': result['runtime_sec'], 'lower_sum_ohm': sums}))
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', default='design/partition/source-lift-mismatch.json')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    run(args.manifest, args.output)
