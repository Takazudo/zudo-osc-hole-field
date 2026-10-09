#!/usr/bin/env python3
"""Staged grid routing of a six-layer jack half (owner decision 2026-10-03, #38) or the core (#43).

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
import argparse,collections,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scripts.pcbgen.grid_router import route,copper_rows,negotiate
from scripts.pcbgen.uuid_tools import stable_uuid
from scripts.pcbgen.route_shards import area_plan,plan,region_key,region_nets,delta

PLANES={'+12V':'In4.Cu','-12V':'In3.Cu'}
FAILED=set()  # signal nets with an unroutable island in an earlier batch; retried by the escape stage
RRR_TRIED=set()  # nets already offered to a rip-up batch in the current round
# Rip-up rounds: once every open net has been offered, the next round re-offers them (earlier
# rounds changed the copper) with a larger rip-up budget; a round that adopts nothing ends them.
RRR_ROUND={'round':0,'adopted':False,'done':False}
REGIONS_TRIED=set()  # hotspot regions already renegotiated in this run (rounded box corners)
# With --max-minutes the run deadline replaces each negotiated stage's local slice budget (budget_s).
# Time a negotiated stage keeps after its last iteration for the fill guard, apply, native DRC and push.
FINALIZE_MARGIN_S=20*60
RUN={'deadline':None,'workers':None,'res':None,'iterations':None,'shard':None}  # --max-minutes/--workers/--res/--iterations/--shard overrides (CI routing)
# Rip-up probes on the jack halves need 5-20 victim nets (JL CI run 37580806638: all 109 skipped at 4),
# so later rounds rip more; every round runs even when the previous one adopted nothing.
RRR_BUDGETS=[{'rrr_max_rip':4,'window_mm':12.0},{'rrr_max_rip':8,'window_mm':16.0},{'rrr_max_rip':12,'window_mm':20.0},{'rrr_max_rip':20,'window_mm':24.0}]
# In3 carries signals as well as the -12V fill (owner stack: four signal layers); In2 is preferred.
SIGNAL_LAYERS=['F.Cu','In2.Cu','In3.Cu','B.Cu']
LAYER_COST=[3.0,1.0,1.0,1.5,1.0,3.0]
RAILS=['+12V','-12V','+5V']
# The core is twice a jack half's area; a 0.05 mm six-layer negotiation raster would not fit in memory.
NEGOTIATE_RES={'osc-core':0.075}
# Fewer forked workers on the core keep its shared rasters within this machine's memory.
# Jack jobs run beside the core (heavy-guard --slots 2): each worker holds ~0.4 GB private.
NEGOTIATE_WORKERS={'osc-core':2,'osc-jack-left':2,'osc-jack-right':2}
# Core iterations plateau near 1000 conflicts by about 25; stop there and hand the rest to rip-up.
NEGOTIATE_ITERATIONS={'osc-core':30}
COMMON=dict(layers=SIGNAL_LAYERS)
# Each stage: router keyword arguments plus which nets it serves.
STAGES=[
    {'name':'terminal-arrays','terminal_arrays':True},
    {'name':'rail-fanout','nets':['+12V','-12V'],'planes':PLANES,'clearance':.25,'rail_width':.4},
    {'name':'rail-links','nets':RAILS,'clearance':.25,'rail_width':.4},
    {'name':'rail-escapes','nets':RAILS,'clearance':.25,'rail_width':.25,'res':.05,'window_mm':6},
    # Negotiated (PathFinder) routing of every signal net on a 0.05 mm grid; leftovers go to the batches below.
    # A run stops after budget_s and saves its state, so each heavy-guard run stays short.
    {'name':'negotiate','negotiate':True,'res':.05,'iterations':60,'workers':4,'budget_s':5400,'clearance':.2,'signal_width':.2,'signal_via_diameter':.6,'grow':{n:.05 for n in [*RAILS,'AGND']}},
    # Second negotiated pass over what is still open, after the sequential stages.
    {'name':'negotiate-open','negotiate':True,'open_only':True,'halo_mm':1.5,'res':.05,'iterations':40,'workers':4,'budget_s':5400,'clearance':.2,'signal_width':.2,'signal_via_diameter':.6,'grow':{n:.05 for n in [*RAILS,'AGND']}},
    # Hotspot regions: rip all signal copper in a few clusters of stranded pins and renegotiate it.
    *({'name':f'region-{i:02d}','negotiate':True,'regions':True,'eps_mm':8,'margin_mm':3,'regions_per_stage':8,'res':.05,'iterations':40,'workers':4,'budget_s':5400,'clearance':.2,'signal_width':.2,'signal_via_diameter':.6,'grow':{n:.05 for n in [*RAILS,'AGND']}} for i in range(1,9)),
    # Short local nets first.
    {'name':'signals-local','signals':True,'max_span_mm':8,'escape_halo_mm':.9,'clearance':.2,'signal_width':.2,'signal_via_diameter':.6,'grow':{n:.05 for n in [*RAILS,'AGND']}},
    # Then the remaining open signal nets, shortest first, in checked and promoted batches
    # (the core needs more batches than a jack half; empty batches are skipped).
    *({'name':f'signals-{i:02d}','signals':True,'chunk':120,'escape_halo_mm':.9,'clearance':.2,'signal_width':.2,'signal_via_diameter':.6,'grow':{n:.05 for n in [*RAILS,'AGND']}} for i in range(1,41)),
    # Rip-up and reroute: probe each failed island with other signal copper as a cost,
    # rip the few nets in its way, route it, then reroute the ripped nets; all-or-nothing.
    *({'name':f'rrr-{i:02d}','signals':True,'chunk':80,'rrr_rounds':2,'clearance':.2,'signal_width':.2,'signal_via_diameter':.6,'grow':{n:.05 for n in [*RAILS,'AGND']}} for i in range(1,25)),  # room for three re-offer rounds; unused batches are skipped
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
    # Custom DRC rules (neck-down areas) travel with the candidate so native checks apply them.
    if (src/f'{board_id}.kicad_dru').exists():shutil.copyfile(src/f'{board_id}.kicad_dru',work/f'{board_id}.kicad_dru')
    shutil.copytree(src/'sheets',work/'sheets')
    return work


class FillUnsettled(RuntimeError):
    """Zone refills kept changing the island counts, so the board has no settled open-edge count."""


def check(board,max_refills=6,stable=3):
    """Native DRC with zone refill, repeated until island memberships hold for `stable` passes.

    A single refill of a freshly edited board can leave the pours in a state the next
    refill changes (AGND islands 22 -> 28 on a neck-down candidate). Two equal passes were
    not enough either: a jack-right stage settled at 169 in-run, and a fresh check of the
    saved board gave 175, so adoption needs three equal passes.
    """
    drc=board.with_name('drc.json');dump=board.with_name('dump.json');seen=[]
    for _ in range(max_refills):
        run('bash','scripts/kicad/run.sh','kicad-cli','pcb','drc','--schematic-parity','--refill-zones','--save-board','--format','json','--severity-all','-o',rel(drc),rel(board))
        run('bash','scripts/kicad/run.sh','python3','scripts/pcbgen/grid_dump.py',rel(board),rel(dump))
        state=json.loads(dump.read_text());seen.append(connectivity_signature(state))
        print(f"  refill pass {len(seen)}: {state['open_edges']} open edges",flush=True)
        if len(seen)>=stable and all(x==seen[-1] for x in seen[-stable:]):break
    else:raise FillUnsettled(f"{rel(board)}: island memberships still changing after {max_refills} refills")
    return json.loads(drc.read_text()),state


def connectivity_signature(dump):
    """Compare all native islands, including padless copper, independent of enumeration."""
    return dump['open_edges'],{n:sorted(sorted(g) for g in groups) for n,groups in dump['islands'].items()}


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


def signal_chunk(dump,chunk,min_span_mm=None,max_span_mm=None,skip=(),only=None):
    """Open signal nets, shortest pad span first; chunk limits the count, spans filter in mm, only keeps a shard's nets."""
    pads={p['uuid']:p['xy'] for p in dump['pads']}
    def span(net):
        pts=[pads[u] for g in dump['islands'][net] for u in g if u in pads]
        return (max(p[0] for p in pts)-min(p[0] for p in pts)+max(p[1] for p in pts)-min(p[1] for p in pts))/1e6 if pts else 0
    skip={*RAILS,'AGND',*skip}
    nets=sorted((n for n in dump['islands'] if n not in skip and (only is None or n in only)),key=lambda n:(span(n),n))
    if min_span_mm is not None:nets=[n for n in nets if span(n)>min_span_mm]
    if max_span_mm is not None:nets=[n for n in nets if span(n)<=max_span_mm]
    return nets[:chunk] if chunk else nets


