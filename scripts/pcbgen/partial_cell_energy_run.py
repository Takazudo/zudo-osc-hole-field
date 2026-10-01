"""Bounded retained partial-cell diagnostic. No global/local field solve.

Inputs remain in an explicit read-only artifact root. A fresh ignored output
belongs to this worktree. Historical receipts are never rewritten or rebound.
"""
from fractions import Fraction as F
import hashlib
import heapq
import json
from pathlib import Path
import time
import numpy as np
from scripts.pcbgen.partial_cell_energy import (
    exact, CanonicalChart, ConservativeIndex, Budget, WorkCap,
    p1_energy_interval, covered_fraction)
from scripts.pcbgen.observation_support_bound import upward
from scripts.pcbgen.potential_pair_localization import (
    down, mismatch_interval, check_complete_mismatch)


REPO = Path(__file__).resolve().parents[2]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def snapshot_json(path, expected=None):
    """Parse precisely the bytes whose digest enters the receipt."""
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if expected is not None and digest != expected:
        raise ValueError('parsed JSON bytes differ from retained hash: '+str(path))
    return json.loads(raw), digest


def artifact_path(root, name):
    root = Path(root).resolve()
    path = Path(name)
    path = (root/path).resolve() if not path.is_absolute() else path.resolve()
    if not path.is_relative_to(root):
        raise ValueError('historical input outside explicit artifact root')
    return path


def merge_hashes(*maps):
    result = {}
    for mapping in maps:
        for name, value in mapping.items():
            if name in result and result[name] != value:
                raise ValueError('conflicting historical hash bindings')
            result[name] = value
    return result


def verify_inputs(root, historical, executed):
    for name, expected in historical.items():
        if sha(artifact_path(root, name)) != expected:
            raise ValueError('historical input hash mismatch: '+name)
    # Execute only local copies whose bytes match the historical code/data
    # contract. Native-only dependency files are checked at their old root.
    for name, expected in executed.items():
        relative = artifact_path(root, name).relative_to(Path(root).resolve())
        if sha(REPO/relative) != expected:
            raise ValueError('executed source epoch mismatch: '+str(relative))


def require_capture_bindings(config, capture, localization, root):
    """Selected capture -> named field artifact and localization -> capture."""
    capture_path = artifact_path(root, config['capture'])
    field_path = artifact_path(root, config['potential_fields'])
    if field_path != capture_path.parent/'potential-fields.npz':
        raise ValueError('selected field path is not the capture artifact')
    if config['input_sha256'].get(config['potential_fields']) != capture['artifact_sha256']['potential-fields.npz']:
        raise ValueError('selected field hash is not the capture artifact')
    capture_links = [digest for name, digest in localization['input_sha256'].items()
                     if artifact_path(root, name) == capture_path]
    expected = config['input_sha256'][config['capture']]
    if not capture_links or any(digest != expected for digest in capture_links):
        raise ValueError('localization is not bound to the selected capture')


def fresh_output(path, root):
    path = Path(path).resolve()
    if path.exists() or not path.is_relative_to(REPO/'.circuit-cache') or path.is_relative_to(Path(root).resolve()):
        raise ValueError('fresh own-worktree ignored output required')
    return path


def record_failure(output, root, error, frozen_core, frozen_runner):
    """Keep a failed bounded attempt without manufacturing an energy result."""
    path = fresh_output(output, root)
    record = {'status': 'NOT RUN missing retained input' if isinstance(error, FileNotFoundError) else 'FAILED diagnostic; no energy bound admitted',
        'exception_type': type(error).__name__, 'reason': str(error),
        'artifact_root': str(Path(root).resolve()),
        'requested_core_sha256': frozen_core, 'requested_runner_sha256': frozen_runner,
        'scope': 'Failure record only. No geometry tolerance or inherited premise was relaxed.'}
    path.mkdir(parents=True)
    (path/'failure.json').write_text(json.dumps(record, indent=2)+'\n')
    return record


