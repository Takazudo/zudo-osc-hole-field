"""Select complete outer-only transactions; no native eligibility is inferred."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def build(plan, source):
    if source['base_sha256'] != plan['base_sha256']:
        raise ValueError('source base changed')
    selected=set(plan['selected_nets'])
    if not selected <= set(source['nets']):
        raise ValueError('unknown selected net')
    added=[r for r in source['added'] if r['net'] in selected]
    if any(r['net'] in selected for r in source['removed']):
        raise ValueError('selected transaction removes original copper')
    if any(r['layer'] not in ('F.Cu','B.Cu') or not r['block'].lstrip().startswith('(segment') for r in added):
        raise ValueError('selected transaction changes inner layers or drills')
    if {r['net'] for r in added} != selected:
        raise ValueError('empty selected transaction')
    return {'base_sha256':plan['base_sha256'],'added':added,'removed':[],'nets':sorted(selected)}
if __name__=='__main__':
    here=Path(__file__).resolve().parent;plan=json.loads((here/'plan.json').read_text())
    source=(ROOT/plan['source_replay']).read_bytes()
    if hashlib.sha256(source).hexdigest()!=plan['source_sha256']:
        raise ValueError('immutable source replay changed')
    if hashlib.sha256((ROOT/'boards/osc-core/osc-core.kicad_pcb').read_bytes()).hexdigest()!=plan['base_sha256']:
        raise ValueError('canonical core changed; reconcile successful copper first')
    out=here/'copper.json';result=build(plan,json.loads(source))
    out.write_text(json.dumps(result,sort_keys=True)+'\n')
    print(len(result['nets']),'nets',len(result['added']),'added, zero removed',hashlib.sha256(out.read_bytes()).hexdigest())
