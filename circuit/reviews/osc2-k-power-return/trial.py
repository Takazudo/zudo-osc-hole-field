#!/usr/bin/env python3
"""OSC2: run one bounded K power/return hypothesis against the adopted K3409 board, never promoting.

Each hypothesis is one stage spec handed unchanged to scripts/pcbgen/route_jack_grid.py
(stage(), stitched(), warning_complete_gate()); that shared driver is imported, not
edited. The adopted board is copied into a disposable .circuit-cache workspace and is
never replaced. The trial receipt, the candidate copper delta and a small precision
return summary are written under this review folder. Draft only: electrical, thermal
and physical qualification remain NOT RUN, and no fabrication output is created.
"""
from __future__ import annotations
import argparse,collections,datetime,hashlib,json,resource,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import scripts.pcbgen.route_jack_grid as driver
from scripts.pcbgen.route_shards import delta

HERE=Path(__file__).resolve().parent
BOARD_ID='osc-core'
K3409_SHA='dda33a25479c9993f71e33d49129cf16414828b3dd2083b6d4f91a65421c728c'
PLANES=driver.PLANES

# Every hypothesis names what it changes, what copper it keeps and when it ends.
# Physical difference: H1 only drops vias into the existing In4/In3 planes; H2 routes +5V
# (no plane) as narrow links; H3 reruns the rejected rail-escapes stage unchanged except
# that the split-attributing culprit drop (agnd_guard) is enabled.
HYPOTHESES={
    'h1-plane-escapes':{
        'changes':'short through-via escapes from stranded +12V/-12V pads and copper into the existing In4.Cu/In3.Cu planes',
        'keeps':'all existing copper; no rip-up; no new plane or pour; +5V and AGND untouched except by optional AGND stitching',
        'spec':{'name':'osc2-h1-plane-escapes','nets':['+12V','-12V'],'planes':PLANES,'clearance':.25,'rail_width':.25,
                'res':.05,'agnd_guard':True},
    },
    'h2-5v-trunks':{
        'changes':'+5V island-to-island trunks at 0.25 mm on the signal layers inside 24 mm windows (K3409 +5V gaps reach 19.7 mm), with the AGND pour guard',
        'keeps':'all existing copper; no rip-up; no +5V pour; +12V/-12V/AGND untouched except by optional AGND stitching',
        'spec':{'name':'osc2-h2-5v-trunks','nets':['+5V'],'clearance':.25,'rail_width':.25,'res':.05,'window_mm':24,'agnd_guard':True},
    },
    'h3-escapes-split-repair':{
        'changes':'the rejected rail-escapes stage (all rails, 0.25 mm, 6 mm windows) with the links nearest each split AGND pad group dropped and retried',
        'keeps':'all existing copper; no rip-up; same router arguments as rail-escapes plus agnd_guard',
        'spec':{**next(s for s in driver.STAGES if s['name']=='rail-escapes'),'name':'osc2-h3-escapes-split-repair','agnd_guard':True},
    },
}
LIMITS={'wall_minutes':150,'max_rss_note':'host 15 GiB, no swap; one trial at a time','stage_retries':'route_jack_grid.stage(): at most 8 drop-and-retry passes',
        'refill':'route_jack_grid.check(): three equal island signatures, at most six refills'}
END='one native-checked candidate (or a rejection) per hypothesis; never repeated with unchanged inputs'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rail_summary(dump):
    open_by={n:len(g)-1 for n,g in dump['islands'].items() if len(g)>1}
    rails={n:open_by.get(n,0) for n in driver.RAILS}
    return {'open_edges':dump['open_edges'],'agnd_open_edges':open_by.get('AGND',0),'agnd_islands':len(dump['islands'].get('AGND',[None])),
            'rail_open_edges':rails,'other_signal_open_edges':dump['open_edges']-open_by.get('AGND',0)-sum(rails.values())}


def precision_returns(before,after):
    """AGND pads that change island membership, grouped by reference designator prefix."""
    pads={p['uuid']:p for p in after['pads']}
    def label(dump):
        groups=dump['islands'].get('AGND',[]);main=max(range(len(groups)),key=lambda i:len(groups[i])) if groups else None
        return {u:(i==main) for i,g in enumerate(groups) for u in g},(len(groups[main]) if groups else 0)
    b,bm=label(before);a,am=label(after)
    agnd=[u for u,p in pads.items() if p['net']=='AGND']
    joined=[u for u in agnd if a.get(u,True) and not b.get(u,True)]
    lost=[u for u in agnd if b.get(u,True) and not a.get(u,True)]
    ref=lambda u:pads[u].get('ref') or pads[u].get('name','?')
    return {'main_agnd_group_before':bm,'main_agnd_group_after':am,
            'agnd_pads_joined_main':len(joined),'agnd_pads_left_main':len(lost),
            'left_main_refs':sorted({ref(u) for u in lost})[:50]}


