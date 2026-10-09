"""Materialize the reviewed core transaction; never modify canonical boards.

Run from the repository root. plan.json pins source copper and the unchanged
base. The native merger independently checks every proposed topology change.
"""
import hashlib,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.uuid_tools import stable_uuid


def build(plan,source):
    if source['base_sha256']!=plan['base_sha256']:
        raise ValueError('wrong base for reviewed recovery')
    omitted=set(plan['omit_new_nets'])
    if not omitted<=set(source['nets']):raise ValueError('omitted net absent from source')
    added=[r for r in source['added'] if r['net'] not in omitted]
    removed=[r for r in source['removed'] if r['net'] not in omitted]
    cluster=plan['via_cluster'];members={v['uuid']:v for v in cluster['members']}
    target=members[cluster['retained_via']]
    if cluster['net'] in source['nets']:raise ValueError('cluster overlaps recovered routing')
    if cluster['layers']!=['F.Cu','In2.Cu','In3.Cu','B.Cu'] or cluster['width_nm']!=200000:
        raise ValueError('reviewed signal constraints changed')
    def mm(n):return f'{n/1e6:.6f}'.rstrip('0').rstrip('.')
    for uid,via in sorted(members.items()):
        if via['net']!=cluster['net'] or via['diameter']!=600000 or via['drill']!=300000:
            raise ValueError('unexpected source via geometry')
        if uid==cluster['retained_via']:continue
        removed.append({'uuid':uid,'net':cluster['net']})
        for layer in cluster['layers']:
            new_id=stable_uuid('osc-core','issue189-reviewed-cluster',uid+':'+layer)
            block=('(segment\n\t\t(start '+ ' '.join(map(mm,via['xy'])) +')\n'
                   '\t\t(end '+ ' '.join(map(mm,target['xy'])) +')\n'
                   '\t\t(width 0.2)\n\t\t(layer "'+layer+'")\n'
                   '\t\t(net "'+cluster['net']+'")\n\t\t(uuid "'+new_id+'")\n\t)')
            added.append({'uuid':new_id,'net':cluster['net'],'layer':layer,'block':block})
    return {'base_sha256':plan['base_sha256'],'added':added,'removed':removed,
            'nets':sorted({r['net'] for r in added+removed})}


if __name__=='__main__':
    here=Path(__file__).resolve().parent;plan=json.loads((here/'plan.json').read_text())
    source=(ROOT/plan['source_replay']).read_bytes()
    if hashlib.sha256(source).hexdigest()!=plan['source_replay_sha256']:
        raise ValueError('reviewed source replay changed')
    board=ROOT/'boards/osc-core/osc-core.kicad_pcb'
    if hashlib.sha256(board.read_bytes()).hexdigest()!=plan['base_sha256']:
        raise ValueError('canonical core changed; reconcile successful copper first')
    result=build(plan,json.loads(source));out=here/'copper.json'
    out.write_text(json.dumps(result,sort_keys=True)+'\n')
    print(out.relative_to(ROOT),hashlib.sha256(out.read_bytes()).hexdigest(),
          len(result['added']),'added',len(result['removed']),'removed')
