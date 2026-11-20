"""Task C step 3a: bind the K-rear latch neighbours of the 31 NOT SHOWN latches to exact sourced heights.

DS-88 exempted chip 0603, SOD-123 and SOT-23 neighbours as ASSUMED lower than the 2.0 mm connector body
with no height retained. This reads each remaining neighbour's MPN from the K schematic sheets, takes the
maximum body height from evidence.json, checks every source file hash, and re-states each verdict.
Neighbour heights only: open-actuator sweep, finger approach and fold are not decided here."""
import argparse, glob, hashlib, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
GATE = ROOT / 'design/stack/geometry/links/link-gate.json'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def schematic_parts(refs):
    out = {}
    for f in sorted(glob.glob(str(ROOT / 'boards/osc-core/sheets/*.kicad_sch'))):
        for blk in re.split(r'\n\s*\(symbol \(lib_id', Path(f).read_text())[1:]:
            p = dict(re.findall(r'\(property "([^"]+)" "([^"]*)"', blk))
            r = p.get('Reference')
            if r in refs:
                out.setdefault(r, set()).add((p.get('MPN', ''), p.get('Footprint', ''), Path(f).name))
    bad = {r: v for r, v in out.items() if len(v) != 1}
    if bad or set(out) != set(refs):
        raise ValueError('ambiguous or missing schematic binding: %r' % (bad or set(refs) - set(out)))
    return {r: dict(zip(('mpn', 'footprint', 'sheet'), next(iter(v)))) for r, v in out.items()}


def verify_sources(ev):
    for mpn, h in ev['heights'].items():
        if 'sha256' in h and sha(ROOT / h['path']) != h['sha256']:
            raise ValueError('source changed for %s' % mpn)
        if 'fact_id' in h:
            facts = json.loads((ROOT / h['path']).read_text())['facts']
            if not any(x['fact_id'] == h['fact_id'] for x in facts):
                raise ValueError('fact missing for %s' % mpn)


def run():
    ev = json.loads((HERE / 'evidence.json').read_text())
    verify_sources(ev)
    gate = json.loads(GATE.read_text())
    cases = [(l['id'], l['latch_reach']) for l in gate['links'] if not l.get('gone')
             and str((l.get('latch_reach') or {}).get('verdict', '')).startswith('NOT')]
    refs = {r for _, lr in cases for r in lr['remaining']}
    parts = schematic_parts(refs)
    limit = ev['connector']['closed_height_min_mm']
    rows, tally = [], {}
    for lid, lr in cases:
        nb, gaps = [], []
        for r in lr['remaining']:
            p = parts[r]
            h = ev['heights'].get(p['mpn'])
            nb.append({'ref': r, **p, 'max_mm': h and h['max_mm']})
            if h is None:
                gaps.append('%s identity unbound' % r if not p['mpn'] else '%s %s height unsourced' % (r, p['mpn']))
            elif h['max_mm'] >= limit:
                gaps.append('%s %.2f mm not below the closed body' % (r, h['max_mm']))
        tallest = max((n['max_mm'] for n in nb if n['max_mm'] is not None), default=None)
        verdict = 'LOWER THAN BODY (sourced)' if not gaps else 'NOT SHOWN'
        tally[verdict] = tally.get(verdict, 0) + 1
        rows.append({'link': lid, 'verdict': verdict, 'tallest_sourced_mm': tallest,
                     'margin_mm': round(limit - tallest, 3) if tallest is not None and not gaps else None,
                     'open_items': gaps, 'neighbours': nb})
    if len(rows) != gate['summary']['latch_not_shown']:
        raise ValueError('latch case count changed')
    return {'status': 'TASK_C_STEP_3A_NEIGHBOUR_HEIGHTS', 'gate_sha256': sha(GATE),
            'evidence_sha256': sha(HERE / 'evidence.json'), 'closed_height_min_mm': limit,
            'tally': tally, 'cases': rows,
            'scope': ('Neighbour body heights only, from schematic MPN properties (placement binding NOT RUN). A '
                      'LOWER THAN BODY case has the same footing as the retained open latches; open-actuator '
                      'sweep (reference 4.8 mm at 90 deg, not a maximum), central finger approach, cable fold '
                      'and solder fillet height stay open for every latch. No geometry or BOM change.')}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    text = json.dumps(run(), indent=1) + '\n'
    if a.output:
        with a.output.open('x') as f:
            f.write(text)
    else:
        print(text, end='')