def resumed_stage(spec,base,before):
    """The fresh-copy verified candidate an interrupted run left behind, as stage() would return it.

    stage() writes <name>-verify only after the candidate passed DRC, parity and the
    fresh-copy connectivity comparison; a container restart can then lose the gate.
    Link counts are not retained there, so only native counts are reported.
    """
    verify=ROOT/'.circuit-cache'/f"{BOARD_ID}-grid-{spec['name']}-verify"/f'{BOARD_ID}.kicad_pcb'
    if not all(verify.with_name(n).exists() for n in ('drc.json','dump.json',verify.name)):return None,None
    drc=json.loads(verify.with_name('drc.json').read_text());after=json.loads(verify.with_name('dump.json').read_text())
    if after.get('board_sha256') not in (None,sha(verify)):raise RuntimeError('verified dump does not describe the candidate bytes')
    if any(v['severity']=='error' for v in drc['violations']) or drc['schematic_parity']:raise RuntimeError('verified candidate has native errors')
    proposal=json.loads((ROOT/'.circuit-cache'/f"{BOARD_ID}-grid-{spec['name']}"/'proposal.json').read_text())
    if proposal['board_sha256']!=K3409_SHA:raise RuntimeError('proposal was not built on K3409')
    return verify,{'stage':spec['name'],'status':'NATIVE CHECKED DRAFT STAGE','resumed_from_verified_candidate':True,
                   'open_edges_before':before['open_edges'],'open_edges_after':after['open_edges'],
                   'copper_rows':len(proposal['copper']),'new_vias':sum(r['kind']=='via' for r in proposal['copper']),'ripped':len(proposal['removed_uuids']),
                   'drc_errors':0,'drc_warnings':sum(v['severity']=='warning' for v in drc['violations']),'parity':0,
                   'open_by_net_after':{n:len(g)-1 for n,g in after['islands'].items()}}


