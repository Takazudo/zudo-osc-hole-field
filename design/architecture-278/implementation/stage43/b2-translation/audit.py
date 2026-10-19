"""Source identity and native partition accounting for an explicitly rejected trial."""
from pathlib import Path
from collections import Counter
import json,sys
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from identity_guard import inventory,compare,digest,copper_contract,top_level_spans
from acceptance import connectivity_gate

def contract(r):
    if r['kind']=='segment':shape=(tuple(r['start_nm']),tuple(r['end_nm']),(r['width_nm'],),r['layer'])
    elif r['kind']=='via':shape=(tuple(r['at_nm']),(r['diameter_nm'],),(r['drill_nm'],),tuple(r['layers']))
    else:raise ValueError('unsupported copper')
    return r['kind'],r['uuid'],shape,r['net']

def audit(directory):
    baseline=ROOT/'.circuit-cache/stage42-full-b1-fresh/osc-jack-left.kicad_pcb'
    candidate=directory/baseline.name
    raw0,raw1=baseline.read_text(),candidate.read_text()
    receipt=json.loads((directory/'receipt.json').read_text())
    if digest(raw0)!=receipt['baseline_sha256'] or digest(raw0)!='975cd15d5ba69b9695e8d32a575a289306a27f1ea17d6b5f7a5819071dc5505b':raise ValueError('baseline binding')
    before,after=inventory(raw0),inventory(raw1)
    rows=json.loads((directory/'proposal.json').read_text())['copper'];ids={r['uuid'] for r in rows}
    new=Counter({k:n for k,n in after['native_contract'].items() if k[1] in ids})
    if new!=Counter(contract(r) for r in rows):raise ValueError('new copper differs from proposal')
    additions=[k for k,n in after['copper'].items() if k[1] in ids for _ in range(n)]
    identity=compare(before,after,receipt['retired_hashes'],additions)
    identity['prepared_footprints_equal']=after['footprints']==receipt['prepared_footprint_hashes']
    identity['foreign_footprints_equal']=all(after['footprints'][r]==h for r,h in before['footprints'].items() if r not in receipt['moved'])
    identity['accepted']=identity['accepted'] and identity['prepared_footprints_equal'] and identity['foreign_footprints_equal']
    for suffix in ('.kicad_pro','.kicad_sch','.kicad_dru'):
        if candidate.with_suffix(suffix).read_bytes()!=baseline.with_suffix(suffix).read_bytes():raise ValueError('project/schematic/rules changed')
    output={'baseline_sha256':digest(raw0),'candidate_sha256':digest(raw1),'identity':identity}
    snapshot=directory/'connectivity.json'
    if snapshot.exists():
        old=json.loads(baseline.with_name('connectivity-passfresh.json').read_text());new=json.loads(snapshot.read_text())
        if old['board_sha256']!=digest(raw0) or new['board_sha256']!=digest(raw1):raise ValueError('snapshot binding')
        retired=[]
        for a,z in top_level_spans(raw0):
            if digest(raw0[a:z]) in receipt['retired_hashes']:retired.append(json.dumps(copper_contract(raw0[a:z])[:-1],separators=(',',':')))
        added=[json.dumps(contract(r)[:-1],separators=(',',':')) for r in rows]
        private={r['net'] for r in rows}-{'AGND','+12V','-12V','+5V'}
        output['connectivity']=connectivity_gate(old,new,retired,added,private)
        output['native_open_edges']=new['native_open_edges']
    if (directory/'drc-first.json').exists():
        drc=json.loads((directory/'drc-first.json').read_text())
        output['drc_counts']={k:len(v) for k,v in drc.items() if isinstance(v,list)}
        output['drc_violation_types']=dict(Counter((r['severity']+':'+r['type']) for r in drc['violations']))
    (directory/'audit.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print(json.dumps(output,indent=2,sort_keys=True))
    if not identity['accepted']:raise SystemExit('Identity failure: trial cannot support a retained-layout comparison')
if __name__=='__main__':audit(Path(sys.argv[1]))