def candidate_census(selected, potential_index, current_index, cap):
    """Stop before another target after the first exhausted census budget.

    One query returns at most the retained mesh's triangle count. A target
    that would exceed the cumulative cap is recorded, never truncated.
    """
    rows = []
    total = 0
    for target in selected:
        query = potential_index.boxes[target['id']]
        currents = len(current_index.query_box(query))
        potentials = len(potential_index.query_box(query))-1
        count = currents+potentials
        rows.append({'id': target['id'], 'current_candidates': currents,
                     'potential_neighbors': potentials,
                     'within_census_cap': total+count <= cap})
        if total+count > cap:
            break
        total += count
    return rows, total


def rank_excluded(chart, values, errors, included, sheet_ohm, limit, cell_cap):
    """Certified cell uppers; exact deterministic two-profile score ordering.

    Each bound is rounded outward to binary64 before summing. This avoids
    unbounded rational-denominator growth across thousands of cell areas.
    """
    excluded = np.flatnonzero(~included)
    if len(excluded) > cell_cap or limit < 1:
        raise ValueError('ranking work cap exceeded')
    heap = []
    all_upper = [F(), F()]
    for count, raw_id in enumerate(excluded):
        ident = int(raw_id)
        _, canonical, _ = chart.cell(ident)
        vertices = chart.sheet.triangles[ident]
        bounds = []
        for k in range(2):
            lo, hi = p1_energy_interval(canonical, values[vertices, k], errors[vertices, k],
                sheet_ohm, chart.sheet.metric_factors[ident])
            bounds.append((down(lo), upward(hi)))
            all_upper[k] += exact(bounds[-1][1])
        score = sum((exact(row[1]) for row in bounds), F())
        item = (score, -ident, ident, bounds)
        if len(heap) < limit:
            heapq.heappush(heap, item)
        elif item[:2] > heap[0][:2]:
            heapq.heapreplace(heap, item)
        if count and count % 16384 == 0:
            print('partial-cell: ranked excluded cells', count, flush=True)
    rows = [{'id': ident, 'full_cell_energy_interval_ohm': bounds,
             'score_exact': str(score)} for score, _, ident, bounds in sorted(heap, key=lambda x: (-x[0], x[2]))]
    return rows, [upward(x) for x in all_upper]


def integrate_selected(selected, included, potential, current, potential_index, current_index, budget):
    """All incomplete/rejected targets retain zero added lower energy."""
    ids = [row['id'] for row in selected]
    if len(ids) != len(set(ids)) or any(i < 0 or i >= len(included) or included[i] for i in ids):
        raise ValueError('duplicate, foreign or already counted potential target')
    total = [F(), F()]
    rows = []
    exhausted = False
    for target in selected:
        ident = target['id']
        record = {'id': ident, 'full_cell_energy_interval_ohm': target['full_cell_energy_interval_ohm']}
        if exhausted:
            record['status'] = 'UNPROCESSED work cap exhausted'
            rows.append(record)
            continue
        try:
            query = potential_index.boxes[ident]
            curr_ids = current_index.query_box(query)
            near_ids = [i for i in potential_index.query_box(query) if i != ident]
            record['current_candidates'] = len(curr_ids)
            record['potential_neighbors'] = len(near_ids)
            budget.charge('candidates', len(curr_ids)+len(near_ids))
            nominal, canonical, epsilon = potential.cell(ident)
            current_witnesses = ((i, current.cell(i)[0], current.cell(i)[2]) for i in curr_ids)
            nearby = ((i, potential.cell(i)[1]) for i in near_ids)
            fraction, covered, upper, pieces = covered_fraction(
                nominal, epsilon, canonical, current_witnesses, nearby, budget)
            contributions = [down(fraction*exact(v[0])) for v in target['full_cell_energy_interval_ohm']]
            for k in range(2):
                total[k] += exact(contributions[k])
            record.update(status='CONDITIONAL certified numerical subset',
                covered_area_mm2_exact=str(covered), full_cell_area_upper_mm2_exact=str(upper),
                fraction_lower_exact=str(fraction), contributing_pieces=pieces,
                added_energy_lower_ohm=contributions)
        except WorkCap as exc:
            exhausted = True
            record.update(status='UNPROCESSED work cap exhausted', reason=str(exc))
        except ValueError as exc:
            record.update(status='REJECTED geometry witness; zero added lower', reason=str(exc))
        rows.append(record)
        if len(rows) % 256 == 0:
            print('partial-cell: completed targets', len(rows), flush=True)
    return rows, [down(x) for x in total]


