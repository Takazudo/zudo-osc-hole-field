#!/usr/bin/env python3
"""One read-only native demonstration of the mandatory complete-warning gate on the core.

Input is the isolated, refilled copy recorded by current_state.py (never the adopted
board itself). The candidate adds exactly one AGND stitch via (0.6/0.3 mm, the
agnd-stitch stage dimensions) at the centre of one SMD pad of a stranded AGND
island, so the open-edge prerequisite can pass and the capped-report path runs
native audits end to end. Nothing is promoted or written under boards/; the
receipt records every hash, the via and the gate verdict. Not routing progress.
"""
from __future__ import annotations
import argparse,hashlib,json,math,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import scripts.pcbgen.route_jack_grid as driver
from scripts.pcbgen.uuid_tools import stable_uuid

BOARD='osc-core'
VIA_DIAMETER_NM=600_000;VIA_DRILL_NM=300_000
# Copper of another net closer than this to the via centre (beyond its own half width) disqualifies a pad.
KEEP_CLEAR_NM=VIA_DIAMETER_NM//2+250_000


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def seg_distance(p,a,b):
    ax,ay=a;bx,by=b;dx,dy=bx-ax,by-ay;n=dx*dx+dy*dy or 1
    u=max(0,min(1,((p[0]-ax)*dx+(p[1]-ay)*dy)/n));return math.hypot(ax+u*dx-p[0],ay+u*dy-p[1])


def inside(poly,xy):
    x,y=xy;hit=False
    for (x1,y1),(x2,y2) in zip(poly,poly[1:]+poly[:1]):
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:hit=not hit
    return hit


def poly_distance(poly,xy):
    """Distance from xy to a pad polygon; zero inside it."""
    if inside(poly,xy):return 0.0
    return min(seg_distance(xy,a,b) for a,b in zip(poly,poly[1:]+poly[:1]))


def candidates(dump):
    """Deterministic SMD AGND pads of non-main AGND islands whose centre is clear of foreign copper and holes."""
    groups=dump['islands'].get('AGND',[])
    if len(groups)<2:return []
    main=max(groups,key=len);pads={p['uuid']:p for p in dump['pads']};out=[]
    for group in sorted((g for g in groups if g is not main),key=lambda g:sorted(g)):
        for uid in sorted(group):
            p=pads.get(uid)
            if not p or p['drill'] or len(p['layers'])!=1:continue
            xy=p['xy']
            # A through via meets every copper layer, so any rule area containing the pad excludes it.
            if any(k['poly'] and inside(k['poly'],xy) for k in dump.get('keepouts',[])):continue
            if any(t['net']!='AGND' and seg_distance(xy,t['a'],t['b'])<KEEP_CLEAR_NM+t['width']/2 for t in dump['tracks']):continue
            if any(v['net']!='AGND' and math.dist(xy,v['xy'])<KEEP_CLEAR_NM+v['diameter']/2 for v in dump['vias']):continue
            if any(q['net']!='AGND' and q['drill'] and math.dist(xy,q['xy'])<KEEP_CLEAR_NM+q['drill'] for q in dump['pads']):continue
            # A through via meets every layer, so any foreign pad outline on either face must clear it too.
            if any(q['net']!='AGND' and q['poly'] and poly_distance(q['poly'],xy)<KEEP_CLEAR_NM for q in dump['pads']):continue
            row={'kind':'via','uuid':stable_uuid(BOARD,'osc1-gate-demo',uid),'net':'AGND','at_nm':[int(xy[0]),int(xy[1])],
                 'diameter_nm':VIA_DIAMETER_NM,'drill_nm':VIA_DRILL_NM,'layers':['F.Cu','B.Cu'],'locked':False}
            link={'net':'AGND','copper_uuids':[row['uuid']]}
            if driver.hole_spacing_culprits([row],[link],dump):continue
            out.append((p,row))
    return out