def repair_batch(dump,radius_mm=1.2,limit=30,only=None):
    """Open signal nets plus the nearby foreign signal copper to cut; batches never share a net."""
    pads={p['uuid']:p for p in dump['pads']};used=set();targets=[];cut=set()
    r2=(radius_mm*1e6)**2
    def near(x,y,t):
        ax,ay=t['a'];bx,by=t['b'];dx,dy=bx-ax,by-ay;length=dx*dx+dy*dy or 1
        u=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/length));return (ax+u*dx-x)**2+(ay+u*dy-y)**2<=r2
    for net in signal_chunk(dump,None,only=only):
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


def repair_nets(dump,targets,cut):
    """Only the selected targets and nets whose local copper was actually cut."""
    objects={i['uuid']:i for kind in ('tracks','vias') for i in dump[kind]}
    if not set(cut)<=objects.keys():raise ValueError('repair cut contains unknown source copper')
    affected={objects[u]['net'] for u in cut}
    if affected&{*RAILS,'AGND'}:raise ValueError('local signal repair cannot cut supply/ground copper')
    return list(targets)+sorted(affected-set(targets))


def repair_selection(dump,spec):
    """Use a source-pinned corridor cut, or the existing terminal-local selection."""
    if 'repair_source_uuids' not in spec:
        return repair_batch(dump,radius_mm=spec.get('repair_radius_mm',1.2),only=spec.get('repair_targets'))
    targets=list(spec.get('repair_targets',[]));cut=set(spec['repair_source_uuids'])
    if not targets or any(n not in dump['islands'] or n in (*RAILS,'AGND') for n in targets):
        raise ValueError('explicit repair requires existing open signal targets')
    repair_nets(dump,targets,cut)  # Reject missing objects and supply/ground cuts before native application.
    return targets,cut


