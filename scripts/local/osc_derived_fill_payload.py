"""Derived-copy fill and evaluation of the frozen core (container payload, option C).

Pinned KiCad 10.0.6 pcbnew, disposable copies under /scratch only; /work is the
read-only published source and is never written. Two modes:

derive: fill exactly the zones named in /spec/spec.json on a copy of the
  source (or of a verified parent derivation mounted at /candidate), observe
  the spec pad pairs before and after, save, reload, re-observe, classify each
  pair, and export the derived board with the pinned project and rules plus a
  manifest carrying its composite identity to the writable /output mount.
evaluate: verify a saved derived board at /candidate against the identity the
  spec and context imply (real file hashes, non-fill semantics against the
  current source, fill ownership), then observe the spec pairs on the source
  and on the derived board without filling anything; a stale or different
  copy is rejected with a reason and never reused as evidence.

Connectivity is native cluster membership (GetConnectedItems returns the whole
cluster in 10.0.6), never net-name equality or shape intersection. No DRC, no
all-zone fill, no route edits, no board acceptance.
"""
import collections
import json
import shutil
import sys
import time
from pathlib import Path

import osc_derived_fill as derived
import osc_frozen_fill as fill
import osc_frozen_topology as topology
import osc_single_zone_payload as zone

WORKER_RESERVE=zone.WORKER_RESERVE
DERIVE_STAGES=zone.STAGES
DERIVE_GROUP=zone.STAGE_GROUP
EVALUATE_STAGES=('load','identity','before','load_derived','after','verify')
EVALUATE_GROUP={'load':'prepare','identity':'prepare','before':'prepare','load_derived':'verify','after':'verify','verify':'verify'}
EVALUATE_CAPS={'prepare':150,'verify':230}
DERIVE_STATUS='DERIVED_FILL_EXPORTED_NOT_ACCEPTANCE'
EVALUATE_STATUS='DERIVED_FILL_EVALUATION_NOT_ACCEPTANCE'
REJECTED_STATUS='DERIVED_REUSE_REJECTED_NOT_ACCEPTANCE'
STATUSES={'derive':DERIVE_STATUS,'evaluate':EVALUATE_STATUS}
RECEIPTS=('zone.json','zone-substages.jsonl')
require=zone.require
uid=zone.uid

def layer_map(pcbnew): return {n:getattr(pcbnew,n.replace('.','_')) for n in topology.COPPER_LAYERS}

def zone_table(board,layers):
    rows=[]
    for z in board.Zones():
        on=[n for n,l in layers.items() if z.IsOnLayer(l)]
        rows.append({'uuid':uid(z),'net':z.GetNetname(),'rule_area':bool(z.GetIsRuleArea()),'layers':on,
                     'counts':{n:int(z.GetFilledPolysList(layers[n]).OutlineCount()) for n in on}})
    require(len(rows)==zone.COUNTS['zone'],'zone count')
    return sorted(rows,key=lambda r:r['uuid'])

def nonselected_fill(rows,selected): return [(r['uuid'],json.dumps(r['counts'],sort_keys=True)) for r in rows if r['uuid'] not in selected]

def net_zones(rows,net,selected):
    return [{'uuid':r['uuid'],'layers':r['layers'],'filled':bool(r['counts']) and all(c>=1 for c in r['counts'].values()),'selected':r['uuid'] in selected}
            for r in rows if r['net']==net and not r['rule_area']]

def select_zones(board,layers,uuids,must_be_unfilled):
    found={}
    for z in board.Zones():
        if uid(z) in uuids:
            require(uid(z) not in found,'selected zone duplicated '+uid(z));found[uid(z)]=z
    require(set(found)==set(uuids),'selected zone missing')
    for u,z in found.items():
        require(not z.GetIsRuleArea() and z.GetNetname(),'selected zone must be a copper net zone '+u)
        require(z.Outline().OutlineCount()>=1,'selected zone outline '+u)
        if must_be_unfilled: require(all(int(z.GetFilledPolysList(l).OutlineCount())==0 for l in layers.values() if z.IsOnLayer(l)),'selected zone already filled '+u)
    return found