def main():
    a=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument('--source-workspace',type=Path,default=ROOT/'.circuit-cache'/f'{BOARD}-grid-current-state')
    a.add_argument('--receipt',type=Path,default=ROOT/'circuit/routing/osc1-complete-gate-demo/receipt.json')
    a.add_argument('--max-attempts',type=int,default=2)
    args=a.parse_args();started=time.time()
    state=json.loads((ROOT/'boards'/BOARD/'reports/routing.json').read_text())
    src=args.source_workspace/f'{BOARD}.kicad_pcb'
    if sha(src)!=state['refilled_copy']['output_board_sha256']:raise ValueError('source workspace is not the recorded current-state copy')
    canonical=ROOT/'boards'/BOARD/f'{BOARD}.kicad_pcb';canonical_sha=sha(canonical)
    if canonical_sha!=state['source']['input_board_sha256']:raise ValueError('adopted board changed since the current-state record')
    before_dir=driver.workspace(BOARD,'osc1-gate-demo-before');before_board=before_dir/src.name
    for name in (src.name,'drc.json','dump.json'):shutil.copyfile(args.source_workspace/name,before_dir/name)
    before_drc=json.loads((before_dir/'drc.json').read_text());before=json.loads((before_dir/'dump.json').read_text())
    receipt={'schema':'osc1-complete-gate-demo-1','status':'RUNNING','promoted':False,'board':BOARD,
             'adopted_board_sha256':canonical_sha,'before_board_sha256':sha(before_board),
             'current_state_record':{'path':f'boards/{BOARD}/reports/routing.json','sha256':sha(ROOT/'boards'/BOARD/'reports/routing.json')},
             'before_capped_warning_types':driver.warning_capped(before_drc,before_drc),'attempts':[]}
    def save():
        args.receipt.parent.mkdir(parents=True,exist_ok=True);args.receipt.write_text(json.dumps(receipt,indent=1,sort_keys=True)+'\n')
    if args.receipt.is_file():
        prior=json.loads(args.receipt.read_text())
        receipt['prior_runs']=prior.pop('prior_runs',[])+[prior]
    save()
    tried={a['pad']['uuid'] for run in receipt.get('prior_runs',[]) for a in run.get('attempts',[])}
    for pad,row in [c for c in candidates(before) if c[0]['uuid'] not in tried][:args.max_attempts]:
        attempt={'pad':{k:pad[k] for k in ('uuid','ref','pad','layers','xy')},'via':row};receipt['attempts'].append(attempt)
        work=driver.workspace(BOARD,'osc1-gate-demo-candidate');candidate=work/src.name;proposal=work/'proposal.json'
        proposal.write_text(json.dumps({'board_sha256':sha(before_board),'removed_uuids':[],'copper':[row]})+'\n')
        driver.run('bash','scripts/kicad/run.sh','python3','scripts/pcbgen/grid_apply.py',driver.rel(before_board),driver.rel(proposal),'--output',driver.rel(candidate))
        after_drc,after=driver.check(candidate)
        errors=[v['type'] for v in after_drc['violations'] if v['severity']=='error']
        attempt.update(candidate_board_sha256=sha(candidate),open_edges_before=before['open_edges'],open_edges_after=after['open_edges'],
                       agnd_open_before=len(before['islands'].get('AGND',[None]))-1,agnd_open_after=len(after['islands'].get('AGND',[None]))-1,
                       drc_errors=errors,parity=len(after_drc['schematic_parity']),capped_warning_types=driver.warning_capped(before_drc,after_drc))
        save()
        if errors or after_drc['schematic_parity'] or after['open_edges']>=before['open_edges']:
            attempt['result']='candidate not usable for the demonstration (native errors, parity or no gain)';save();continue
        evidence=driver.workspace(BOARD,'osc1-gate-demo-audits')/'native-audits'
        t0=time.time()
        gate=driver.warning_complete_gate(before_board,candidate,before,after,before_drc,after_drc,evidence,zone_batch_size=16)
        gate=driver.enforce_warning_completeness(gate,before_drc,after_drc,sha(before_board),sha(candidate))
        attempt['audit_seconds']=round(time.time()-t0,1)
        attempt['gate']={k:v for k,v in gate.items() if k not in ('split_pad_groups',)}
        attempt['gate']['split_pad_groups']=len(gate['split_pad_groups'])
        receipt['status']='COMPLETE READ-ONLY DEMONSTRATION; NOT PROMOTED'
        break
    else:receipt['status']='NO USABLE CANDIDATE; gate demonstration NOT RUN'
    if sha(canonical)!=canonical_sha:raise RuntimeError('adopted board changed during the demonstration')
    receipt['elapsed_seconds']=round(time.time()-started,1);save()
    print(json.dumps({'status':receipt['status'],'attempts':len(receipt['attempts'])}))


if __name__=='__main__':main()
