"""Rebase saved signal paths only after the sole JR writer has finished.

Pass the reviewed exact accepted board hash. Preserve every full copper block,
including duplicate UUIDs, and reject unknown changes or proposal conflicts.
This does not run or replace the mandatory native gate.
"""
import argparse,hashlib,json,subprocess,sys,math
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

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--accepted-sha256',required=True);args=parser.parse_args()
    board='boards/osc-jack-right/osc-jack-right.kicad_pcb'
    source_commit='1686c77cefa7874a765fbf768adf071557ff469e'
    old=subprocess.check_output(['git','show',f'{source_commit}:{board}'],cwd=ROOT).decode()
    current=(ROOT/board).read_text();sha=hashlib.sha256(current.encode()).hexdigest()
    assert sha==args.accepted_sha256,'reviewed accepted JR hash differs'
    source=json.loads((HERE/'proposal-original.json').read_text())
    assert hashlib.sha256(old.encode()).hexdigest()==source['board_sha256']
    before,after=copper_block_groups(old),copper_block_groups(current)
    assert all(rows==after.get(u) for u,rows in before.items()),'prior copper changed'
    change=delta(old,current);assert not change['removed']
    known=json.loads((HERE.parent/'jr-d7504-via-avoid/proposal.json').read_text())['copper']
    actual_new={r['uuid'] for r in change['added']}
    assert not actual_new or actual_new=={r['uuid'] for r in known},'unreviewed JR changes: inspect and update explicitly'
    fixed=known if actual_new else []
    rows=source['copper'];assert not source['removed_uuids'] and len(rows)==233
    assert all(r['kind']=='via' or r['layer'] in ('F.Cu','In2.Cu','In3.Cu','B.Cu') for r in rows)
    assert len({r['uuid'] for r in rows})==len(rows) and all(r['uuid'] not in after for r in rows)
    minimum=min(gap(a,b) for i,a in enumerate(rows) for b in rows[:i]);assert minimum>=.25
    fixed_gap=min((gap(a,b) for a in rows for b in fixed),default=None)
    assert fixed_gap is None or fixed_gap>=.25,'saved signal path conflicts with accepted new JR copper'
    p=HERE/'proposal.json';p.write_text(json.dumps({**source,'board_sha256':sha},indent=2)+'\n')
    (HERE/'plan.json').write_text(json.dumps({'base_sha256':sha,'proposal_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'3signal transactions,233objects,zero removals. Full native gates mandatory.'},indent=2)+'\n')
    (HERE/'rebase.json').write_text(json.dumps({'status':'REBASED; NATIVE NOT RUN','source_commit':source_commit,'source_board_sha256':source['board_sha256'],'accepted_board_sha256':sha,'retained_objects':sum(map(len,after.values())),'retained_new_objects':len(actual_new),'added_objects':len(rows),'removed_objects':0,'minimum_new_cross_net_gap_mm':minimum if math.isfinite(minimum) else None,'minimum_gap_to_accepted_new_copper_mm':fixed_gap},indent=2)+'\n')
    print('Rebased233signal objects; native NOT RUN')

if __name__=='__main__':main()