def spec_pads(board):
    pads={};names={}
    for f in board.GetFootprints():
        for p in f.Pads():
            name=f.GetReference()+'.'+p.GetNumber();names[uid(p)]=name
            if name in topology.EXPECTED:
                require(name not in pads and uid(p)==topology.EXPECTED[name]['uuid'] and p.GetNetname()==topology.EXPECTED[name]['net'],'pad identity '+name)
                pads[name]=p
    require(set(pads)==set(topology.EXPECTED),'missing pad')
    return pads,names

def selected_polys(selected,layers):
    polys=[]
    for u,z in sorted(selected.items()):
        for n,l in layers.items():
            if z.IsOnLayer(l):
                poly=z.GetFilledPolysList(l)
                if poly.OutlineCount(): polys.append((u,n,poly))
    return polys

def summarize_cluster(items,layers,names,selected,polys):
    counts=collections.Counter();by_layer=collections.Counter();vias=[];zones=[];pad_names=[];truncated=0
    for item in items:
        if hasattr(item,'Cast'): item=item.Cast()
        kind=type(item).__name__;counts[kind]+=1
        for name in zone.layer_names(item,layers): by_layer[name]+=1
        if kind=='PCB_VIA':
            if len(vias)>=zone.VIA_LIMIT: truncated+=1;continue
            row=zone.describe(item,layers,names)
            row['inside_selected_fill']=sorted({u for u,_,poly in polys if poly.Contains(item.GetPosition())}) if polys else None
            vias.append(row)
        elif kind=='ZONE': zones.append({'uuid':uid(item),'net':item.GetNetname(),'layers':zone.layer_names(item,layers),'selected':uid(item) in selected})
        elif kind=='PAD': pad_names.append(names.get(uid(item),uid(item)))
    return {'size':len(items),'counts':dict(counts),'layers':dict(by_layer),'vias':sorted(vias,key=lambda r:r['uuid']),'zones':sorted(zones,key=lambda r:r['uuid']),
            'pads':sorted(pad_names),'selected_zone_member':any(z['selected'] for z in zones),'vias_truncated':truncated}

def pair_observations(board,layers,pairs,selected,previous=None):
    conn=board.GetConnectivity();conn.Build(board)
    pads,names=spec_pads(board);polys=selected_polys(selected,layers)
    rows={}
    for a,b in pairs:
        ca,cb=zone.cluster(conn,pads[a]),zone.cluster(conn,pads[b])
        ids_a={uid(x) for x in ca};ids_b={uid(x) for x in cb}
        row={'connected':uid(pads[b]) in ids_a,'symmetric':uid(pads[a]) in ids_b,'net':topology.EXPECTED[a]['net'],
             'cluster_a':summarize_cluster(ca,layers,names,selected,polys),'cluster_b':summarize_cluster(cb,layers,names,selected,polys)}
        require(row['connected']==row['symmetric'],'asymmetric cluster membership '+a+'<->'+b)
        if previous is not None:
            before=previous[a+'<->'+b];side_a={v['uuid'] for v in before['cluster_a']['vias']};side_b={v['uuid'] for v in before['cluster_b']['vias']}
            merged=row['cluster_a']['vias'] if row['connected'] else []
            row['bridging_vias']={'from_a_side':[v for v in merged if v['uuid'] in side_a and v['inside_selected_fill']],
                                  'from_b_side':[v for v in merged if v['uuid'] in side_b and v['inside_selected_fill']],
                                  'new_in_merged_cluster':[v for v in merged if v['uuid'] not in side_a|side_b and v['inside_selected_fill']][:zone.VIA_LIMIT]}
        rows[a+'<->'+b]=row
    conn.RecalculateRatsnest()
    rows['ratsnest']={'unconnected_count':int(conn.GetUnconnectedCount(True))}
    return rows

def classify(pairs,before,after,rows,selected):
    return {a+'<->'+b:derived.classify_pair(before[a+'<->'+b]['connected'],after[a+'<->'+b]['connected'],net_zones(rows,topology.EXPECTED[a]['net'],selected)) for a,b in pairs}

