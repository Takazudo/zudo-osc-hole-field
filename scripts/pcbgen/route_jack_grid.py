#!/usr/bin/env python3
"""Staged grid routing of a six-layer jack half (owner decision 2026-10-03, #38).

Host driver: KiCad steps run through scripts/kicad/run.sh and routing runs on
the host (numerical-requirements.txt). Starting from the synced, placed and
plane-prepared board, each stage dumps the current candidate, proposes copper
with grid_router.py, applies it to a disposable copy two directories below the
repository root, and keeps only links that pass native DRC with schematic
parity and zone refill. A stage is adopted only when native open edges fall.
The adopted board is copied over boards/<id>/<id>.kicad_pcb at the end; every
stage writes a receipt under boards/<id>/reports/grid-routing/. Draft only:
electrical and physical qualification remain NOT RUN.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows,negotiate
from scripts.pcbgen.uuid_tools import stable_uuid

PLANES={'+12V':'In4.Cu','-12V':'In3.Cu'}
FAILED=set()  # signal nets with an unroutable island in an earlier batch; retried by the escape stage
RRR_TRIED=set()  # nets already offered to a rip-up batch in this run
# In3 carries signals as well as the -12V fill (owner stack: four signal layers); In2 is preferred.
SIGNAL_LAYERS=['F.Cu','In2.Cu','In3.Cu','B.Cu']
LAYER_COST=[3.0,1.0,1.0,1.5,1.0,3.0]
RAILS=['+12V','-12V','+5V']
COMMON=dict(layers=SIGNAL_LAYERS)
# Each stage: router keyword arguments plus which nets it serves.
STAGES=[
    {'name':'terminal-arrays','terminal_arrays':True},
    {'name':'rail-fanout','nets':['+12V','-12V'],'planes':PLANES,'clearance':.25,'rail_width':.4},
    {'name':'rail-links','nets':RAILS,'clearance':.25,'rail_width':.4},
    {'name':'rail-escapes','nets':RAILS,'clearance':.25,'rail_width':.25,'res':.05,'window_mm':6},
    # Negotiated (PathFinder) routing of every signal net on a 0.05 mm grid; leftovers go to the batches below.
    {'name':'negotiate','negotiate':True,'res':.05,'iterations':16,'workers':4,'clearance':.2,'signal_width':.2,'signal_via_diameter':.6,'grow':{n:.05 for n in [*RAILS,'AGND']}},
    # Short local nets first.
    {'name':'signals-local','signals':True,'max_span_mm':8,'escape_halo_mm':.9,'clearance':.2,'signal_width':.2,'signal_via_diameter':.6,'grow':{n:.05 for n in [*RAILS,'AGND']}},
    # Then the remaining open signal nets, shortest first, in checked and promoted batches.
    *({'name':f'signals-{i:02d}','signals':True,'chunk':120,'escape_halo_mm':.9,'clearance':.2,'signal_width':.2,'signal_via_diameter':.6,'grow':{n:.05 for n in [*RAILS,'AGND']}} for i in range(1,13)),
    # Rip-up and reroute: probe each failed island with other signal copper as a cost,
    # rip the few nets in its way, route it, then reroute the ripped nets; all-or-nothing.
    *({'name':f'rrr-{i:02d}','signals':True,'chunk':80,'rrr_rounds':2,'clearance':.2,'signal_width':.2,'signal_via_diameter':.6,'grow':{n:.05 for n in [*RAILS,'AGND']}} for i in range(1,9)),
    {'name':'agnd-stitch-1','agnd_stitch':True},
    {'name':'signal-escapes','signals':True,'clearance':.2,'signal_width':.2,'signal_via_diameter':.6,'grow':{n:.05 for n in [*RAILS,'AGND']},'res':.05,'window_mm':6},
    *({'name':f'repair-{i:02d}','repair':True,'clearance':.2,'signal_width':.2,'signal_via_diameter':.6,'grow':{n:.05 for n in [*RAILS,'AGND']},'res':.05,'window_mm':8} for i in range(1,9)),
    {'name':'agnd-stitch-2','agnd_stitch':True},
]


def run(*args):
    done=subprocess.run(args,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if done.returncode:print(done.stdout[-3000:]);raise RuntimeError(f'{args[:4]} failed ({done.returncode})')
    return done.stdout


def rel(p):return str(Path(p).resolve().relative_to(ROOT))


def workspace(board_id,name):
    """Candidate folder two levels below the root so ${KIPRJMOD}/../../ library paths resolve."""
    work=ROOT/'.circuit-cache'/f'{board_id}-grid-{name}'
    if work.exists():shutil.rmtree(work)
    work.mkdir(parents=True);src=ROOT/'boards'/board_id
    for name_ in ('fp-lib-table','sym-lib-table',f'{board_id}.kicad_pro',f'{board_id}.kicad_sch'):shutil.copyfile(src/name_,work/name_)
    shutil.copytree(src/'sheets',work/'sheets')
    return work


def check(board):
    drc=board.with_name('drc.json')
    run('bash','scripts/kicad/run.sh','kicad-cli','pcb','drc','--schematic-parity','--refill-zones','--save-board','--format','json','--severity-all','-o',rel(drc),rel(board))
    data=json.loads(drc.read_text())
    dump=board.with_name('dump.json')
    run('bash','scripts/kicad/run.sh','python3','scripts/pcbgen/grid_dump.py',rel(board),rel(dump))
    return data,json.loads(dump.read_text())


def terminal_array(dump,board_id,definition):
    """Source load-terminal transfer arrays: rows x columns of through vias inside each terminal land."""
    spec=definition['routing']['load_terminal_transfer'];pitch=spec['array_pitch_mm']*1e6
    rows=[];n=spec['array_rows'];m=spec['array_columns']
    for p in dump['pads']:
        if not p['ref'].startswith('TP') or p['net'] not in spec['nets']:continue
        for i in range(n):
            for j in range(m):
                x=int(round(p['xy'][0]+(j-(m-1)/2)*pitch));y=int(round(p['xy'][1]+(i-(n-1)/2)*pitch))
                rows.append({'kind':'via','uuid':stable_uuid(board_id,'terminal-array',f"{p['ref']}:{i}:{j}"),'net':p['net'],'at_nm':[x,y],
                             'diameter_nm':int(round(spec['via_diameter_mm']*1e6)),'drill_nm':int(round(spec['via_drill_mm']*1e6)),'layers':['F.Cu','B.Cu'],'locked':False})
    return rows,[{'net':'terminal arrays','copper_uuids':[r['uuid'] for r in rows]}]


def signal_chunk(dump,chunk,min_span_mm=None,max_span_mm=None,skip=()):
    """Open signal nets, shortest pad span first; chunk limits the count, spans filter in mm."""
    pads={p['uuid']:p['xy'] for p in dump['pads']}
    def span(net):
        pts=[pads[u] for g in dump['islands'][net] for u in g if u in pads]
        return (max(p[0] for p in pts)-min(p[0] for p in pts)+max(p[1] for p in pts)-min(p[1] for p in pts))/1e6 if pts else 0
    skip={*RAILS,'AGND',*skip}
    nets=sorted((n for n in dump['islands'] if n not in skip),key=lambda n:(span(n),n))
    if min_span_mm is not None:nets=[n for n in nets if span(n)>min_span_mm]
    if max_span_mm is not None:nets=[n for n in nets if span(n)<=max_span_mm]
    return nets[:chunk] if chunk else nets


def repair_batch(dump,radius_mm=1.2,limit=30):
    """Open signal nets plus the nearby foreign signal copper to cut; batches never share a net."""
    pads={p['uuid']:p for p in dump['pads']};used=set();targets=[];cut=set()
    r2=(radius_mm*1e6)**2
    def near(x,y,t):
        ax,ay=t['a'];bx,by=t['b'];dx,dy=bx-ax,by-ay;length=dx*dx+dy*dy or 1
        u=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/length));return (ax+u*dx-x)**2+(ay+u*dy-y)**2<=r2
    for net in signal_chunk(dump,None):
        groups=dump['islands'][net];main=max(range(len(groups)),key=lambda i:len(groups[i]))
        pts=[pads[u]['xy'] for i,g in enumerate(groups) if i!=main for u in g if u in pads]
        hits={t['uuid']:t['net'] for t in dump['tracks'] if t['net'] not in (*RAILS,'AGND',net) and any(near(x,y,t) for x,y in pts)}
        hits.update({v['uuid']:v['net'] for v in dump['vias'] if v['net'] not in (*RAILS,'AGND',net)
                     and any((v['xy'][0]-x)**2+(v['xy'][1]-y)**2<=r2 for x,y in pts)})
        nets=set(hits.values())
        if net in used or nets&used or net in {n for n in nets}:continue
        targets.append(net);cut|=set(hits);used|=nets|{net}
        if len(targets)>=limit:break
    return targets,cut


def stage(board_id,current,spec,definition,log):
    original=current
    dump=json.loads((current.with_name('dump.json')).read_text())
    if spec.get('terminal_arrays'):
        rows,links=terminal_array(dump,board_id,definition);removed=[]
    elif spec.get('repair'):
        # Phase A: cut foreign signal copper beside the failed pins; native islands then
        # describe exactly what each cut net must reconnect.
        targets,cut=repair_batch(dump)
        if not targets:return None,None
        work=workspace(board_id,spec['name']+'-cut');cut_board=work/f'{board_id}.kicad_pcb';proposal=work/'proposal.json'
        proposal.write_text(json.dumps({'board_sha256':hashlib.sha256(current.read_bytes()).hexdigest(),'removed_uuids':sorted(cut),'copper':[]})+'\n')
        run('bash','scripts/kicad/run.sh','python3','scripts/pcbgen/grid_apply.py',rel(current),rel(proposal),'--output',rel(cut_board))
        _,dump=check(cut_board)
        floating=[u for n,groups in dump['islands'].items() for g in groups if not any(x in {p['uuid'] for p in dump['pads']} for x in g) for u in g]
        if floating:
            # Pad-less fragments are dead copper: drop them instead of reconnecting them.
            proposal.write_text(json.dumps({'board_sha256':hashlib.sha256(current.read_bytes()).hexdigest(),'removed_uuids':sorted(cut|set(floating)),'copper':[]})+'\n')
            run('bash','scripts/kicad/run.sh','python3','scripts/pcbgen/grid_apply.py',rel(current),rel(proposal),'--output',rel(cut_board))
            _,dump=check(cut_board);cut|=set(floating)
        cut_nets=sorted({n for n in dump['islands'] if n not in (*RAILS,'AGND')}-set(targets))
        kwargs={k:v for k,v in spec.items() if k in ('clearance','signal_width','signal_via_diameter','grow','res','window_mm','escape_halo_mm')}
        results,removed=route(dump,targets+[n for n in cut_nets if n not in targets],allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,log=log,**kwargs)
        rows,links=copper_rows(results,board_id,'grid-'+spec['name'])
        current=cut_board;removed=[]
    elif spec.get('agnd_stitch'):
        # Every AGND island except the main network gets a via into the In1 ground plane.
        groups=dump['islands'].get('AGND',[])
        if len(groups)<2:return None,None
        main=max(range(len(groups)),key=lambda i:len(groups[i]))
        stitched={**dump,'islands':{'AGND':[g for i,g in enumerate(groups) if i!=main]}}
        results,removed=route(stitched,['AGND'],planes={'AGND':'In1.Cu'},allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,
                              log=log,clearance=.25,rail_width=.3,via_diameter=.6,res=.05)
        rows,links=copper_rows(results,board_id,'grid-'+spec['name'])
    elif spec.get('negotiate'):
        # PathFinder pass over every signal net: rip all signal copper and reroute together.
        nets=sorted({p['net'] for p in dump['pads'] if p['net'] and p['net'] not in (*RAILS,'AGND')})
        nets=[n for n in nets if sum(1 for p in dump['pads'] if p['net']==n)>1]
        results,removed=negotiate(dump,nets,res=spec['res'],layer_cost=LAYER_COST,clearance=spec['clearance'],width=spec['signal_width'],
                                  via_diameter=spec['signal_via_diameter'],allowed_layers=SIGNAL_LAYERS,grow=spec['grow'],
                                  iterations=spec['iterations'],present=2.0,present_growth=1.5,history=2.0,workers=spec['workers'],
                                  fill_guards={'-12V':'In3.Cu'},log=log)
        rows,links=copper_rows(results,board_id,'grid-'+spec['name'])
    elif spec.get('signal_fanout'):
        # Reserve a via escape for every pin of a long net before long routes can box it in.
        nets=signal_chunk(dump,None,min_span_mm=spec['signal_fanout'])
        kwargs={k:v for k,v in spec.items() if k in ('clearance','signal_width','signal_via_diameter','grow','res')}
        results,removed=route(dump,nets,planes={n:None for n in nets},allowed_layers=SIGNAL_LAYERS,rail_nets=RAILS,log=log,rail_width=spec['signal_width'],via_diameter=spec['signal_via_diameter'],**kwargs)
        rows,links=copper_rows(results,board_id,'grid-'+spec['name'])
    else:
        rrr=spec.get('rrr_rounds')
        nets=spec.get('nets') or signal_chunk(dump,spec.get('chunk'),max_span_mm=spec.get('max_span_mm'),
                                              skip=RRR_TRIED if rrr else (FAILED if spec.get('chunk') else ()))
        if rrr:RRR_TRIED.update(nets)
        kwargs={k:v for k,v in spec.items() if k in ('planes','clearance','rail_width','signal_width','signal_via_diameter','grow','res','window_mm','full_board','max_expansions','escape_halo_mm','rrr_rounds')}
        kwargs['fill_guards']={'-12V':'In3.Cu'}
        results,removed=route(dump,nets,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,log=log,**kwargs)
        rows,links=copper_rows(results,board_id,'grid-'+spec['name'])
        if spec.get('chunk') and not spec.get('rrr_rounds'):FAILED.update(r['net'] for r in results if not r['path'])
    dropped=[]
    for attempt in range(4):
        work=workspace(board_id,spec['name']);proposal=work/'proposal.json';candidate=work/f'{board_id}.kicad_pcb'
        proposal.write_text(json.dumps({'board_sha256':hashlib.sha256(current.read_bytes()).hexdigest(),'removed_uuids':removed,'copper':rows})+'\n')
        run('bash','scripts/kicad/run.sh','python3','scripts/pcbgen/grid_apply.py',rel(current),rel(proposal),'--output',rel(candidate))
        drc,after=check(candidate)
        bad={i.get('uuid') for v in drc['violations'] if v['severity']=='error' for i in v['items']}
        if drc['schematic_parity']:raise RuntimeError('schematic parity findings after '+spec['name'])
        base=json.loads(original.with_name('dump.json').read_text())['islands']
        split=[n for n in PLANES if len(after['islands'].get(n,[None]))>len(base.get(n,[None]))]
        if split and not bad:
            # Signals sharing a plane's layer must not cut the plane apart. Cut AGND
            # surface-pour islands are rejoined later by the agnd-stitch stage.
            plane_layers={PLANES[n] for n in split}
            bad={r['uuid'] for r in rows if r['kind']=='segment' and r['layer'] in plane_layers}
            log(f"{spec['name']}: {split} split; dropping links with copper on {sorted(plane_layers)}")
            if not bad:raise RuntimeError(f"{spec['name']}: {split} split without attributable copper")
        if not bad:break
        culprits=[l for l in links if bad & set(l['copper_uuids'])]
        if not culprits:raise RuntimeError(f"{spec['name']}: DRC errors not attributable to new copper")
        if removed:
            # A rerouted (ripped) net loses its whole new route and gets its old copper back.
            ripped_nets={i['net'] for k in ('tracks','vias') for i in dump[k] if i['uuid'] in set(removed)}
            back={l['net'] for l in culprits}&ripped_nets
            culprits+=[l for l in links if l['net'] in back and l not in culprits]
            removed=[u for u in removed if not any(i['uuid']==u and i['net'] in back for k in ('tracks','vias') for i in dump[k])]
        drop={u for l in culprits for u in l['copper_uuids']};dropped+=culprits
        rows=[r for r in rows if r['uuid'] not in drop];links=[l for l in links if l not in culprits]
        log(f"{spec['name']}: dropped {len(culprits)} links with DRC errors; retrying")
    else:raise RuntimeError(f"{spec['name']}: DRC errors persist")
    before=json.loads(original.with_name('dump.json').read_text())['open_edges']
    receipt={'stage':spec['name'],'status':'NATIVE CHECKED DRAFT STAGE','open_edges_before':before,'open_edges_after':after['open_edges'],
             'links_added':len(links),'links_dropped_for_drc':len(dropped),'copper_rows':len(rows),'ripped':len(removed),
             'drc_errors':0,'drc_warnings':sum(v['severity']=='warning' for v in drc['violations']),'parity':0,
             'open_by_net_after':{n:len(g)-1 for n,g in after['islands'].items()}}
    return candidate,receipt


def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0]);p.add_argument('board_id',choices=('osc-jack-left','osc-jack-right'))
    p.add_argument('--from-stage',default=STAGES[0]['name']);p.add_argument('--to-stage');p.add_argument('--promote',action='store_true');a=p.parse_args()
    board=ROOT/'boards'/a.board_id/f'{a.board_id}.kicad_pcb';definition=json.loads((ROOT/'design/boards'/f'{a.board_id}.json').read_text())
    if definition['layers']!=6:raise ValueError('six-layer jack definition required')
    reports=board.parent/'reports'/'grid-routing';reports.mkdir(parents=True,exist_ok=True)
    work=workspace(a.board_id,'start');current=work/board.name;shutil.copyfile(board,current);check(current)
    names=[s['name'] for s in STAGES]
    last=names.index(a.to_stage)+1 if a.to_stage else len(STAGES)
    for spec in STAGES[names.index(a.from_stage):last]:
        candidate,receipt=stage(a.board_id,current,spec,definition,lambda m:print(m,flush=True))
        if candidate is None:print(f"{spec['name']}: nothing to do",flush=True);continue
        receipt['adopted']=receipt['open_edges_after']<receipt['open_edges_before']
        (reports/f"{spec['name']}.json").write_text(json.dumps(receipt,indent=1,sort_keys=True)+'\n')
        print(f"{spec['name']}: {receipt['open_edges_before']} -> {receipt['open_edges_after']} open edges",flush=True)
        if receipt['open_edges_after']<receipt['open_edges_before']:
            current=candidate
            # Promote every adopted stage so a later interruption keeps checked progress.
            if a.promote:shutil.copyfile(current,board);print('promoted',rel(board),flush=True)
    print('final candidate',rel(current))


if __name__=='__main__':main()
