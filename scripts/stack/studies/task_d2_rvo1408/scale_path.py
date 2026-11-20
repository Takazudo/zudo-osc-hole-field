"""Task D step 2: RVO1408 (O4 SCALE_TRIM) against its circuit role, by footprint origin distances.

The trim is a 1 kΩ rheostat from SCALE_ADJ to AGND; R1452 (1.5 kΩ R_RS_FIXED) joins SCALE_ADJ to SCALE_PIN, which
is AS3340 U1405 pin 14 with bypass C1410. For the canonical board, the cumulative link-gate projection and the ST-07
rear proposal, this reports the origin-to-origin XY distance and face of each hop. Origins are locators, not pad
or routed lengths, and a face change implies at least one via. Paper only."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PATH = (('RVO1408', 'R1452', '/O4/SCALE_ADJ'), ('R1452', 'U1405', '/O4/SCALE_PIN'), ('C1410', 'U1405', '/O4/SCALE_PIN'))


def run():
    side = json.loads((ROOT / 'design/reports/board-side-map.json').read_text())
    gate = json.loads((ROOT / 'design/stack/geometry/links/link-gate.json').read_text())
    plan = json.loads((ROOT / 'design/stack/trimmers/relocation-plan.json').read_text())
    canon = {r: (side[r]['footprint_origin_mm'], side[r]['BoardSide'][0]) for p in PATH for r in p[:2]}
    proj = dict(canon)
    for f in gate['replacement']['footprints']:
        if f['board'] == 'K' and f['ref'] in proj and f.get('new'):
            proj[f['ref']] = (f['new'], f['new_face'])
    rec = next(r for r in plan['records'] if r['ref'] == 'RVO1408')
    prop = dict(proj)
    prop['RVO1408'] = (rec['proposal']['xy_mm'], rec['proposal']['face'])
    # Same proposal, but with R1452 kept beside the trim: the hop that lengthens moves to SCALE_PIN instead.
    pair = dict(prop)
    pair['R1452'] = prop['RVO1408']
    out = {}
    for name, pos in (('canonical', canon), ('after_link_projection', proj), ('st07_rear_proposal', prop),
                      ('st07_proposal_with_R1452_beside_trim', pair)):
        hops = []
        for a, b, net in PATH:
            (pa, fa), (pb, fb) = pos[a], pos[b]
            hops.append({'from': a, 'to': b, 'net': net, 'xy_mm': round(math.dist(pa, pb), 2), 'faces': fa + fb,
                         'face_change': fa != fb})
        out[name] = {'positions': {r: [p, f] for r, (p, f) in pos.items()}, 'hops': hops}
    return {'status': 'TASK_D_STEP_2_RVO1408_SCALE_PATH', 'cases': out,
            'scope': 'Footprint-origin XY distances only; not pad, routed, parasitic or stability values. '
                     'The paired case is a what-if, not a proposal checked against any obstacle.'}


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    text = json.dumps(run(), indent=1) + '\n'
    if a.output:
        with a.output.open('x') as f:
            f.write(text)
    else:
        print(text, end='')