def worker(scratch):
    spec=json.loads((scratch/'spec.json').read_text());mode=spec['mode'];pairs=[tuple(p) for p in spec['pairs']];selected_ids=set(spec['zones'])
    stages=zone.StageLog(scratch/'zone-substages.jsonl');result={'board_acceptance':False,'mode':mode,'repair_basis':False}
    try:
        import pcbnew
        require(pcbnew.GetBuildVersion()==derived.KICAD_VERSION,'pcbnew version')
        layers=layer_map(pcbnew)
        with stages.stage('load'):
            board=pcbnew.LoadBoard(str(scratch/'input'/'osc-core.kicad_pcb'));require(board is not None,'load failed')
        with stages.stage('identity'):
            result['counts']=zone.counts(board);result['duplicates_before']=zone.duplicates(board)
            rows=zone_table(board,layers);result['input_zone_owners']=sorted(r['uuid'] for r in rows if any(c>=1 for c in r['counts'].values()))
            require(result['input_zone_owners']==sorted(spec['input_zones']),'input fill ownership differs from the declared input')
            selected=select_zones(board,layers,selected_ids,must_be_unfilled=(mode=='derive'))
        with stages.stage('before'):
            result['before']={'zones_nonselected':nonselected_fill(rows,selected_ids),'overrides':zone.overrides(board,layers),'pairs':pair_observations(board,layers,pairs,{})}
        if mode=='derive':
            with stages.stage('fill'):
                selection=pcbnew.ZONES()
                for u in sorted(selected): selection.append(selected[u])
                require(len(selection)==len(selected_ids),'selection length')
                started=time.monotonic();ok=pcbnew.ZONE_FILLER(board).Fill(selection,False)
                result['fill']={'returned':bool(ok),'seconds':time.monotonic()-started,'zones':sorted(selected_ids)}
                require(ok is True,'Fill not true')
            with stages.stage('after'):
                rows=zone_table(board,layers)
                result['after']={'zones':[r for r in rows if r['uuid'] in selected_ids],'zones_nonselected':nonselected_fill(rows,selected_ids),'overrides':zone.overrides(board,layers),
                    'duplicates':zone.duplicates(board),'counts':zone.counts(board),'pairs':pair_observations(board,layers,pairs,selected,result['before']['pairs'])}
                require(result['after']['zones_nonselected']==result['before']['zones_nonselected'],'nonselected native fill changed')
                require(all(all(c>=1 for c in r['counts'].values()) for r in result['after']['zones']),'a selected zone has no fill on one of its layers')
            with stages.stage('save'):
                out=scratch/'after'/'osc-core.kicad_pcb';pcbnew.SaveBoard(str(out),board);require(out.is_file(),'save failed')
            with stages.stage('reload'):
                board=pcbnew.LoadBoard(str(out));require(board is not None,'reload failed')
        else:
            with stages.stage('load_derived'):
                board=pcbnew.LoadBoard(str(scratch/'derived'/'osc-core.kicad_pcb'));require(board is not None,'derived load failed')
            with stages.stage('after'):
                rows=zone_table(board,layers);selected=select_zones(board,layers,selected_ids,must_be_unfilled=False)
                result['after']={'zones':[r for r in rows if r['uuid'] in selected_ids],'zones_nonselected':nonselected_fill(rows,selected_ids),'overrides':zone.overrides(board,layers),
                    'duplicates':zone.duplicates(board),'counts':zone.counts(board),'pairs':pair_observations(board,layers,pairs,selected,result['before']['pairs'])}
                require(result['after']['zones_nonselected']==result['before']['zones_nonselected'],'derived board differs from the source outside the selected zones')
                require(all(all(c>=1 for c in r['counts'].values()) for r in result['after']['zones']),'derived board lacks fill on a selected zone layer')
        with stages.stage('verify'):
            rows=zone_table(board,layers);selected=select_zones(board,layers,selected_ids,must_be_unfilled=False)
            result['reloaded']={'zones':[r for r in rows if r['uuid'] in selected_ids],'zone_table':rows,'zones_nonselected':nonselected_fill(rows,selected_ids),'overrides':zone.overrides(board,layers),
                'duplicates':zone.duplicates(board),'counts':zone.counts(board),'pairs':pair_observations(board,layers,pairs,selected,result['before']['pairs'])}
            require(result['reloaded']['zones_nonselected']==result['before']['zones_nonselected'],'nonselected fill changed on reload')
            require(result['reloaded']['duplicates']==result['duplicates_before']==result['after']['duplicates'],'duplicate identity changed')
            require([r['counts'] for r in result['reloaded']['zones']]==[r['counts'] for r in result['after']['zones']],'selected fill not preserved on reload')
            for key in result['after']['pairs']:
                if key!='ratsnest': require(result['after']['pairs'][key]['connected']==result['reloaded']['pairs'][key]['connected'],'pair connectivity changed on reload '+key)
            result['classification']=classify(pairs,result['before']['pairs'],result['reloaded']['pairs'],rows,selected_ids)
    except Exception as exc:
        result['failure']=type(exc).__name__+': '+str(exc)[:500]
        (scratch/'zone.json').write_text(json.dumps(result,sort_keys=True));raise
    finally: stages.close()
    (scratch/'zone.json').write_text(json.dumps(result,sort_keys=True))

