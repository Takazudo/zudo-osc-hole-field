"""One disposable selected-zone fill of the frozen core: the +12V In4.Cu zone only.

Container payload (pinned KiCad 10.0.6, pcbnew). Works on a disposable copy
under /scratch; /work is read-only and never written. It answers exactly two
questions: after filling only zone 265b1369 and rebuilding native
connectivity, do C1129.1-U1105.16 and C1131.1-U1106.8 share a connected
component, and through which native items (pads, vias, the selected fill)
and layer transitions. Connectivity is native cluster membership
(CONNECTIVITY_DATA::GetConnectedItems returns the whole cluster in 10.0.6),
never net-name equality or shape intersection; via-inside-fill tests only
corroborate which members bridge layers.
No whole-board DRC, no other zone, no AGND claim, no board acceptance.
"""
import collections
import json
import os
import signal
import shutil
import subprocess
import sys
import time
from pathlib import Path

import osc_frozen_fill as fill
import osc_frozen_topology as topology

TARGET_ZONE='265b1369-38aa-5a3a-b488-eb0aae22e998'
TARGET_NET='+12V'
TARGET_LAYER='In4.Cu'
# Outline from the exact hash-pinned board (boards/osc-core/osc-core.kicad_pcb, mm).
TARGET_OUTLINE=[(104,58),(414,58),(414,296),(358,296),(358,342),(104,342)]
PAIRS=[('C1129.1','U1105.16'),('C1131.1','U1106.8')]
# Pinned structural evidence of the frozen core (handoff ZONE-COMPLEXITY.json / PRESERVED-BOARD-COMPARISON.json).
COUNTS={'segment':123905,'via':9646,'zone':351,'copper_zone':5}
DUPLICATE_UUIDS=('6ad7a8ef-06c4-5daf-8c20-536f50fb0495','7a9f1a78-0122-5c1a-807d-edd14509239d','7bc22643-4022-5e36-b5d2-8117e4041966',
                 '8ed29fa2-46b9-5922-8b00-41d148dd7308','9dd204e2-36b2-5742-bd54-f78d414e5f80','d97e2b87-75be-5022-a172-0d789754bbe1')
PAYLOAD_SECONDS=420
STAGE_CAPS={'prepare':60,'fill':260,'verify':100}
STAGES=('load','identity','before','fill','after','save','reload','verify')
STAGE_GROUP={'load':'prepare','identity':'prepare','before':'prepare','fill':'fill','after':'verify','save':'verify','reload':'verify','verify':'verify'}
CLUSTER_LIMIT=200000
VIA_LIMIT=400
OUTPUT_LIMIT=900000
PCB_LIMIT=64*1024*1024
STATUS='SINGLE_ZONE_CONNECTIVITY_OBSERVATIONS_NOT_ACCEPTANCE'

class StageLog(fill.SubstageLog):
    """Durable substage log for this payload's own stage order; never mutates the shared SUBSTAGES."""
    def __init__(self,path):
        self.phase='zone';self.seq=0;self.size=0;self.last=-float('inf');self.stream=path.open('xb')

def parse_stages(data):
    if len(data)>fill.SUBSTAGE_LIMIT: raise ValueError('substage bound')
    rows=[];previous=-float('inf');expected=[(s,e) for s in STAGES for e in ('start','complete')]
    for line in data.splitlines(keepends=True):
        if not line.endswith(b'\n'): raise ValueError('incomplete substage record')
        row=json.loads(line)
        if not isinstance(row,dict) or set(row)!={'seq','phase','stage','event','monotonic_seconds'}: raise ValueError('substage schema')
        i=len(rows);stamp=row['monotonic_seconds']
        if type(row['seq']) is not int or row['seq']!=i+1 or row['phase']!='zone' or i>=len(expected) or (row['stage'],row['event'])!=expected[i]: raise ValueError('substage order')
        if type(stamp) not in (int,float) or stamp<previous: raise ValueError('substage time')
        rows.append(row);previous=stamp
    return {'rows':rows,'complete':len(rows)==len(expected)}