class StageRejected(RuntimeError):
    """A stage whose candidate keeps DRC errors that cannot be dropped: keep the previous board."""


def run_stage(board_id,current,spec,definition,log):
    """stage(), with an unrepairable candidate turned into a rejected receipt instead of an abort."""
    try:return stage(board_id,current,spec,definition,log)
    except (StageRejected,FillUnsettled) as e:
        before=json.loads(current.with_name('dump.json').read_text())['open_edges']
        log(f"{spec['name']}: rejected ({e}); keeping the previous board")
        return None,{'stage':spec['name'],'status':'REJECTED: '+str(e),'open_edges_before':before,'open_edges_after':before,'rejected':True}


def stitched(board_id,current,candidate,receipt,spec,definition,log):
    """Judge a signal candidate after AGND stitching when it closed signal edges but cut AGND pours.

    New signal copper at the AGND clearance splits surface pours, so a stage can close signal
    edges and still not lower the total; stitching the cut islands to the In1 plane decides it.
    Shards skip this: AGND is not a net a shard owns.
    """
    if RUN['shard'] or spec.get('agnd_stitch'):return candidate,receipt
    before=json.loads(current.with_name('dump.json').read_text())
    signal_before=before['open_edges']-(len(before['islands'].get('AGND',[None]))-1)
    signal_after=receipt['open_edges_after']-receipt['open_by_net_after'].get('AGND',0)
    if signal_after>=signal_before:return candidate,receipt
    joined,stitch=run_stage(board_id,candidate,{'name':spec['name']+'-stitch','agnd_stitch':True},definition,log)
    if joined is None or stitch['open_edges_after']>=receipt['open_edges_before']:return candidate,receipt
    log(f"{spec['name']}: signal edges {signal_before} -> {signal_after}; with AGND stitching {receipt['open_edges_before']} -> {stitch['open_edges_after']} open edges")
    return joined,{**receipt,'open_edges_after':stitch['open_edges_after'],'open_by_net_after':stitch['open_by_net_after'],
                   'agnd_stitch':{k:stitch[k] for k in ('links_added','links_dropped_for_drc','copper_rows')}}


