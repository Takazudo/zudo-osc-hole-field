"""Require exact named original-grid P vias before native insertion."""
from scripts.pcbgen.uuid_tools import stable_uuid


def validate(plan, manifest, native):
    if native['board_id'] != 'osc-control' or plan['board_sha256'] != native['board_sha256']:
        raise ValueError('P array plan belongs to a different native authority')
    if [plan['via_diameter_mm'], plan['via_drill_mm'], plan['pitch_mm']] != [.7, .3, .7]:
        raise ValueError('P original finite array geometry changed')
    lands = {row['reference']: row for row in manifest['all_P_main_lands']}
    rows = plan['rows']
    if len(rows) != 6 or len({row['ref'] for row in rows}) != 6 or {row['ref'] for row in rows} != set(lands):
        raise ValueError('P array source must cover every fixed main land once')
    pads = {(row['ref'], row['pad']): row for row in native['items'] if 'ref' in row}
    if len(pads) != sum('ref' in row for row in native['items']):
        raise ValueError('Duplicate native P pad identity')
    all_ids = set()
    for row in rows:
        land = lands[row['ref']]
        pad = pads[row['ref'], '1']
        centre = [a+b for a, b in zip(land['center_mm'], [100, 50])]
        if row['net'] != land['net'] or row['owning_pad_uuid'] != pad['uuid'] or pad['xy_mm'] != centre or pad['net'] != row['net'] or set(pad['copper']) != {'B.Cu'}:
            raise ValueError('P finite array owner/net/face/position changed')
        if not row['legal_sites']:
            raise ValueError('P land has no finite transfer sites')
        indices = set()
        for accepted, sites in ((True, row['legal_sites']), (False, row['blocked_sites'])):
            for site in sites:
                ix, iy = site['grid_index']
                if (ix, iy) in indices or not (0 <= ix < 5 and 0 <= iy < 5) or int(ix) != ix or int(iy) != iy:
                    raise ValueError('P original-grid site missing/duplicated/invalid')
                indices.add((ix, iy))
                expected = [centre[0]+(ix-2)*.7, centre[1]+(iy-2)*.7]
                if max(abs(a-b) for a, b in zip(expected, site['xy_mm'])) > 1e-9:
                    raise ValueError('P finite via shifted off its named original grid')
                uid = stable_uuid('osc-control', 'load-array:'+row['net'], row['ref']+':'+str(ix)+':'+str(iy))
                if site['uuid'] != uid or uid in all_ids:
                    raise ValueError('P finite via source UUID changed or duplicated')
                all_ids.add(uid)
                if accepted == bool(site['collisions']):
                    raise ValueError('P accepted/blocked site collision disposition changed')
        if len(indices) != 25:
            raise ValueError('P planner must account for all 25 original candidates per land')
    count = sum(len(row['legal_sites']) for row in rows)
    if count != plan['retained_via_count']:
        raise ValueError('P accepted finite via count differs')
    return {'status': 'PASS explicit P finite via ownership only; native gates still required',
            'land_count': len(rows), 'accepted_count': count, 'accounted_candidate_count': len(all_ids)}