def trial(key,base_work,resume=False,audit_not_run=None):
    h=HYPOTHESES[key];spec=h['spec']
    definition=json.loads((ROOT/'design/boards'/f'{BOARD_ID}.json').read_text())
    base=base_work/f'{BOARD_ID}.kicad_pcb'
    if sha(base)!=K3409_SHA:raise RuntimeError('base workspace is not the adopted K3409 bytes')
    before=json.loads(base.with_name('dump.json').read_text());before_drc=json.loads(base.with_name('drc.json').read_text())
    log=lambda m:print(m,flush=True)
    t0=time.time()
    candidate,receipt=resumed_stage(spec,base,before) if resume else (None,None)
    if candidate is None:candidate,receipt=driver.run_stage(BOARD_ID,base,spec,definition,log)
    out={'schema':'osc2-k-power-return-trial-1','hypothesis':key,'changes':h['changes'],'keeps':h['keeps'],'spec':spec,
         'limits':LIMITS,'end_condition':END,'input_board_sha256':K3409_SHA,
         'started_utc':datetime.datetime.fromtimestamp(t0,datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
         'tool':{'kicad_cli_version':driver.run('bash','scripts/kicad/run.sh','kicad-cli','version').strip(),'wrapper':'scripts/kicad/run.sh'},
         'before':rail_summary(before),'adopted':False,'promoted':False,
         'status':'UNVALIDATED DRAFT TRIAL; NOT PROMOTED','fabrication_outputs':'NOT CREATED',
         'qualification':'NOT RUN: electrical, thermal and physical qualification'}
    if candidate is None:
        out.update(result=receipt or {'status':'NOTHING TO DO'},after=None)
    else:
        if (receipt['open_edges_after']>=receipt['open_edges_before'] or
            driver.split_pad_groups(before,json.loads(candidate.with_name('dump.json').read_text()))):
            candidate,receipt=driver.stitched(BOARD_ID,base,candidate,receipt,spec,definition,log)
        if audit_not_run:
            # Raw gate only; the capped reports stay incomplete and nothing may be adopted from this receipt.
            gate=driver.promotion_gate(before,json.loads(candidate.with_name('dump.json').read_text()),before_drc,json.loads(candidate.with_name('drc.json').read_text()))
            receipt.update(gate,capped_warning_types=driver.warning_capped(before_drc,json.loads(candidate.with_name('drc.json').read_text())),
                           raw_gate_would_adopt=gate['adopted'],adopted=False,rejection_reason='incomplete_native_warning_evidence',
                           complete_native_warning_evidence_status='NOT RUN: '+audit_not_run)
        else:receipt=driver.complete_gate(BOARD_ID,base,candidate,receipt,spec)
        receipt['candidate_board_sha256']=sha(candidate)
        after=json.loads(candidate.with_name('dump.json').read_text())
        if not receipt['adopted'] and (receipt['split_pad_groups'] or receipt['new_warning_identities']) and 'rejection_reason' not in receipt:
            receipt['rejection_reason']='connected_pad_group_split' if receipt['split_pad_groups'] else 'new_native_warning'
        gate_pass=bool(receipt['adopted'])
        receipt['split_pad_groups']=[{'net':s['net'],'pads':len(s['previously_connected_pads'])} for s in receipt['split_pad_groups']]
        receipt.pop('raw_promotion_gate',None)
        replay=delta(base.read_text(),candidate.read_text())
        (HERE/f'{key}-copper.json').write_text(json.dumps(replay,sort_keys=True)+'\n')
        out.update(result=receipt,after=rail_summary(after),precision_returns=precision_returns(before,after),
                   gate_would_adopt=gate_pass,candidate_board_sha256=receipt['candidate_board_sha256'],
                   copper_delta={'path':str((HERE/f'{key}-copper.json').relative_to(ROOT)),'sha256':sha(HERE/f'{key}-copper.json'),
                                 'added':len(replay.get('added',[])),'removed':len(replay.get('removed',[]))})
        if sha(ROOT/'boards'/BOARD_ID/f'{BOARD_ID}.kicad_pcb')!=K3409_SHA:raise RuntimeError('adopted board changed during the trial')
    out['wall_seconds']=round(time.time()-t0)
    out['peak_rss_mib_self_and_children']=round(max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)/1024)
    (HERE/f'{key}.json').write_text(json.dumps(out,indent=1,sort_keys=True)+'\n')
    print(json.dumps({k:out.get(k) for k in ('hypothesis','before','after','gate_would_adopt','wall_seconds')}),flush=True)


def baseline():
    """Settle the K3409 copy once (three equal refills) so every trial starts from the same dump."""
    work=driver.workspace(BOARD_ID,'osc2-base');copy=work/f'{BOARD_ID}.kicad_pcb'
    shutil.copyfile(ROOT/'boards'/BOARD_ID/f'{BOARD_ID}.kicad_pcb',copy)
    drc,dump=driver.check(copy)
    s=rail_summary(dump);s.update(refilled_sha256=sha(copy),input_sha256=K3409_SHA)
    (HERE/'baseline.json').write_text(json.dumps(s,indent=1,sort_keys=True)+'\n');print(json.dumps(s),flush=True)
    return work


def record_baseline(work):
    """Summarize the settled base workspace without refilling it again."""
    dump=json.loads((work/'dump.json').read_text());drc=json.loads((work/'drc.json').read_text())
    s=rail_summary(dump);s.update(input_sha256=K3409_SHA,refilled_sha256=sha(work/f'{BOARD_ID}.kicad_pcb'),
        drc_errors=sum(v['severity']=='error' for v in drc['violations']),schematic_parity=len(drc.get('schematic_parity',[])),
        capped_warning_types=driver.warning_capped(drc,drc))
    (HERE/'baseline.json').write_text(json.dumps(s,indent=1,sort_keys=True)+'\n');print(json.dumps(s),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('hypothesis',choices=['baseline','record-baseline',*HYPOTHESES])
    p.add_argument('--audit-not-run',metavar='REASON',help='record the raw gate only, with the complete-warning audit NOT RUN for REASON (never adoptable)')
    p.add_argument('--resume',action='store_true',help='gate the verified candidate an interrupted run left behind')
    a=p.parse_args()
    if a.hypothesis=='baseline':baseline();return
    work=ROOT/'.circuit-cache'/f'{BOARD_ID}-grid-osc2-base'
    if a.hypothesis=='record-baseline':record_baseline(work);return
    trial(a.hypothesis,work,a.resume,a.audit_not_run)


if __name__=='__main__':main()