def refined_region(localization, added):
    """Keep all old uppers/work/current terms and every other region intact."""
    old = next(r for r in localization['regions'] if r['id'] == 'foil:B.Cu')
    result = json.loads(json.dumps(old))
    for k in range(2):
        if exact(added[k]) < 0:
            raise ValueError('negative added lower')
        interval = result['potential_energy_interval_ohm'][k]
        interval[0] = down(exact(interval[0])+exact(added[k]))
        if interval[0] > interval[1]:
            raise ValueError('refined lower contradicts retained outer upper')
        result['mismatch_interval_ohm'][k] = mismatch_interval(
            result['current_energy_interval_ohm'][k], interval, result['work_interval_ohm'][k],
            localization['global_canonical_mismatch_upper_ohm'][k])
        rows = [result if row['id'] == result['id'] else row for row in localization['regions']]
        check_complete_mismatch([row['mismatch_interval_ohm'][k] for row in rows],
                                localization['global_canonical_mismatch_upper_ohm'][k])
    return result


def load_sheet(path, layer):
    import gc
    import pickle
    from types import SimpleNamespace
    # Hash verification precedes every trusted retained pickle load.
    with Path(path).open('rb') as stream:
        key, sheets = pickle.load(stream)
    sheet = sheets[layer]
    result = SimpleNamespace(**{name: getattr(sheet, name) for name in
        ('metric_xy', 'triangles', 'metric_factors', 'interface_faces')})
    del sheets, sheet
    gc.collect()
    return key, result