def neck_kwargs(board_id):
    """Neck-down width/clearance for signal routing on boards listed in neckdown-areas.json."""
    path=ROOT/'design/partition/neckdown-areas.json'
    if not path.exists():return {}
    src=json.loads(path.read_text())
    if board_id not in src['boards']:return {}
    return {'neck_width':src['rule']['track_width_mm'],'neck_clearance':src['rule']['clearance_mm']}


def hotspot_regions(dump,eps_mm):
    """Clusters of stranded signal pins (every island but each net's largest), largest first.

    Single-link clustering at eps_mm; returns [(lo_xy_nm, hi_xy_nm, pad_count)].
    """
    pads={p['uuid']:p for p in dump['pads']};pts=[]
    for net,groups in sorted(dump['islands'].items()):
        if len(groups)<2 or net in (*RAILS,'AGND'):continue
        largest=max(groups,key=lambda g:sum(u in pads for u in g))
        pts+=[pads[u]['xy'] for g in groups if g is not largest for u in g if u in pads]
    if not pts:return []
    xy=np.array(pts,float);pairs=cKDTree(xy).query_pairs(eps_mm*1e6,output_type='ndarray')
    graph=coo_matrix((np.ones(len(pairs)),(pairs[:,0],pairs[:,1])),shape=(len(xy),len(xy)))
    _,label=connected_components(graph,directed=False)
    regions=[(xy[label==c].min(0),xy[label==c].max(0),int((label==c).sum())) for c in range(label.max()+1)]
    return sorted(regions,key=lambda r:(-r[2],tuple(r[0])))