def read_context(spec_dir):
    context=json.loads((spec_dir/'context.json').read_text())
    require(set(context)=={'image_id','kicad','source_pins','process','tooling_sha','budget'},'context shape')
    require(context['kicad']==derived.KICAD_VERSION and context['process']==derived.PROCESS_VERSION and context['source_pins']==fill.PINS,'context pins')
    derived.budget(context['budget'])
    return context

def limits(b):
    return ('budget '+b['name']+': payload %d s; worker reserve %d s; derive stage caps prepare %d / fill %d / verify %d; evaluate caps prepare %d / verify %d; output board bound %d bytes; selected zones only; no route edits'
            %(b['payload'],WORKER_RESERVE,b['stage_caps']['prepare'],b['stage_caps']['fill'],b['stage_caps']['verify'],EVALUATE_CAPS['prepare'],EVALUATE_CAPS['verify'],b['pcb_limit']))

def parent_identity(candidate_dir,context,source_nonfill):
    """Verify a mounted derivation against the identity its own manifest records, re-pinned to this run's source, image and process."""
    manifest=json.loads((candidate_dir/'manifest.json').read_text())
    recorded=derived.manifest_identity(manifest,candidate_dir)[0]
    expected=derived.identity(context['source_pins'],recorded['zones'],context['image_id'],context['kicad'],recorded.get('parent_key'))
    return derived.verify_derived(candidate_dir,expected,source_nonfill,fill.semantic_hash)

def compact(worker_result):
    phases={phase:{k:v.get('connected') for k,v in (worker_result.get(phase) or {}).get('pairs',{}).items() if k!='ratsnest'} for phase in ('before','after','reloaded')}
    ratsnest={phase:((worker_result.get(phase) or {}).get('pairs',{}).get('ratsnest') or {}).get('unconnected_count') for phase in ('before','after','reloaded')}
    return {'fill':worker_result.get('fill'),'counts':worker_result.get('counts'),'selected_after':(worker_result.get('after') or {}).get('zones'),'connected':phases,
            'unconnected_count':ratsnest,'classification':worker_result.get('classification'),'failure':worker_result.get('failure')}

def export(scratch,output,names):
    exported={}
    for name in names: shutil.copyfile(scratch/name,output/name);exported[name]=fill.sha(output/name)
    return exported