def run(config_path, artifact_root, output, frozen_core, frozen_runner, census_only=False):
    import platform
    import resource
    import scipy
    import shapely
    from scripts.pcbgen.ground_volume_geometry import extract
    started = time.monotonic()
    root = Path(artifact_root).resolve()
    output = fresh_output(output, root)
    config_path = Path(config_path).resolve()
    config, config_digest = snapshot_json(config_path)
    if config['layer'] != 'B.Cu' or config['layer_index'] != 3 or config['status'] != 'UNSELECTED conditional numerical diagnostic':
        raise ValueError('unexpected diagnostic scope')
    if (type(config['selected_limit']) is not int or not 1 <= config['selected_limit'] <= 4096
            or type(config['ranking_cell_cap']) is not int or not 1 <= config['ranking_cell_cap'] <= 150000
            or set(config['work_caps']) != {'candidates', 'clips', 'overlap_checks'}
            or any(type(v) is not int or not 1 <= v <= maximum for v, maximum in
                ((config['work_caps']['candidates'], 500000), (config['work_caps']['clips'], 500000),
                 (config['work_caps']['overlap_checks'], 1000000)))):
        raise ValueError('bounded diagnostic work caps required')
    own = {str(config_path): config_digest, str(Path(__file__).resolve()): frozen_runner,
           str(REPO/'scripts/pcbgen/partial_cell_energy.py'): frozen_core}
    def verify_own():
        if any(sha(name) != expected for name, expected in own.items()):
            raise ValueError('diagnostic code differs from reviewed freeze')
    verify_own()
    for name, expected in config['input_sha256'].items():
        if sha(artifact_path(root, name)) != expected:
            raise ValueError('configured input hash mismatch: '+name)
    capture, _ = snapshot_json(artifact_path(root, config['capture']), config['input_sha256'][config['capture']])
    localization, _ = snapshot_json(artifact_path(root, config['localization']), config['input_sha256'][config['localization']])
    require_capture_bindings(config, capture, localization, root)
    if capture['source_pair'] != [['J900134', '2'], ['C107', '2']] or capture['reference_contact']['ref'] != 'TP990031' or capture['reference_contact']['pad'] != '1':
        raise ValueError('captured source identities changed')
    historical = merge_hashes(config['input_sha256'], capture['input_sha256'],
        capture['native_prerequisite']['dependency_sha256'], localization['input_sha256'])
    if historical.get(config['potential_fields']) != capture['artifact_sha256']['potential-fields.npz']:
        raise ValueError('potential field artifact binding changed')
    executed = {name: value for name, value in capture['input_sha256'].items()
        if not artifact_path(root, name).relative_to(root).parts[0].startswith('.')}
    # The immutable localization helper is imported by this runner too.
    for name, value in localization['input_sha256'].items():
        if artifact_path(root, name).relative_to(root).as_posix() == 'scripts/pcbgen/potential_pair_localization.py':
            executed[name] = value
    def verify():
        verify_own()
        verify_inputs(root, historical, executed)
    verify()
    libraries = {'python': platform.python_version(), 'numpy': np.__version__,
                 'scipy': scipy.__version__, 'shapely': shapely.__version__}
    if libraries != capture['libraries']:
        raise ValueError('numeric environment differs from capture')
    manifest, _ = snapshot_json(artifact_path(root, capture['manifest']), historical[capture['manifest']])
    old_full, _ = snapshot_json(artifact_path(root, manifest['full_receipt']), historical[manifest['full_receipt']])
    rho = 1.7241e-5*(1+.003947*50)
    print('partial-cell: unchanged geometry/ownership reconstruction; no field solve', flush=True)
    geometry = extract(artifact_path(root, manifest['native']), rho,
        refinement=old_full['refinement'], include_loads=True, main_strands=True)
    if geometry['barrel_ownership'] != old_full['barrel_ownership'] or geometry['active_sheet_layers'][3] != 'B.Cu':
        raise ValueError('geometry ownership or layer changed')
    interfaces = [{'centre': centre, 'relative': barrel.interface_polygon()} for barrel, centre in geometry['barrels']]
    key, potential_sheet = load_sheet(artifact_path(root, manifest['potential_mesh']), 3)
    if key != manifest['potential_cache_key']:
        raise ValueError('potential mesh cache key changed')
    _, current_sheet = load_sheet(artifact_path(root, manifest['current_mesh']), 3)
    if (len(potential_sheet.triangles), len(current_sheet.triangles)) != tuple(config['triangle_counts_potential_current']):
        raise ValueError('retained triangle counts changed')
    potential = CanonicalChart(potential_sheet, interfaces)
    current = CanonicalChart(current_sheet, interfaces)
    # A broad phase can exclude an unseen bad coordinate: validating only
    # returned candidates would be circular. Audit BOTH complete vertex sets.
    potential.validate_all_vertices()
    current.validate_all_vertices()
    polygons = shapely.polygons(np.asarray(potential_sheet.metric_xy[potential_sheet.triangles], dtype=float))
    inner_guard = geometry['inner'][3].buffer(-2e-9, join_style='mitre')
    included = np.asarray(shapely.covers(inner_guard, polygons), dtype=bool)
    del polygons, geometry
    old_region = next(r for r in localization['regions'] if r['id'] == 'foil:B.Cu')
    if int(included.sum()) != old_region['potential_envelope']['guaranteed_inner_cells']:
        raise ValueError('old whole-cell inclusion mask count changed')
    field_path = artifact_path(root, config['potential_fields'])
    with np.load(field_path) as fields:
        values, errors = fields['nodal_3'], fields['nodal_error_3']
    if values.shape != (len(potential_sheet.metric_xy), 2) or errors.shape != values.shape or not np.isfinite(values).all() or not np.isfinite(errors).all() or np.min(errors) < 0:
        raise ValueError('invalid captured nodal coefficient intervals')
    from scripts.pcbgen.foil_stack import resolve_stack
    native, _ = snapshot_json(artifact_path(root, manifest['native']), historical[manifest['native']])
    thickness = resolve_stack(native['stackup'], native.get('thickness_mm'))['thickness'][3]
    selected, excluded_upper = rank_excluded(potential, values, errors, included,
        exact(rho)/exact(thickness), config['selected_limit'], config['ranking_cell_cap'])
    potential_index, current_index = ConservativeIndex(potential_sheet), ConservativeIndex(current_sheet)
    # Census is bounded by the selected-cell count; no all-pairs materialization.
    census, census_count = candidate_census(selected, potential_index, current_index, config['work_caps']['candidates'])
    budget = Budget(config['work_caps'])
    rows, added = ([], [0., 0.]) if census_only else integrate_selected(
        selected, included, potential, current, potential_index, current_index, budget)
    refined = refined_region(localization, added)
    remaining = []
    for k in range(2):
        old_upper = exact(old_region['potential_envelope']['excluded_or_crossing_cell_energy_upper_ohm'][k])
        if exact(added[k]) > old_upper:
            raise ValueError('covered lower contradicts excluded-cell upper')
        remaining.append(upward(old_upper-exact(added[k])))
    result = {'status': 'CENSUS ONLY; integration NOT RUN' if census_only else 'CONDITIONAL retained partial-cell lower; no physical admission',
        'artifact_root': str(root), 'historical_input_sha256': historical, 'diagnostic_sha256': own,
        'libraries': libraries, 'layer': 'B.Cu', 'inherited_premise': config['inherited_premise'],
        'old_inclusion_mask_sha256': hashlib.sha256(included.tobytes()).hexdigest(),
        'whole_cell_count': int(included.sum()), 'excluded_cell_count': int((~included).sum()),
        'selection_policy': config['selection_policy'], 'selected': selected,
        'selected_ids_sha256': hashlib.sha256(json.dumps([r['id'] for r in selected]).encode()).hexdigest(),
        'candidate_census': census, 'census_candidates_within_cap': census_count,
        'work_caps': budget.limits, 'work_used': budget.used,
        'geometry_rows': rows, 'potential_chart': potential.audit(), 'current_chart': current.audit(),
        'all_excluded_new_cell_energy_upper_ohm': excluded_upper,
        'added_potential_energy_lower_ohm': added,
        'unchanged_excluded_full_cell_upper_ohm': old_region['potential_envelope']['excluded_or_crossing_cell_energy_upper_ohm'],
        'uncovered_or_unprocessed_energy_upper_ohm': remaining,
        'old_region': old_region, 'refined_region': refined,
        'unchanged_global_canonical_mismatch_upper_ohm': localization['global_canonical_mismatch_upper_ohm'],
        'runtime_sec': time.monotonic()-started, 'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'limits': ['Nominal current-inner containment is inherited, not independently physically certified.',
                   'No source, trace, field, mesh, geometry, material, electrical threshold or old receipt changed.',
                   'Remaining energy is an uncertainty upper, not identified physical mismatch.',
                   'All old current/source/Green/barrel/outer-upper costs remain unchanged.']}
    verify()
    output.mkdir(parents=True)
    (output/'partial-cell-energy.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'output': str(output/'partial-cell-energy.json'), 'runtime_sec': result['runtime_sec'],
        'added_lower_ohm': added, 'work_used': budget.used}), flush=True)
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='design/partition/partial-cell-energy.json')
    parser.add_argument('--artifact-root', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--frozen-core-sha256', required=True)
    parser.add_argument('--frozen-runner-sha256', required=True)
    parser.add_argument('--census-only', action='store_true')
    args = parser.parse_args()
    try:
        run(args.config, args.artifact_root, args.output, args.frozen_core_sha256, args.frozen_runner_sha256, args.census_only)
    except Exception as error:
        record_failure(args.output, args.artifact_root, error, args.frozen_core_sha256, args.frozen_runner_sha256)
        raise