def stage(board_id,current,spec,definition,log):
    original=current
    repair_details=None
    dump=json.loads((current.with_name('dump.json')).read_text())
    if spec.get('terminal_arrays'):
        if 'load_terminal_transfer' not in definition['routing']:return None,None
        rows,links=terminal_array(dump,board_id,definition);removed=[]
    elif spec.get('repair'):
        # Phase A: cut foreign signal copper beside the failed pins; native islands then
        # describe exactly what each cut net must reconnect.
        targets,cut=repair_selection(dump,spec)
        if not targets:return None,None
        nets_to_repair=repair_nets(dump,targets,cut)
        work=workspace(board_id,spec['name']+'-cut');cut_board=work/f'{board_id}.kicad_pcb';proposal=work/'proposal.json'
        proposal.write_text(json.dumps({'board_sha256':hashlib.sha256(current.read_bytes()).hexdigest(),'removed_uuids':sorted(cut),'copper':[]})+'\n')
        run('bash','scripts/kicad/run.sh','python3','scripts/pcbgen/grid_apply.py',rel(current),rel(proposal),'--output',rel(cut_board))
        _,dump=check(cut_board)
        repair_details={'targets':targets,'affected_nets':nets_to_repair,'removed_source_uuids':sorted(cut),
                        'cut_native_open_edges':dump['open_edges'],'routing_diagnostics':[]}
        # Keep padless fragments and native component identities: they remain
        # boundary anchors/obligations, rather than disappearing from the metric.
        kwargs={k:v for k,v in spec.items() if k in ('clearance','signal_width','signal_via_diameter','grow','res','window_mm','escape_halo_mm')}
        results,removed=route(dump,nets_to_repair,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,
                              fill_guards={'-12V':'In3.Cu'},diagnostics=repair_details['routing_diagnostics'],log=log,**kwargs,**neck_kwargs(board_id))
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
        # PathFinder pass: rip the chosen signal nets and reroute them together.
        nets=sorted({p['net'] for p in dump['pads'] if p['net'] and p['net'] not in (*RAILS,'AGND')})
        nets=[n for n in nets if sum(1 for p in dump['pads'] if p['net']==n)>1]
        if spec.get('regions'):
            # Hotspot pass: every signal net with copper or a stranded pin in a few stuck regions.
            # A shard (--shard) takes its regions from the base-board plan and renegotiates only the nets it owns.
            pool=RUN['shard']['regions'] if RUN['shard'] else hotspot_regions(dump,spec['eps_mm'])
            regions=[r for r in pool if region_key(r) not in REGIONS_TRIED][:spec['regions_per_stage']]
            if not regions:return None,None
            REGIONS_TRIED.update(region_key(r) for r in regions)
            chosen=set().union(*(region_nets(dump,nets,r,spec['margin_mm']) for r in regions))
            if RUN['shard']:chosen&=set(RUN['shard']['nets'])
            nets=sorted(chosen);log(f"{spec['name']}: {len(regions)} regions ({[r[2] for r in regions]} stranded pins), {len(nets)} nets renegotiated")
        if spec.get('open_only'):
            # Second pass: only the open nets and the nets whose copper crowds their pads.
            open_nets={n for n in nets if len(dump['islands'].get(n,[]))>1}
            tree=cKDTree([p['xy'] for p in dump['pads'] if p['net'] in open_nets])
            near=lambda xy:tree.query(xy)[0]<=spec['halo_mm']*1e6
            crowding={i['net'] for i in dump['tracks'] if i['net'] in nets and (near(i['a']) or near(i['b']))}
            crowding|={i['net'] for i in dump['vias'] if i['net'] in nets and near(i['xy'])}
            nets=sorted(open_nets|crowding);log(f"{spec['name']}: {len(open_nets)} open nets, {len(nets)} nets renegotiated")
        results,removed=negotiate(dump,nets,res=RUN['res'] or NEGOTIATE_RES.get(board_id,spec['res']),layer_cost=LAYER_COST,clearance=spec['clearance'],width=spec['signal_width'],
                                  via_diameter=spec['signal_via_diameter'],allowed_layers=SIGNAL_LAYERS,grow=spec['grow'],
                                  iterations=RUN['iterations'] or NEGOTIATE_ITERATIONS.get(board_id,spec['iterations']),present=0.5,present_growth=1.8,history=0.5,workers=RUN['workers'] or NEGOTIATE_WORKERS.get(board_id,spec['workers']),
                                  fill_guards={'-12V':'In3.Cu'},log=log,deadline=(RUN['deadline']-FINALIZE_MARGIN_S if RUN['deadline'] else time.time()+spec['budget_s']),
                                  state_path=str(ROOT/'.circuit-cache'/f"{board_id}-{spec['name']}-{hashlib.sha256(current.read_bytes()).hexdigest()[:16]}.pkl"),**neck_kwargs(board_id))
        # Out of time: the negotiation state is saved; rerun this stage to continue it.
        if results is None:return None,'resume'
        if spec.get('open_only') or spec.get('regions'):
            # A net still in conflict keeps its old copper instead of losing it.
            kept={r['net'] for r in results if not r['path']}
            results=[r for r in results if r['path']]
            removed=[u for u in removed if not any(i['uuid']==u and i['net'] in kept for k in ('tracks','vias') for i in dump[k])]
        rows,links=copper_rows(results,board_id,'grid-'+spec['name'])
    elif spec.get('signal_fanout'):
        # Reserve a via escape for every pin of a long net before long routes can box it in.
        nets=signal_chunk(dump,None,min_span_mm=spec['signal_fanout'])
        kwargs={k:v for k,v in spec.items() if k in ('clearance','signal_width','signal_via_diameter','grow','res')}
        results,removed=route(dump,nets,planes={n:None for n in nets},allowed_layers=SIGNAL_LAYERS,rail_nets=RAILS,log=log,rail_width=spec['signal_width'],via_diameter=spec['signal_via_diameter'],**kwargs)
        rows,links=copper_rows(results,board_id,'grid-'+spec['name'])
    else:
        rrr=spec.get('rrr_rounds')
        if rrr and RRR_ROUND['done']:return None,None
        chunk=lambda:spec.get('nets') or signal_chunk(dump,spec.get('chunk'),max_span_mm=spec.get('max_span_mm'),
                                                      skip=RRR_TRIED if rrr else (FAILED if spec.get('chunk') else ()),
                                                      only=set(RUN['shard']['nets']) if RUN['shard'] else None)
        nets=chunk()
        if rrr and not nets:
            if RRR_ROUND['round']+1>=len(RRR_BUDGETS):RRR_ROUND['done']=True;return None,None
            RRR_ROUND.update(round=RRR_ROUND['round']+1,adopted=False);RRR_TRIED.clear();nets=chunk()
            log(f"{spec['name']}: rip-up round {RRR_ROUND['round']+1}, budget {RRR_BUDGETS[RRR_ROUND['round']]}")
        if not nets:return None,None
        if rrr:RRR_TRIED.update(nets)
        kwargs={k:v for k,v in spec.items() if k in ('planes','clearance','rail_width','signal_width','signal_via_diameter','grow','res','window_mm','full_board','max_expansions','escape_halo_mm','rrr_rounds')}
        if rrr:kwargs.update(RRR_BUDGETS[RRR_ROUND['round']])
        kwargs['fill_guards']={'-12V':'In3.Cu'}
        if RUN['shard']:kwargs['rip_only']=set(RUN['shard']['nets'])  # a shard rips only the nets it owns
        results,removed=route(dump,nets,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,log=log,**kwargs,**neck_kwargs(board_id))
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
            if not bad:
                # Through vias cross the plane layer too; without plane-layer track, drop the new vias.
                bad={r['uuid'] for r in rows if r['kind']=='via'}
            log(f"{spec['name']}: {split} split; dropping links with copper on {sorted(plane_layers)}")
            if not bad:raise StageRejected(f"{split} split without attributable copper")
        if not bad:break
        culprits=[l for l in links if bad & set(l['copper_uuids'])]
        if not culprits:raise StageRejected("DRC errors not attributable to new copper")
        if removed:
            # A rerouted (ripped) net loses its whole new route and gets its old copper back.
            ripped_nets={i['net'] for k in ('tracks','vias') for i in dump[k] if i['uuid'] in set(removed)}
            back={l['net'] for l in culprits}&ripped_nets
            culprits+=[l for l in links if l['net'] in back and l not in culprits]
            removed=[u for u in removed if not any(i['uuid']==u and i['net'] in back for k in ('tracks','vias') for i in dump[k])]
        drop={u for l in culprits for u in l['copper_uuids']};dropped+=culprits
        rows=[r for r in rows if r['uuid'] not in drop];links=[l for l in links if l not in culprits]
        log(f"{spec['name']}: dropped {len(culprits)} links with DRC errors; retrying")
    else:raise StageRejected("DRC errors persist after dropping culprit links")
    # A candidate checked where it was built has read lower than the same file checked fresh
    # (jack-right AGND 21 vs 28), so adoption counts a copy checked in a new workspace.
    verify=workspace(board_id,spec['name']+'-verify')/candidate.name;shutil.copyfile(candidate,verify)
    drc_v,fresh=check(verify)
    if connectivity_signature(fresh)!=connectivity_signature(after):
        raise StageRejected('fresh copy connectivity differs from settled candidate')
    if any(v['severity']=='error' for v in drc_v['violations']) or drc_v['schematic_parity']:raise StageRejected("fresh copy has DRC errors or parity findings")
    candidate,after,drc=verify,fresh,drc_v
    before=json.loads(original.with_name('dump.json').read_text())['open_edges']
    receipt={'stage':spec['name'],'status':'NATIVE CHECKED DRAFT STAGE','open_edges_before':before,'open_edges_after':after['open_edges'],
             'links_added':len(links),'links_dropped_for_drc':len(dropped),'copper_rows':len(rows),
             'ripped':len(removed)+(len(repair_details['removed_source_uuids']) if repair_details else 0),
             'drc_errors':0,'drc_warnings':sum(v['severity']=='warning' for v in drc['violations']),'parity':0,
             'open_by_net_after':{n:len(g)-1 for n,g in after['islands'].items()}}
    if repair_details:receipt['local_repair']=repair_details
    return candidate,receipt


