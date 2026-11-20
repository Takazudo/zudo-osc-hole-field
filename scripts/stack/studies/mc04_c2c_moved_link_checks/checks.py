"""Task C step 2c: retained per-link figures for the five improving link moves of step 2b.

For each moved link, recomputes with the retained links_gate functions the cable needed and loop, the K-field
compliance (DS-87 limit and holding-hand list), the leads to trim under the front tail, and the class-distance
accept, and compares them with the recorded link. The coupling ratio does not depend on placement: the stock
cable length and conductor order are unchanged, so the retained ratio carries over. Room/paper only."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'scripts/stack/geometry'))
import links_gate as lg  # noqa: E402
import links_gate_part2 as p2  # noqa: E402
import stackgeom as sg  # noqa: E402

SRC = ROOT / 'scripts/stack/studies/mc04_c2b_link_shift_replace/result.json'


def run():
    step = json.loads(SRC.read_text())
    moves = {lid: step['results'][lid]['best']['geometry'] for lid in step['combined_improving_moves']['links']}
    doc = json.loads((ROOT / 'design/stack/geometry/links/link-gate.json').read_text())
    inp = lg.load_inputs(sg.ROOT)
    sites, model, ctx, out, s, refs = lg.gate_run(inp, {})
    site_by = {x['id']: x for x in sites}
    limits = p2.limits_of(ctx.gopts)
    cm = model.compliance
    rows = {}
    for lid, geo in moves.items():
        r = next(x for x in doc['links'] if x['id'] == lid)
        f = r['front_board']
        size = lg.rec_size(ctx, r)
        need = ctx.need(f, geo['a_mm'], geo['b_mm'])
        comp = lg.cvalue(ctx.cmap, geo['K_connector'])
        rows[lid] = {
            'recorded': {'cable_needed_mm': r['cable_needed_mm'], 'loop_mm': r['loop_mm'],
                         'compliance_mm_per_N': r['compliance_mm_per_N'], 'trim_leads': r['trim_leads']},
            'moved': {'cable_needed_mm': round(need, 4), 'loop_mm': round(size['cable_length_mm'] - need, 4),
                      'compliance_mm_per_N': comp, 'trim_leads': lg.trim_list(ctx.model, f, geo),
                      'front_extension_mm': geo['front_extension_mm'], 'K_extension_mm': geo['K_extension_mm']},
            'cable_fits': size['cable_length_mm'] - need >= -1e-9,
            'compliance_within_limit': comp is not None and comp <= cm.limit + 1e-12,
            'holding_hand': comp is None or comp > cm.list_above,
            'class_accept': p2.class_accept(r, site_by, limits)(geo) or 'ACCEPT',
        }
    return {'status': 'TASK_C_STEP_2C_MOVED_LINK_FIGURES',
            'source_sha256': hashlib.sha256(SRC.read_bytes()).hexdigest(),
            'compliance_limit_mm_per_N': cm.limit, 'holding_hand_above_mm_per_N': cm.list_above, 'links': rows,
            'coupling': 'unchanged: placement does not enter the retained ratio (stock length and order unchanged)',
            'scope': 'Paper figures with the retained functions; no electrical review of re-placed parts; no canonical write.'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    text = json.dumps(run(), indent=1) + '\n'
    if a.output:
        with a.output.open('x') as fh:
            fh.write(text)
    else:
        print(text, end='')
