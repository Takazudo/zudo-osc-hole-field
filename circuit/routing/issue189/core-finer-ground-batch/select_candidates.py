"""Select compatible saved ground paths; this is not a rebase or native acceptance."""
import hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
SOURCE='a0e3cff1ebc211564b8be10f6a993d50fb6d4372edde86a056ebc8dda3ea5932'

def main():
    names=sys.argv[1:] or ['result','next48','next48b','next48c','next48d','last']
    transactions=[];inputs=[];dump_hashes=set();router_hashes=set()
    for name in names:
        path=HERE.parent/'core1441-ground-finer'/f'{name}.json';data=json.loads(path.read_text())
        assert data['published_board_sha256']==SOURCE
        dump_hashes.add(data['input_native_dump_sha256']);router_hashes.add(data['router_sha256'])
        inputs.append({'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'transactions':len(data['transactions'])})
        transactions.extend(t for t in data['transactions'] if t['proposal']['copper'])
    assert len(dump_hashes)==len(router_hashes)==1
    selected=[];rejected=[];vias=[];rows=[];ids=set();groups=set()
    for t in sorted(transactions,key=lambda t:(len(t['proposal']['copper']),t['pads'])):
        group=tuple(sorted(t['pads']));assert group not in groups;groups.add(group)
        proposal=t['proposal'];assert proposal['board_sha256']==SOURCE and not proposal['removed_uuids']
        copper=proposal['copper'];assert all(r['net']=='AGND' for r in copper)
        assert all(r['width_nm']==300000 if r['kind']=='segment' else r['kind']=='via' and r['diameter_nm']==600000 and r['drill_nm']==300000 for r in copper)
        assert len({r['uuid'] for r in copper})==len(copper) and not ids.intersection(r['uuid'] for r in copper)
        newvias=[r for r in copper if r['kind']=='via']
        distances=[math.dist(a['at_nm'],b['at_nm'])/1e6 for a in newvias for b in vias]
        distances.extend(math.dist(a['at_nm'],b['at_nm'])/1e6 for i,a in enumerate(newvias) for b in newvias[:i])
        minimum=min(distances,default=None)
        if minimum is not None and minimum<.85:
            rejected.append({'pads':t['pads'],'reason':'new via centers below conservative0.85mm pair spacing','minimum_mm':minimum});continue
        selected.append({'pads':t['pads'],'objects':len(copper),'uuids':[r['uuid'] for r in copper]});rows.extend(copper);vias.extend(newvias);ids.update(r['uuid'] for r in copper)
    output=HERE/'proposal-original.json';output.write_text(json.dumps({'board_sha256':SOURCE,'removed_uuids':[],'copper':rows},indent=2)+'\n')
    (HERE/'selection.json').write_text(json.dumps({'status':'SAVED ORIGINAL INPUT ONLY; WAIT FOR CORE37936741388; NO REBASE OR NATIVE VALIDATION','source_sha256':SOURCE,'input_files':inputs,'input_dump_sha256':next(iter(dump_hashes)),'router_sha256':next(iter(router_hashes)),'selected':selected,'excluded':rejected,'objects':len(rows),'vias':len(vias),'proposal_sha256':hashlib.sha256(output.read_bytes()).hexdigest()},indent=2)+'\n')
    print('Selected',len(selected),'groups',len(rows),'objects',len(vias),'vias; native NOT RUN, no rebase')
if __name__=='__main__':main()