def capture_stages(result,scratch,require_complete=False):
    path=scratch/'zone-substages.jsonl';target=result.setdefault('worker_substages',{})
    try:
        with path.open('rb') as stream: data=stream.read(fill.SUBSTAGE_LIMIT+1)
        observation={'log_sha256':fill.hashlib.sha256(data).hexdigest(),'bytes':len(data),**parse_stages(data)}
        target['zone']=observation
        if require_complete and not observation['complete']: raise ValueError('worker substage incomplete')
    except Exception as exc:
        entry=target.setdefault('zone',{'rows':[],'complete':False});entry['error']=type(exc).__name__+': '+str(exc)[:240]
        if 'data' in locals():
            prefix=b'';valid={'rows':[],'complete':False}
            for line in data.splitlines(keepends=True):
                try: candidate=parse_stages(prefix+line)
                except Exception: break
                prefix+=line;valid=candidate
            entry.update(rows=valid['rows'],complete=False,valid_prefix_bytes=len(prefix),captured_bytes=len(data))
        raise

def require(condition,message):
    if not condition: raise ValueError(message)

def uid(x): return x.m_Uuid.AsString()

def layer_names(item,layers): return [n for n,l in layers.items() if item.IsOnLayer(l)]

def describe(item,layers,pads):
    kind=type(item).__name__
    row={'type':kind,'uuid':uid(item),'net':item.GetNetname(),'layers':layer_names(item,layers)}
    if kind=='PAD': row['pad']=pads.get(uid(item))
    if kind in ('PCB_TRACK','PCB_ARC'):
        row['start']=[item.GetStart().x,item.GetStart().y];row['end']=[item.GetEnd().x,item.GetEnd().y];row['width']=item.GetWidth()
    elif kind=='PCB_VIA':
        row['at']=[item.GetPosition().x,item.GetPosition().y];row['drill']=item.GetDrillValue()
    elif kind=='ZONE':
        row['rule_area']=bool(item.GetIsRuleArea())
    else:
        row['at']=[item.GetPosition().x,item.GetPosition().y]
    return row

def summarize_cluster(items,layers,pads,target,poly):
    """Compact description of one native cluster (the whole connected component)."""
    counts=collections.Counter();by_layer=collections.Counter();vias=[];zones=[];pad_names=[]
    for item in items:
        kind=type(item).__name__;counts[kind]+=1
        for name in layer_names(item,layers): by_layer[name]+=1
        if kind=='PCB_VIA':
            if len(vias)>=VIA_LIMIT: raise ValueError('via listing bound')
            row=describe(item,layers,pads)
            row['inside_selected_fill']=bool(poly.Contains(item.GetPosition())) if poly is not None else None
            vias.append(row)
        elif kind=='ZONE': zones.append({'uuid':uid(item),'net':item.GetNetname(),'layers':layer_names(item,layers),'selected':uid(item)==TARGET_ZONE})
        elif kind=='PAD': pad_names.append(pads.get(uid(item),uid(item)))
    return {'size':len(items),'counts':dict(counts),'layers':dict(by_layer),'vias':sorted(vias,key=lambda r:r['uuid']),'zones':sorted(zones,key=lambda r:r['uuid']),
            'pads':sorted(pad_names),'selected_zone_member':any(z['selected'] for z in zones)}

def cluster(conn,item):
    items=list(conn.GetConnectedItems(item))
    if len(items)>CLUSTER_LIMIT: raise ValueError('cluster bound')
    return items