def run(mode,root,spec_dir,candidate_dir,scratch,output,result):
    start=time.monotonic()
    require(output.is_dir() and not any(output.iterdir()),'empty writable /output required')
    fill.record_memory(result,'preflight','before')
    spec=derived.load_spec(spec_dir/'spec.json',topology.EXPECTED);context=read_context(spec_dir)
    b=derived.budget(context['budget']);derived.budget_allows(b,mode,spec['zones'],chained=mode=='derive' and candidate_dir.is_dir());deadline=start+b['payload']
    result['budget']=b['name'];result['limits']=limits(b)
    result['spec']={'zones':spec['zones'],'pairs':spec['pairs'],'note':spec['note']};result['tooling_sha']=context['tooling_sha']
    result['input_before']=fill.verify_inputs(root)
    result['source_nonfill']=fill.semantic_hash(root/'osc-core.kicad_pcb')
    result['source_owners']=derived.zone_fill_owners(root/'osc-core.kicad_pcb')
    require(result['source_owners']=={'zones':zone.COUNTS['zone'],'filled_polygon_by_zone':{}},'published source must be unfilled with the pinned zone count')
    scratch.mkdir(exist_ok=False);(scratch/'input').mkdir();(scratch/'after').mkdir()
    for name in ('osc-core.kicad_pro','osc-core.kicad_dru'): shutil.copyfile(root/name,scratch/'input'/name)
    input_zones=[];parent_key=None
    if mode=='derive':
        if candidate_dir.is_dir():
            result['parent']=parent_identity(candidate_dir,context,result['source_nonfill'])
            if not result['parent']['reusable']: result['status']=REJECTED_STATUS;raise ValueError('parent derivation rejected: '+result['parent']['reason'])
            parent_key=derived.identity_key(result['parent']['identity']);input_zones=sorted(set(result['parent']['identity']['zones'])|set(result['parent']['ancestor_zones']))
            require(not set(input_zones)&set(spec['zones']),'selected zones overlap the parent derivation')
            shutil.copyfile(candidate_dir/'after'/'osc-core.kicad_pcb',scratch/'input'/'osc-core.kicad_pcb')
        else:
            shutil.copyfile(root/'osc-core.kicad_pcb',scratch/'input'/'osc-core.kicad_pcb')
        ident=derived.identity(context['source_pins'],spec['zones'],context['image_id'],context['kicad'],parent_key)
    else:
        require(candidate_dir.is_dir(),'evaluate needs a derived board at /candidate')
        manifest=json.loads((candidate_dir/'manifest.json').read_text());recorded=derived.manifest_identity(manifest,candidate_dir)[0]
        ident=derived.identity(context['source_pins'],spec['zones'],context['image_id'],context['kicad'],recorded.get('parent_key'))
        result['reuse']=derived.verify_derived(candidate_dir,ident,result['source_nonfill'],fill.semantic_hash)
        if not result['reuse']['reusable']: result['status']=REJECTED_STATUS;raise ValueError('derived board rejected: '+result['reuse']['reason'])
        require(recorded.get('parent_key') is None,'evaluate of chained derivations is not supported: input fill ownership would not be the source')
        shutil.copyfile(root/'osc-core.kicad_pcb',scratch/'input'/'osc-core.kicad_pcb')
        (scratch/'derived').mkdir();shutil.copyfile(candidate_dir/'after'/'osc-core.kicad_pcb',scratch/'derived'/'osc-core.kicad_pcb')
    result['identity']=ident;result['identity_key']=derived.identity_key(ident)
    (scratch/'spec.json').write_text(json.dumps({'mode':mode,'zones':spec['zones'],'pairs':spec['pairs'],'input_zones':input_zones}))
    result['input_hashes']={name:fill.sha(scratch/'input'/name) for name in derived.BOARD_FILES}
    fill.record_memory(result,'preflight','after')
    fill.record_memory(result,'zone','before')
    result['command']={}
    group,caps,stages=(DERIVE_GROUP,b['stage_caps'],DERIVE_STAGES) if mode=='derive' else (EVALUATE_GROUP,EVALUATE_CAPS,EVALUATE_STAGES)
    zone.run_worker(scratch,deadline-WORKER_RESERVE,result['command'],script=__file__,stage_group=group,stage_caps=caps,pcb_limit=b['pcb_limit'])
    zone.capture_stages(result,scratch,require_complete=True,stages=stages)
    worker_result=json.loads((scratch/'zone.json').read_text())
    result['worker_summary']=compact(worker_result)
    require(result['worker_summary']['failure'] is None and isinstance(result['worker_summary']['classification'],dict),'worker result')
    fill.record_memory(result,'zone','after')
    fill.record_memory(result,'verify','before')
    if mode=='derive':
        require(result['worker_summary']['fill'].get('returned') is True,'worker fill')
        after=scratch/'after'/'osc-core.kicad_pcb'
        for name in ('osc-core.kicad_pro','osc-core.kicad_dru'): shutil.copyfile(root/name,scratch/'after'/name)
        result['nonfill_after']=fill.semantic_hash(after)
        require(result['source_nonfill']==result['nonfill_after'],'non-fill semantic change in derived copy')
        result['after_owners']=derived.zone_fill_owners(after)
        require(result['after_owners']['zones']==zone.COUNTS['zone'] and set(result['after_owners']['filled_polygon_by_zone'])==set(input_zones)|set(spec['zones']),'filled_polygon ownership differs from input zones plus selected zones')
        (output/'after').mkdir();result['exported']={}
        for name in derived.BOARD_FILES: shutil.copyfile(scratch/'after'/name,output/'after'/name);result['exported'][name]=fill.sha(output/'after'/name)
        result['exported_receipts']=export(scratch,output,RECEIPTS)
        manifest={'status':derived.MANIFEST_STATUS,'identity':ident,'identity_key':result['identity_key'],'exported':{'after':result['exported']},'input_hashes':result['input_hashes'],
                  'nonfill_sha256':{'source':result['source_nonfill'],'after':result['nonfill_after']},'after_owners':result['after_owners'],'fill_seconds':result['worker_summary']['fill']['seconds'],
                  'pairs':spec['pairs'],'classification':result['worker_summary']['classification'],'unconnected_count':result['worker_summary']['unconnected_count'],
                  'parent':{'identity_key':parent_key,'zones':input_zones},'spec_note':spec['note'],'tooling_sha':context['tooling_sha'],'exported_receipts':result['exported_receipts'],
                  'budget':b['name'],'stage_caps':b['stage_caps'],'board_acceptance':False,'repair_basis':False}
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');result['manifest_sha256']=fill.sha(output/'manifest.json')
    else:
        result['exported_receipts']=export(scratch,output,RECEIPTS)
        evaluation={'status':EVALUATE_STATUS,'identity':ident,'identity_key':result['identity_key'],'reuse':result['reuse'],'pairs':spec['pairs'],
                    'classification':result['worker_summary']['classification'],'connected':result['worker_summary']['connected'],'unconnected_count':result['worker_summary']['unconnected_count'],
                    'spec_note':spec['note'],'tooling_sha':context['tooling_sha'],'exported_receipts':result['exported_receipts'],'board_acceptance':False,'repair_basis':False}
        (output/'evaluation.json').write_text(json.dumps(evaluation,indent=2,sort_keys=True)+'\n');result['evaluation_sha256']=fill.sha(output/'evaluation.json')
    result['input_after']=fill.verify_inputs(root)
    fill.record_memory(result,'verify','after')
    require(time.monotonic()<=deadline,'payload deadline')
    result['status']=STATUSES[mode]