def connected_pad_groups(dump):
    """Native pad memberships; absent open nets are fully connected, not absent."""
    pads={p['uuid']:p for p in dump['pads'] if p['net']}
    by_net=collections.defaultdict(list)
    for uid,p in pads.items():by_net[p['net']].append(uid)
    return {n:sorted(sorted(u for u in g if u in pads) for g in dump['islands'].get(n,[ids]))
            for n,ids in sorted(by_net.items())}


def split_pad_groups(before,after):
    old,new=connected_pad_groups(before),connected_pad_groups(after);bad=[]
    for net,groups in old.items():
        labels={u:i for i,g in enumerate(new.get(net,[])) for u in g}
        for g in groups:
            if any(u not in labels for u in g) or len({labels[u] for u in g if u in labels})>1:
                bad.append({'net':net,'previously_connected_pads':g})
    return bad


def warning_identities(drc):
    return sorted((v['type'],tuple(sorted(i.get('uuid','') for i in v.get('items',[]))))
                  for v in drc['violations'] if v['severity']=='warning')


def promotion_gate(before,after,before_drc,after_drc):
    splits=split_pad_groups(before,after)
    previous=set(warning_identities(before_drc))
    new_warnings=[w for w in warning_identities(after_drc) if w not in previous]
    native_errors=any(v['severity']=='error' for v in after_drc['violations']) or bool(after_drc.get('schematic_parity'))
    return {'adopted':after['open_edges']<before['open_edges'] and not splits and not new_warnings and not native_errors,
            'split_pad_groups':splits,'new_warning_identities':new_warnings,'native_errors':native_errors}