def pair_observations(board,pcb,layers,target,previous=None):
    """Native cluster membership per endpoint pad; connected means the partner pad is in the same cluster.

    GetConnectedItems returns the full cluster (connectivity_data.cpp 10.0.6 SearchClusters),
    so one call per endpoint is the traversal; nothing is inferred from net names or shapes.
    """
    conn=board.GetConnectivity();conn.Build(board)
    pads={};names={}
    for f in board.GetFootprints():
        for p in f.Pads():
            name=f.GetReference()+'.'+p.GetNumber();names[uid(p)]=name
            if name in topology.EXPECTED:
                require(name not in pads and uid(p)==topology.EXPECTED[name]['uuid'] and p.GetNetname()==topology.EXPECTED[name]['net'],'pad identity '+name)
                pads[name]=p
    require(set(pads)==set(topology.EXPECTED),'missing pad')
    poly=target.GetFilledPolysList(layers[TARGET_LAYER]) if target.GetFilledPolysList(layers[TARGET_LAYER]).OutlineCount() else None
    rows={}
    for a,b in PAIRS:
        ca,cb=cluster(conn,pads[a]),cluster(conn,pads[b])
        ids_a={uid(x) for x in ca};ids_b={uid(x) for x in cb}
        row={'connected':uid(pads[b]) in ids_a,'symmetric':uid(pads[a]) in ids_b,'cluster_a':summarize_cluster(ca,layers,names,target,poly),'cluster_b':summarize_cluster(cb,layers,names,target,poly)}
        if previous is not None:
            before=previous[a+'<->'+b];side_a={v['uuid'] for v in before['cluster_a']['vias']};side_b={v['uuid'] for v in before['cluster_b']['vias']}
            merged=row['cluster_a']['vias'] if row['connected'] else []
            row['bridging_vias']={'from_a_side':[v for v in merged if v['uuid'] in side_a and v['inside_selected_fill']],
                                  'from_b_side':[v for v in merged if v['uuid'] in side_b and v['inside_selected_fill']],
                                  'new_in_merged_cluster':[v for v in merged if v['uuid'] not in side_a|side_b and v['inside_selected_fill']][:VIA_LIMIT]}
        rows[a+'<->'+b]=row
    conn.RecalculateRatsnest()
    rows['ratsnest']={'unconnected_count':int(conn.GetUnconnectedCount(True))}
    return rows

def zone_state(board,layers):
    rows=[]
    for z in board.Zones():
        counts={n:int(z.GetFilledPolysList(l).OutlineCount()) for n,l in layers.items() if z.IsOnLayer(l)}
        rows.append({'uuid':uid(z),'net':z.GetNetname(),'rule_area':bool(z.GetIsRuleArea()),'filled':bool(z.IsFilled()),'counts':counts})
    require(len(rows)==COUNTS['zone'],'zone count');return rows

def nonselected_fill(rows):
    return sorted((r['uuid'],json.dumps(r['counts'],sort_keys=True)) for r in rows if r['uuid']!=TARGET_ZONE)

def duplicates(board):
    rows=collections.Counter()
    for t in board.GetTracks():
        if uid(t) in DUPLICATE_UUIDS:
            rows[(uid(t),type(t).__name__,t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y,t.GetWidth(),t.GetLayer(),t.GetNetname())]+=1
    require(len(rows)==12 and all(n==1 for n in rows.values()),'duplicate UUID multiplicity/geometry')
    require(collections.Counter(k[0] for k in rows)==collections.Counter({u:2 for u in DUPLICATE_UUIDS}),'duplicate UUID occurrence count')
    return sorted([list(k)+[n] for k,n in rows.items()])

def counts(board):
    c=collections.Counter(type(t).__name__ for t in board.GetTracks())
    result={'segment':c.get('PCB_TRACK',0)+c.get('PCB_ARC',0),'via':c.get('PCB_VIA',0),'zone':len(board.Zones()),
            'copper_zone':sum(1 for z in board.Zones() if not z.GetIsRuleArea())}
    require(result==COUNTS,'pinned counts '+json.dumps(result));return result