def main(mode):
    start=time.monotonic()
    root=Path('/work/boards/osc-core');spec_dir=Path('/spec');candidate_dir=Path('/candidate');scratch=Path('/scratch/osc-'+mode);output=Path('/output')
    result={'status':'FAILED','mode':mode,'board_acceptance':False,'repair_basis':False,'full_board_fill':False,'refill_zones_option_used':False,
            'drc':'NOT RUN: outside this derived-copy connectivity diagnostic',
            'limits':'budget profile is read from /spec/context.json before any native work; selected zones only; no route edits'}
    try:
        run(mode,root,spec_dir,candidate_dir,scratch,output,result)
    except Exception as exc:
        result['failure']={'type':type(exc).__name__,'message':str(exc)[:500]}
        if result['status']!=REJECTED_STATUS: result['status']='FAILED'
        if scratch.is_dir():
            try: zone.capture_stages(result,scratch,stages=DERIVE_STAGES if mode=='derive' else EVALUATE_STAGES)
            except Exception as check: result['substage_capture_failure']=type(check).__name__+': '+str(check)[:240]
            if (scratch/'zone.json').is_file():
                try: result['worker_summary']=compact(json.loads((scratch/'zone.json').read_text()))
                except Exception as check: result['worker_receipt_failure']=str(check)[:240]
        try: fill.record_memory(result,'failed','after')
        except Exception as check: result['telemetry_failure']=type(check).__name__+': '+str(check)[:160]
        try: result['input_after']=fill.verify_inputs(root)
        except Exception as check: result['input_recheck_failure']=str(check)[:500]
    result['elapsed_seconds']=time.monotonic()-start
    data=json.dumps(result,sort_keys=True)
    if len(data.encode())>zone.OUTPUT_LIMIT:
        data=json.dumps({'status':'FAILED','mode':mode,'board_acceptance':False,'failure':{'type':'ValueError','message':'output bound'},'elapsed_seconds':time.monotonic()-start})
    print(data,flush=True)
    return 0 if result['status']==STATUSES.get(mode) else 1

