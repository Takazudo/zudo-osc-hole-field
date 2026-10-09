"""Rebase saved short outer-layer signal paths only after the sole core writer has finished.

Pass the reviewed exact accepted board hash. Preserve every full copper block,
including duplicate UUIDs, and reject unknown changes or proposal conflicts.
This does not run or replace the mandatory native gate.
"""
import argparse,hashlib,json,subprocess,sys,math,re
from decimal import Decimal
from pathlib import Path
from shapely.geometry import Point,LineString
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.route_shards import copper_block_groups,delta

def gap(a,b):
    if a['net']==b['net'] or (a['kind']==b['kind']=='segment' and a['layer']!=b['layer']):return float('inf')
    def shape(r):
        if r['kind']=='via':return Point(r['at_nm']),r['diameter_nm']/2
        assert r['kind']=='segment';return LineString([r['start_nm'],r['end_nm']]),r['width_nm']/2
    x,r=shape(a);y,s=shape(b);return (x.distance(y)-r-s)/1e6

def require_known_geometry(added,known):
    """UUID equality alone cannot prove the accepted additions match the saved geometry."""
    expected={row['uuid']:row for row in known}
    for item in added:
        row=expected[item['uuid']];block=item['block']
        assert item['net']==row['net'],'accepted new net changed'
        def nm(tag):
            match=re.search(r'\('+tag+r'\s+([^()]+)\)',block)
            assert match,'missing native geometry '+tag
            return [int(Decimal(value)*1000000) for value in match[1].split()]
        if row['kind']=='segment':
            assert block.startswith('(segment')
            assert nm('start')==row['start_nm'] and nm('end')==row['end_nm']
            assert nm('width')==[row['width_nm']] and item['layer']==row['layer']
        else:
            assert block.startswith('(via')
            assert nm('at')==row['at_nm'] and nm('size')==[row['diameter_nm']] and nm('drill')==[row['drill_nm']]
            match=re.search(r'\(layers\s+([^()]+)\)',block)
            assert match and re.findall(r'"([^"]+)"',match[1])==row['layers']

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--accepted-sha256',required=True);args=parser.parse_args()
    board='boards/osc-core/osc-core.kicad_pcb'
    source_commit='4580536e8edd0bb9216c02d6b01aec00189da20e'
    old=subprocess.check_output(['git','show',f'{source_commit}:{board}'],cwd=ROOT).decode()
    current=(ROOT/board).read_text();sha=hashlib.sha256(current.encode()).hexdigest()
    assert sha==args.accepted_sha256,'reviewed accepted core hash differs'
    source=json.loads((HERE/'proposal-original.json').read_text())
    assert hashlib.sha256(old.encode()).hexdigest()==source['board_sha256']
    before,after=copper_block_groups(old),copper_block_groups(current)
    assert all(rows==after.get(u) for u,rows in before.items()),'prior copper changed'
    change=delta(old,current);assert not change['removed']
    known=json.loads((HERE.parent/'core-finer-ground-batch/proposal.json').read_text())['copper']
    actual_new={r['uuid'] for r in change['added']}
    assert not actual_new or actual_new=={r['uuid'] for r in known},'unreviewed core changes: inspect and update explicitly'
    require_known_geometry(change['added'],known)
    fixed=known if actual_new else []
    rows=source['copper'];selection=json.loads((HERE/'selection.json').read_text());assert not source['removed_uuids'] and len(rows)==selection['objects'];assert hashlib.sha256((HERE/'proposal-original.json').read_bytes()).hexdigest()==selection['proposal_sha256']
    assert len(rows)==19 and len(selection['selected'])==11
    assert all(r['net'] not in ['AGND','+12V','-12V','+5V'] and r['kind']=='segment' and r['layer'] in ['F.Cu','B.Cu'] and r['width_nm'] in [150000,200000] for r in rows)
    vias=[r for r in rows if r['kind']=='via'];assert all(math.dist(a['at_nm'],b['at_nm'])/1e6>=.85 for i,a in enumerate(vias) for b in vias[:i])
    assert len({r['uuid'] for r in rows})==len(rows) and all(r['uuid'] not in after for r in rows)
    minimum=min(gap(a,b) for i,a in enumerate(rows) for b in rows[:i]);assert minimum>=.25
    fixed_gap=min((gap(a,b) for a in rows for b in fixed),default=None)
    assert fixed_gap is None or fixed_gap>=.25,'saved signal path conflicts with accepted new core copper'
    p=HERE/'proposal.json';p.write_text(json.dumps({**source,'board_sha256':sha},indent=2)+'\n')
    (HERE/'plan.json').write_text(json.dumps({'base_sha256':sha,'proposal_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':f"{len(selection['selected'])}short signal transactions,{len(rows)}outer segments,no vias/cuts. Full native gates mandatory."},indent=2)+'\n')
    (HERE/'rebase.json').write_text(json.dumps({'status':'REBASED; NATIVE NOT RUN','source_commit':source_commit,'source_board_sha256':source['board_sha256'],'accepted_board_sha256':sha,'retained_objects':sum(map(len,after.values())),'retained_new_objects':len(actual_new),'added_objects':len(rows),'removed_objects':0,'minimum_new_cross_net_gap_mm':minimum if math.isfinite(minimum) else None,'minimum_gap_to_accepted_new_copper_mm':fixed_gap},indent=2)+'\n')
    print('Rebased',len(rows),'signal objects; native NOT RUN')

if __name__=='__main__':main()