def overrides(board,layers):
    n=0
    for f in board.GetFootprints():
        for p in f.Pads(): n+=sum(1 for l in layers.values() if p.IsOnLayer(l) and int(p.GetZoneLayerOverride(l))!=0)
    for t in board.GetTracks():
        if type(t).__name__=='PCB_VIA': n+=sum(1 for l in layers.values() if t.IsOnLayer(l) and int(t.GetZoneLayerOverride(l))!=0)
    return n

def select(board,pcb,layers):
    found=[z for z in board.Zones() if uid(z)==TARGET_ZONE]
    require(len(found)==1,'target cardinality');z=found[0]
    require(z.GetNetname()==TARGET_NET and board.GetLayerName(z.GetLayer())==TARGET_LAYER and not z.GetIsRuleArea(),'target identity')
    outline=z.Outline();require(outline.OutlineCount()==1,'target outline count')
    pts=[(outline.CVertex(i).x,outline.CVertex(i).y) for i in range(outline.VertexCount(0))]
    require(pts==[(pcb.FromMM(x),pcb.FromMM(y)) for x,y in TARGET_OUTLINE],'target outline geometry')
    require(all(int(z.GetFilledPolysList(l).OutlineCount())==0 for l in layers.values() if z.IsOnLayer(l)),'target already filled')
    return z

def worker(scratch):
    stages=StageLog(scratch/'zone-substages.jsonl');result={'board_acceptance':False}
    try:
        import pcbnew
        require(pcbnew.GetBuildVersion()=='10.0.6','pcbnew version')
        layers={n:getattr(pcbnew,n.replace('.','_')) for n in topology.COPPER_LAYERS}
        with stages.stage('load'):
            board=pcbnew.LoadBoard(str(scratch/'input'/'osc-core.kicad_pcb'));require(board is not None,'load failed')
        with stages.stage('identity'):
            result['counts']=counts(board);result['duplicates_before']=duplicates(board);target=select(board,pcbnew,layers)
        with stages.stage('before'):
            zones=zone_state(board,layers)
            result['before']={'zones_nonselected':nonselected_fill(zones),'overrides':overrides(board,layers),'pairs':pair_observations(board,pcbnew,layers,target)}
        with stages.stage('fill'):
            selection=pcbnew.ZONES();selection.append(target);require(len(selection)==1,'selection length')
            started=time.monotonic();ok=pcbnew.ZONE_FILLER(board).Fill(selection,False)
            result['fill']={'returned':bool(ok),'seconds':time.monotonic()-started}
            require(ok is True,'Fill not true')
        with stages.stage('after'):
            zones=zone_state(board,layers)
            selected=[z for z in zones if z['uuid']==TARGET_ZONE][0]
            poly=target.GetFilledPolysList(layers[TARGET_LAYER])
            result['after']={'selected':selected,'selected_vertices':int(poly.TotalVertices()),'selected_holes':int(poly.HoleCount(0)) if poly.OutlineCount() else None,
                'zones_nonselected':nonselected_fill(zones),'overrides':overrides(board,layers),'duplicates':duplicates(board),'counts':counts(board),
                'pairs':pair_observations(board,pcbnew,layers,target,result['before']['pairs'])}
            require(result['after']['zones_nonselected']==result['before']['zones_nonselected'],'nonselected native fill changed')
            require(selected['counts'].get(TARGET_LAYER,0)>=1,'selected zone has no fill')
        with stages.stage('save'):
            out=scratch/'after'/'osc-core.kicad_pcb';pcbnew.SaveBoard(str(out),board);require(out.is_file(),'save failed')
        with stages.stage('reload'):
            board=pcbnew.LoadBoard(str(out));require(board is not None,'reload failed')
        with stages.stage('verify'):
            zones=zone_state(board,layers);target=[z for z in board.Zones() if uid(z)==TARGET_ZONE][0]
            result['reloaded']={'selected':[z for z in zones if z['uuid']==TARGET_ZONE][0],'zones_nonselected':nonselected_fill(zones),'overrides':overrides(board,layers),
                'duplicates':duplicates(board),'counts':counts(board),'pairs':pair_observations(board,pcbnew,layers,target,result['before']['pairs'])}
            require(result['reloaded']['zones_nonselected']==result['before']['zones_nonselected'],'nonselected fill changed on reload')
            require(result['reloaded']['duplicates']==result['duplicates_before']==result['after']['duplicates'],'duplicate identity changed')
            require(result['reloaded']['selected']['counts']==result['after']['selected']['counts'],'selected fill not preserved on reload')
    except Exception as exc:
        result['failure']=type(exc).__name__+': '+str(exc)[:500]
        (scratch/'zone.json').write_text(json.dumps(result,sort_keys=True));raise
    finally: stages.close()
    (scratch/'zone.json').write_text(json.dumps(result,sort_keys=True))