def validate_result(result,mode,budget_name='standard'):
    """Structural gate before the controller trusts a payload receipt; host re-verification of files follows separately."""
    if not isinstance(result,dict) or result.get('status')!=STATUSES[mode] or result.get('board_acceptance') is not False or result.get('repair_basis') is not False: raise ValueError('payload status')
    if result.get('budget')!=budget_name: raise ValueError('payload budget differs from the controller budget')
    for key in ('failure','input_recheck_failure','substage_capture_failure','telemetry_failure','worker_receipt_failure'):
        if key in result: raise ValueError('payload failure key present: '+key)
    if result.get('refill_zones_option_used') is not False or result.get('full_board_fill') is not False: raise ValueError('scope flags')
    if result.get('input_before')!=fill.PINS or result.get('input_after')!=fill.PINS: raise ValueError('input identity')
    if not derived.hash_ok(result.get('source_nonfill')) or result.get('identity_key')!=derived.identity_key(result.get('identity',{})): raise ValueError('identity')
    command=result.get('command',{})
    if command.get('status')!='COMPLETE' or command.get('exit_code')!=0: raise ValueError('worker command')
    stages=DERIVE_STAGES if mode=='derive' else EVALUATE_STAGES
    log=result.get('worker_substages',{}).get('zone',{})
    if log.get('complete') is not True or 'error' in log or not zone.parse_stages(b''.join((json.dumps(r)+'\n').encode() for r in log.get('rows',[])),stages)['complete']: raise ValueError('worker substages')
    frames=result.get('memory_telemetry',[])
    if [(f.get('phase'),f.get('point')) for f in frames]!=[('preflight','before'),('preflight','after'),('zone','before'),('zone','after'),('verify','before'),('verify','after')]: raise ValueError('telemetry coverage')
    for frame in frames:
        values=frame.get('values',{})
        if 'error' in frame or values.get('memory.max')!=fill.MEMORY_CAP or values.get('memory.swap.max')!=0: raise ValueError('telemetry values')
        if any(frame.get('events_since_baseline',{}).get(k,0)>0 for k in ('oom','oom_kill')): raise ValueError('OOM event')
    summary=result.get('worker_summary',{})
    if not isinstance(summary,dict) or summary.get('failure') is not None or summary.get('counts')!=zone.COUNTS: raise ValueError('worker summary')
    pairs={a+'<->'+b for a,b in result.get('spec',{}).get('pairs',[])}
    if not pairs or set(summary.get('classification',{}))!=pairs: raise ValueError('classification coverage')
    for phase in ('before','after','reloaded'):
        if set(summary.get('connected',{}).get(phase,{}))!=pairs or any(type(v) is not bool for v in summary['connected'][phase].values()): raise ValueError('pair coverage '+phase)
    for key,row in summary['classification'].items():
        if row.get('class') not in derived.CLASSES or row.get('repair_basis') is not False: raise ValueError('classification row '+key)
        if (row.get('connected_before'),row.get('connected_after'))!=(summary['connected']['before'][key],summary['connected']['reloaded'][key]): raise ValueError('classification flags '+key)
    if mode=='derive':
        if summary.get('fill',{}).get('returned') is not True or sorted(summary['fill'].get('zones',[]))!=result['identity']['zones']: raise ValueError('worker fill')
        if not result.get('nonfill_after')==result['source_nonfill'] or not derived.hash_ok(result.get('manifest_sha256')): raise ValueError('derived semantics')
        parent=result.get('parent') or {};owners=result.get('after_owners',{})
        expected=set(result['identity']['zones'])|set(parent.get('identity',{}).get('zones',[]))|set(parent.get('ancestor_zones',[]))
        if owners.get('zones')!=zone.COUNTS['zone'] or set(owners.get('filled_polygon_by_zone',{}))!=expected: raise ValueError('fill ownership')
    else:
        if result.get('reuse',{}).get('reusable') is not True or not derived.hash_ok(result.get('evaluation_sha256')): raise ValueError('reuse')
    if not isinstance(result.get('elapsed_seconds'),(int,float)) or not 0<=result['elapsed_seconds']<=derived.budget(budget_name)['payload']: raise ValueError('payload deadline')

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--worker': worker(Path(sys.argv[2]))
    elif len(sys.argv)==2 and sys.argv[1] in STATUSES: sys.exit(main(sys.argv[1]))
    else: raise SystemExit('usage: osc_derived_fill_payload.py derive|evaluate')