def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0]);p.add_argument('board_id',choices=('osc-jack-left','osc-jack-right','osc-core'))
    p.add_argument('--from-stage',default=STAGES[0]['name']);p.add_argument('--to-stage');p.add_argument('--promote',action='store_true')
    p.add_argument('--workers',type=int,help='negotiation workers for every negotiated stage (default: per-board table)')
    p.add_argument('--max-minutes',type=float,help='stop before starting a stage after this, and cap negotiation deadlines')
    # The local core caps (0.075 mm, 30 iterations) exist for an 11 GB host; a 16 GB CI runner can lift them.
    p.add_argument('--res',type=float,help='negotiation raster in mm for every negotiated stage (default: per-board table)')
    p.add_argument('--iterations',type=int,help='negotiation iteration cap for every negotiated stage (default: per-board table)')
    p.add_argument('--after-promote',help='shell command run after each promotion, with STAGE, OPEN_BEFORE and OPEN_AFTER set (CI pushes)')
    p.add_argument('--shard',help='I/N: route only shard I of N hotspot-region shards planned from the start board (region stages only)')
    a=p.parse_args()
    RUN.update(workers=a.workers,res=a.res,iterations=a.iterations,deadline=time.time()+a.max_minutes*60 if a.max_minutes else None)
    board=ROOT/'boards'/a.board_id/f'{a.board_id}.kicad_pcb';definition=json.loads((ROOT/'design/boards'/f'{a.board_id}.json').read_text())
    if definition['layers']!=6:raise ValueError('six-layer board definition required')
    reports=board.parent/'reports'/'grid-routing';reports.mkdir(parents=True,exist_ok=True)
    work=workspace(a.board_id,'start');current=work/board.name;shutil.copyfile(board,current);drc,start_dump=check(current)
    errors=collections.Counter(v['type'] for v in drc['violations'] if v['severity']=='error')
    # Stage gates attribute every DRC error to new copper, so the start board must be clean.
    if errors or drc['schematic_parity']:raise RuntimeError(f"start board not clean: {dict(errors)}, {len(drc['schematic_parity'])} parity")
    names=[s['name'] for s in STAGES]
    last=names.index(a.to_stage)+1 if a.to_stage else len(STAGES)
    if a.shard:
        index,count=map(int,a.shard.split('/'))
        chosen=STAGES[names.index(a.from_stage):last]
        regional=all(s.get('regions') for s in chosen)
        # Area shards own disjoint nets, so only stages that route and rip signal nets alone may run.
        signal_only=all(s.get('signals') and not s.get('nets') and not s.get('repair') for s in chosen)
        if not 0<=index<count or not (regional or signal_only):
            raise ValueError('--shard needs I/N with 0<=I<N and a stage range of only region stages or only signal/rrr stages')
        signal={p['net'] for p in start_dump['pads'] if p['net'] and p['net'] not in (*RAILS,'AGND')}
        signal={n for n in signal if sum(1 for p in start_dump['pads'] if p['net']==n)>1}
    if a.shard and signal_only:
        pads=collections.defaultdict(list)
        for p_ in start_dump['pads']:
            if p_['net'] in signal:pads[p_['net']].append(p_['xy'])
        points={n:(*np.mean(xy,axis=0),len(start_dump['islands'].get(n,[None]))-1) for n,xy in pads.items()}
        shards=[{'nets':nets_,'open_nets':[n for n in nets_ if points[n][2]],'open_edges':int(sum(points[n][2] for n in nets_))} for nets_ in area_plan(points,count)]
        RUN['shard']=shards[index]
        (work/'shard-plan.json').write_text(json.dumps(shards)+'\n')
        print(f"shard {index}/{count} (area): {len(RUN['shard']['open_nets'])} open nets, {RUN['shard']['open_edges']} open edges, "
              f"{len(RUN['shard']['nets'])} owned nets",flush=True)
    elif a.shard:
        spec=chosen[0]
        regions=hotspot_regions(start_dump,spec['eps_mm'])
        shards=plan(regions,[region_nets(start_dump,signal,r,spec['margin_mm']) for r in regions],count,margin=spec['margin_mm']*1e6)
        RUN['shard']=shards[index]
        (work/'shard-plan.json').write_text(json.dumps(shards)+'\n')
        print(f"shard {index}/{count}: {len(RUN['shard']['regions'])} of {len(regions)} regions, {len(RUN['shard']['nets'])} owned nets, "
              f"{RUN['shard']['stranded_pins']} stranded pins",flush=True)
    for spec in STAGES[names.index(a.from_stage):last]:
        if RUN['deadline'] and time.time()>RUN['deadline']:
            print(f"run time budget used; rerun --from-stage {spec['name']} to resume",flush=True);break
        candidate,receipt=run_stage(a.board_id,current,spec,definition,lambda m:print(m,flush=True))
        if receipt=='resume':print(f"{spec['name']}: time budget used; rerun --from-stage {spec['name']} to resume",flush=True);break
        if candidate is None and receipt:
            receipt['adopted']=False;(reports/f"{spec['name']}.json").write_text(json.dumps(receipt,indent=1,sort_keys=True)+'\n');continue
        if candidate is None:print(f"{spec['name']}: nothing to do",flush=True);continue
        if (receipt['open_edges_after']>=receipt['open_edges_before'] or
            split_pad_groups(json.loads(current.with_name('dump.json').read_text()),
                             json.loads(candidate.with_name('dump.json').read_text()))):
            candidate,receipt=stitched(a.board_id,current,candidate,receipt,spec,definition,lambda m:print(m,flush=True))
        # Count improvements can conceal disconnected feeds/returns on another net.
        # Check after the optional stitching transaction, so temporary AGND splits
        # may be repaired in the disposable candidate but never promoted.
        receipt.update(promotion_gate(json.loads(current.with_name('dump.json').read_text()),
                                      json.loads(candidate.with_name('dump.json').read_text()),
                                      json.loads(current.with_name('drc.json').read_text()),
                                      json.loads(candidate.with_name('drc.json').read_text())))
        receipt['input_board_sha256']=hashlib.sha256(current.read_bytes()).hexdigest()
        receipt['candidate_board_sha256']=hashlib.sha256(candidate.read_bytes()).hexdigest()
        if receipt['split_pad_groups'] or receipt['new_warning_identities']:
            receipt['rejection_reason']='connected_pad_group_split' if receipt['split_pad_groups'] else 'new_native_warning'
            print(f"{spec['name']}: rejected: {receipt['rejection_reason']}",flush=True)
        if receipt['adopted']:
            # Retain a source replay against the canonical bytes that will be
            # replaced. Refill is intentionally repeated after replay.
            replay=delta((board if a.promote else current).read_text(),candidate.read_text())
            replay_path=reports/f"{spec['name']}-copper.json"
            replay_path.write_text(json.dumps(replay,sort_keys=True)+'\n')
            receipt['copper_replay']={'path':rel(replay_path),'sha256':hashlib.sha256(replay_path.read_bytes()).hexdigest(),
                                     'base_sha256':replay['base_sha256']}
        if spec.get('rrr_rounds') and receipt['adopted']:RRR_ROUND['adopted']=True
        (reports/f"{spec['name']}.json").write_text(json.dumps(receipt,indent=1,sort_keys=True)+'\n')
        print(f"{spec['name']}: {receipt['open_edges_before']} -> {receipt['open_edges_after']} open edges",flush=True)
        if receipt['adopted']:
            current=candidate
            # Promote every adopted stage so a later interruption keeps checked progress.
            if a.promote:shutil.copyfile(current,board);print('promoted',rel(board),flush=True)
            if a.promote and a.after_promote:
                env={**os.environ,'STAGE':spec['name'],'OPEN_BEFORE':str(receipt['open_edges_before']),'OPEN_AFTER':str(receipt['open_edges_after'])}
                done=subprocess.run(a.after_promote,shell=True,cwd=ROOT,env=env)
                if done.returncode:print(f"after-promote command failed ({done.returncode}); routing continues",flush=True)
    print('final candidate',rel(current))


if __name__=='__main__':main()