def zone_fill_owners(path):
    """Line-based scan of the pinned serialization: which depth-1 zones carry filled_polygon."""
    owners=collections.Counter();current=None;zones=0
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            if line.startswith('\t(zone'): zones+=1;current='?'
            elif line.startswith('\t)'): current=None
            elif current is not None and line.startswith('\t\t(uuid "'): current=line.split('"')[1]
            elif current is not None and line.startswith('\t\t(filled_polygon'): owners[current]+=1
    return {'zones':zones,'filled_polygon_by_zone':dict(owners)}

def read_rows(log,limit=fill.SUBSTAGE_LIMIT):
    rows=[]
    if not log.is_file(): return rows
    with log.open('rb') as stream: data=stream.read(limit+1)
    for line in data.splitlines(keepends=True):
        if line.endswith(b'\n'):
            try: rows.append(json.loads(line))
            except ValueError: break
    return rows

def run_worker(scratch,deadline,record):
    log=scratch/'zone-substages.jsonl';stdout=scratch/'zone.log'
    argv=[sys.executable,'-B',str(Path(__file__).resolve()),'--worker',str(scratch)]
    record.update(argv=argv,status='STARTED',start_monotonic_seconds=time.monotonic(),deadline_monotonic_seconds=deadline)
    group_start={};current=None;proc=None
    try:
        with stdout.open('xb') as output:
            proc=subprocess.Popen(argv,cwd=scratch,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
            while proc.poll() is None:
                now=time.monotonic()
                if now>=deadline: raise TimeoutError('payload deadline')
                for row in read_rows(log):
                    if row.get('event')=='start':
                        group=STAGE_GROUP.get(row.get('stage'))
                        if group and group not in group_start: group_start[group]=row['monotonic_seconds']
                        current=group
                if current and now-group_start[current]>STAGE_CAPS[current]: raise TimeoutError(current+' stage cap')
                after=scratch/'after'/'osc-core.kicad_pcb'
                if after.exists() and after.stat().st_size>PCB_LIMIT: raise ValueError('output board bound')
                if stdout.stat().st_size>fill.LOG_LIMIT: raise ValueError('worker log bound')
                time.sleep(.1)
        if proc.returncode!=0: raise ValueError('worker exit '+str(proc.returncode))
        record['status']='COMPLETE'
    except BaseException as exc:
        record['status']='FAILED';record['error']=type(exc).__name__+': '+str(exc)[:300]
        if proc is not None and proc.poll() is None: os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=5)
        raise
    finally:
        record['end_monotonic_seconds']=time.monotonic();record['elapsed_seconds']=record['end_monotonic_seconds']-record['start_monotonic_seconds']
        record['exit_code']=proc.returncode if proc is not None else None
        record['stage_group_starts']=group_start
        if stdout.is_file():
            record['log_sha256']=fill.sha(stdout)
            with stdout.open('rb') as s: s.seek(max(0,stdout.stat().st_size-2048));record['log_tail']=s.read(2048).decode('utf-8',errors='replace')

def main():
    start=time.monotonic();deadline=start+PAYLOAD_SECONDS
    root=Path('/work/boards/osc-core');scratch=Path('/scratch/osc-zone')
    result={'status':'FAILED','board_acceptance':False,'full_board_fill':False,'drc':'NOT RUN: whole-board DRC is outside this two-pair diagnostic',
            'target_zone':TARGET_ZONE,'pairs':PAIRS,'limits':'one selected fill; 420 s payload; stage caps prepare 60 / fill 260 / verify 100; no route edits','command':{}}
    try:
        fill.record_memory(result,'preflight','before')
        result['input_before']=fill.verify_inputs(root)
        result['nonfill_input']=fill.semantic_hash(root/'osc-core.kicad_pcb')
        result['input_owners']=zone_fill_owners(root/'osc-core.kicad_pcb')
        require(result['input_owners']=={'zones':COUNTS['zone'],'filled_polygon_by_zone':{}},'input must be unfilled with pinned zone count')
        scratch.mkdir(exist_ok=False);(scratch/'input').mkdir();(scratch/'after').mkdir()
        for name in fill.PINS: shutil.copyfile(root/name,scratch/'input'/name)
        fill.record_memory(result,'preflight','after')
        fill.record_memory(result,'zone','before')
        run_worker(scratch,deadline,result['command'])
        capture_stages(result,scratch,require_complete=True)
        result['worker']=json.loads((scratch/'zone.json').read_text())
        fill.record_memory(result,'zone','after')
        fill.record_memory(result,'verify','before')
        after=scratch/'after'/'osc-core.kicad_pcb'
        result['nonfill_after']=fill.semantic_hash(after)
        require(result['nonfill_input']==result['nonfill_after'],'non-fill semantic change in saved copy')
        result['after_owners']=zone_fill_owners(after)
        require(result['after_owners']['zones']==COUNTS['zone'] and set(result['after_owners']['filled_polygon_by_zone'])=={TARGET_ZONE},'filled_polygon outside selected zone')
        result['scratch_hashes']={'input':fill.sha(scratch/'input'/'osc-core.kicad_pcb'),'after':fill.sha(after)}
        result['input_after']=fill.verify_inputs(root)
        fill.record_memory(result,'verify','after')
        if time.monotonic()>deadline: raise TimeoutError('payload deadline')
        result['status']=STATUS
    except Exception as exc:
        result['failure']={'type':type(exc).__name__,'message':str(exc)[:500]}
        try: capture_stages(result,scratch)
        except Exception as check: result['substage_capture_failure']=type(check).__name__+': '+str(check)[:240]
        if (scratch/'zone.json').is_file():
            try: result['worker']=json.loads((scratch/'zone.json').read_text())
            except Exception as check: result['worker_receipt_failure']=str(check)[:240]
        try: fill.record_memory(result,'failed','after')
        except Exception as check: result['telemetry_failure']=type(check).__name__+': '+str(check)[:160]
        try: result['input_after']=fill.verify_inputs(root)
        except Exception as check: result['input_recheck_failure']=str(check)[:500]
    result['elapsed_seconds']=time.monotonic()-start
    data=json.dumps(result,sort_keys=True)
    if len(data.encode())>OUTPUT_LIMIT:
        worker=result.get('worker',{})
        for key in ('before','after','reloaded'):
            for row in worker.get(key,{}).get('pairs',{}).values():
                if isinstance(row,dict):
                    for side in ('cluster_a','cluster_b'):
                        if side in row: row[side].pop('vias',None);row[side]['vias_omitted_for_bound']=True
        data=json.dumps(result,sort_keys=True)
    if len(data.encode())>OUTPUT_LIMIT:
        data=json.dumps({'status':'FAILED','board_acceptance':False,'failure':{'type':'ValueError','message':'output bound'},'elapsed_seconds':time.monotonic()-start})
    print(data,flush=True)
    return 0 if result['status']==STATUS else 1

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--worker': worker(Path(sys.argv[2]))
    elif len(sys.argv)==1: sys.exit(main())
    else: raise SystemExit('invalid arguments')
