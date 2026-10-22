import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'ci'))
import osc_candidate_check as c
import osc_frozen_fill as fill
import osc_frozen_topology as topology
import osc_single_zone_payload as z
import osc_derived_fill as d
import osc_derived_fill_payload as dp
import osc_single_zone_local as l

IMAGE_ID='sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec'
PLUS12='265b1369-38aa-5a3a-b488-eb0aae22e998'
AGND_IN1='e67a5bc7-b575-52b6-a78a-9c84381053da'
AGND_F='601e02b2-8ccb-5c28-83e5-03789d47fbbd'
AGND_B='e389d344-872d-538e-9bfc-39577adb1686'
PINS={'osc-core.kicad_pcb':'a'*64,'osc-core.kicad_pro':'b'*64,'osc-core.kicad_dru':'c'*64}

def board_text(filled=()):
    zones=''
    for u in (PLUS12,AGND_IN1,AGND_F):
        body='\t\t(filled_polygon\n\t\t\t(pts)\n\t\t)\n' if u in filled else ''
        zones+='\t(zone\n\t\t(net "x")\n\t\t(uuid "%s")\n%s\t)\n'%(u,body)
    return '(kicad_pcb\n\t(version 20250101)\n%s\t(segment\n\t\t(uuid "s1")\n\t)\n)\n'%zones

def write_board(path,filled=()):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(board_text(filled));return c.sha(path)

def derived_dir(root,zones,pins,parent_key=None,image=IMAGE_ID,status=d.MANIFEST_STATUS):
    root.mkdir(parents=True)
    after={'osc-core.kicad_pcb':write_board(root/'after'/'osc-core.kicad_pcb',zones)}
    for name in ('osc-core.kicad_pro','osc-core.kicad_dru'):
        (root/'after'/name).write_text(name);after[name]=c.sha(root/'after'/name)
    pins=dict(pins);pins['osc-core.kicad_pro']=after['osc-core.kicad_pro'];pins['osc-core.kicad_dru']=after['osc-core.kicad_dru']
    ident=d.identity(pins,zones,image,parent_key=parent_key)
    manifest={'status':status,'identity':ident,'identity_key':d.identity_key(ident),'exported':{'after':after},'board_acceptance':False}
    (root/'manifest.json').write_text(json.dumps(manifest))
    return ident,manifest

class Identity(unittest.TestCase):
    def test_key_is_stable_and_sensitive_to_every_component(self):
        base=d.identity(PINS,[PLUS12],IMAGE_ID);key=d.identity_key(base)
        self.assertEqual(key,d.identity_key(json.loads(json.dumps(base))))
        self.assertEqual(d.identity_key(d.identity(PINS,[PLUS12],IMAGE_ID)),key)
        variants=[d.identity({**PINS,'osc-core.kicad_pcb':'d'*64},[PLUS12],IMAGE_ID),d.identity({**PINS,'osc-core.kicad_pro':'d'*64},[PLUS12],IMAGE_ID),
                  d.identity({**PINS,'osc-core.kicad_dru':'d'*64},[PLUS12],IMAGE_ID),d.identity(PINS,[AGND_IN1],IMAGE_ID),d.identity(PINS,[PLUS12,AGND_IN1],IMAGE_ID),
                  d.identity(PINS,[PLUS12],'sha256:'+'f'*64),d.identity(PINS,[PLUS12],IMAGE_ID,parent_key='e'*64),d.identity(PINS,[PLUS12],IMAGE_ID,process='derived-fill/2')]
        keys={d.identity_key(v) for v in variants};self.assertEqual(len(keys),len(variants));self.assertNotIn(key,keys)
        self.assertEqual(d.identity(PINS,[AGND_IN1,PLUS12],IMAGE_ID)['zones'],sorted([AGND_IN1,PLUS12]))
    def test_identity_rejects_bad_components(self):
        for bad in (lambda:d.identity({'osc-core.kicad_pcb':'a'*64},[PLUS12],IMAGE_ID),lambda:d.identity(PINS,[],IMAGE_ID),lambda:d.identity(PINS,['nope'],IMAGE_ID),
                    lambda:d.identity(PINS,[PLUS12,PLUS12],IMAGE_ID),lambda:d.identity(PINS,[PLUS12],'latest'),lambda:d.identity(PINS,[PLUS12],IMAGE_ID,kicad='9.0.0'),
                    lambda:d.identity(PINS,[PLUS12],IMAGE_ID,parent_key='short'),lambda:d.identity(PINS,['%08x-0000-0000-0000-000000000000'%i for i in range(d.ZONE_LIMIT+1)],IMAGE_ID)):
            with self.assertRaises(ValueError):bad()

class Spec(unittest.TestCase):
    def write(self,t,spec):
        p=Path(t)/'spec.json';p.write_text(json.dumps(spec));return p
    def test_valid_spec(self):
        with tempfile.TemporaryDirectory() as t:
            spec=d.load_spec(self.write(t,{'zones':[AGND_IN1],'pairs':[['C1111.2','U1105.12'],['C1129.1','U1105.16']],'note':'next limited diagnostic'}),topology.EXPECTED)
            self.assertEqual(spec['pairs'],[('C1111.2','U1105.12'),('C1129.1','U1105.16')]);self.assertEqual(spec['zones'],[AGND_IN1])
    def test_invalid_specs(self):
        bad=[{'zones':[AGND_IN1],'pairs':[['C1111.2','U1105.16']]},{'zones':[AGND_IN1],'pairs':[['C1111.2','Z9.1']]},{'zones':[],'pairs':[['C1129.1','U1105.16']]},
             {'zones':[AGND_IN1,AGND_IN1],'pairs':[['C1129.1','U1105.16']]},{'zones':['bad'],'pairs':[['C1129.1','U1105.16']]},{'zones':[AGND_IN1],'pairs':[]},
             {'zones':[AGND_IN1],'pairs':[['C1129.1','U1105.16']],'extra':1},{'zones':[AGND_IN1],'pairs':[['C1129.1','U1105.16'],['C1129.1','U1105.16']]},
             {'zones':[AGND_IN1],'pairs':[['C1129.1','C1129.1']]},{'zones':[AGND_IN1],'pairs':[['C1129.1','U1105.16']],'note':'x'*501}]
        with tempfile.TemporaryDirectory() as t:
            for spec in bad:
                with self.assertRaises(ValueError,msg=json.dumps(spec)[:80]):d.load_spec(self.write(t,spec),topology.EXPECTED)

class Classification(unittest.TestCase):
    def zones(self,*rows): return [{'uuid':u,'filled':f,'selected':s} for u,f,s in rows]
    def test_plus12v_pairs_regression_from_candidate_run_2(self):
        # Candidate run 2: both +12V pairs open on the published board, connected after filling only the In4.Cu +12V zone; unconnected 4283 -> 3802.
        for pair in ('C1129.1<->U1105.16','C1131.1<->U1106.8'):
            row=d.classify_pair(False,True,self.zones((PLUS12,True,True)))
            self.assertEqual(row['class'],'CONNECTED_VIA_SELECTED_FILL');self.assertEqual(row['selected_net_zones'],[PLUS12]);self.assertIs(row['repair_basis'],False)
    def test_unfilled_net_zones_block_a_verdict(self):
        row=d.classify_pair(False,False,self.zones((AGND_F,False,False),(AGND_B,False,False),(AGND_IN1,True,True)))
        self.assertEqual(row['class'],'UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN');self.assertEqual(row['unfilled_net_zones'],[AGND_F,AGND_B]);self.assertIn('not a repair basis',row['meaning'])
    def test_other_classes(self):
        self.assertEqual(d.classify_pair(True,True,[])['class'],'CONNECTED_ON_INPUT')
        self.assertEqual(d.classify_pair(False,False,[])['class'],'OPEN_WITHOUT_NET_ZONES')
        self.assertEqual(d.classify_pair(False,False,self.zones((AGND_F,True,True),(AGND_B,True,True),(AGND_IN1,True,True)))['class'],'OPEN_WITH_ALL_NET_ZONES_FILLED')
        with self.assertRaises(ValueError):d.classify_pair(None,False,[])
        self.assertEqual(set(d.CLASSES),{r['class'] for r in (d.classify_pair(True,True,[]),d.classify_pair(False,True,[]),d.classify_pair(False,False,[]),
            d.classify_pair(False,False,self.zones((AGND_F,False,False))),d.classify_pair(False,False,self.zones((AGND_F,True,True))))})

class Reuse(unittest.TestCase):
    def source_hash(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'src.kicad_pcb';write_board(p);return fill.semantic_hash(p)
    def test_normal_reuse_accepted(self):
        with tempfile.TemporaryDirectory() as t:
            ident,_=derived_dir(Path(t)/'d',[PLUS12],PINS)
            v=d.verify_derived(Path(t)/'d',ident,self.source_hash(),fill.semantic_hash)
            self.assertTrue(v['reusable'],v);self.assertEqual(v['checks']['provenance'],'manifest');self.assertEqual(v['identity'],ident)
    def test_stale_cache_rejected_by_real_file_hash(self):
        with tempfile.TemporaryDirectory() as t:
            ident,_=derived_dir(Path(t)/'d',[PLUS12],PINS)
            (Path(t)/'d'/'after'/'osc-core.kicad_pcb').write_text(board_text([PLUS12])+'\n')
            v=d.verify_derived(Path(t)/'d',ident,self.source_hash(),fill.semantic_hash);self.assertFalse(v['reusable']);self.assertIn('stale or altered',v['reason'])
    def test_input_change_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            ident,_=derived_dir(Path(t)/'d',[PLUS12],PINS)
            changed=dict(ident);changed['source']={**ident['source'],'osc-core.kicad_pcb':'9'*64}
            v=d.verify_derived(Path(t)/'d',changed,self.source_hash(),fill.semantic_hash);self.assertFalse(v['reusable']);self.assertIn('identity key mismatch in source',v['reason'])
            v=d.verify_derived(Path(t)/'d',ident,'0'*64,fill.semantic_hash);self.assertFalse(v['reusable']);self.assertIn('non-fill semantics differ',v['reason'])
    def test_fill_ownership_and_zone_set_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            ident,manifest=derived_dir(Path(t)/'d',[PLUS12],PINS)
            other=d.identity(ident['source'],[AGND_IN1],IMAGE_ID)
            v=d.verify_derived(Path(t)/'d',other,self.source_hash(),fill.semantic_hash);self.assertFalse(v['reusable']);self.assertIn('zones',v['reason'])
            (Path(t)/'d'/'after'/'osc-core.kicad_pcb').write_text(board_text([AGND_IN1]));manifest['exported']['after']['osc-core.kicad_pcb']=c.sha(Path(t)/'d'/'after'/'osc-core.kicad_pcb')
            (Path(t)/'d'/'manifest.json').write_text(json.dumps(manifest))
            v=d.verify_derived(Path(t)/'d',ident,self.source_hash(),fill.semantic_hash);self.assertFalse(v['reusable']);self.assertIn('fill ownership',v['reason'])
    def test_missing_or_tampered_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            ident=d.identity(PINS,[PLUS12],IMAGE_ID)
            v=d.verify_derived(Path(t),ident,'0'*64,fill.semantic_hash);self.assertFalse(v['reusable']);self.assertIn('manifest',v['reason'])
            ident,manifest=derived_dir(Path(t)/'d',[PLUS12],PINS);manifest['identity_key']='1'*64;(Path(t)/'d'/'manifest.json').write_text(json.dumps(manifest))
            v=d.verify_derived(Path(t)/'d',ident,self.source_hash(),fill.semantic_hash);self.assertFalse(v['reusable']);self.assertIn('identity key',v['reason'])
    def test_legacy_candidate_needs_sidecar(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/'legacy';root.mkdir()
            after={'osc-core.kicad_pcb':write_board(root/'after'/'osc-core.kicad_pcb',[PLUS12])}
            for name in ('osc-core.kicad_pro','osc-core.kicad_dru'):(root/'after'/name).write_text(name);after[name]=c.sha(root/'after'/name)
            pins={**PINS,'osc-core.kicad_pro':after['osc-core.kicad_pro'],'osc-core.kicad_dru':after['osc-core.kicad_dru']}
            manifest={'status':d.LEGACY_STATUS,'target_zone':PLUS12,'input':pins,'exported':{'before':{},'after':after},'board_acceptance':False}
            (root/'manifest.json').write_text(json.dumps(manifest))
            ident=d.identity(pins,[PLUS12],IMAGE_ID)
            v=d.verify_derived(root,ident,self.source_hash(),fill.semantic_hash);self.assertFalse(v['reusable']);self.assertIn('adoption sidecar',v['reason'])
            sidecar=d.legacy_sidecar(root/'manifest.json',IMAGE_ID,'image id from receipt.json image_identity; pcbnew 10.0.6 required by payload')
            (root/d.SIDECAR).write_text(json.dumps(sidecar))
            v=d.verify_derived(root,ident,self.source_hash(),fill.semantic_hash);self.assertTrue(v['reusable'],v);self.assertTrue(v['checks']['provenance'].startswith('legacy-sidecar:'))
            (root/'manifest.json').write_text(json.dumps(manifest)+'\n')
            v=d.verify_derived(root,ident,self.source_hash(),fill.semantic_hash);self.assertFalse(v['reusable']);self.assertIn('sidecar manifest hash',v['reason'])
            with self.assertRaises(ValueError):d.legacy_sidecar(root/'manifest.json',IMAGE_ID,'short')

class PayloadHelpers(unittest.TestCase):
    def test_net_zones_and_nonselected(self):
        rows=[{'uuid':AGND_F,'net':'AGND','rule_area':False,'layers':['F.Cu'],'counts':{'F.Cu':0}},{'uuid':AGND_IN1,'net':'AGND','rule_area':False,'layers':['In1.Cu'],'counts':{'In1.Cu':1}},
              {'uuid':'k','net':'','rule_area':True,'layers':['F.Cu'],'counts':{'F.Cu':0}},{'uuid':PLUS12,'net':'+12V','rule_area':False,'layers':['In4.Cu'],'counts':{'In4.Cu':0}}]
        nz=dp.net_zones(rows,'AGND',{AGND_IN1});self.assertEqual([(r['uuid'],r['filled'],r['selected']) for r in nz],[(AGND_F,False,False),(AGND_IN1,True,True)])
        self.assertEqual([u for u,_ in dp.nonselected_fill(rows,{AGND_IN1})],[AGND_F,'k',PLUS12])
        cls=dp.classify([('C1111.2','U1105.12'),('C1129.1','U1105.16')],{'C1111.2<->U1105.12':{'connected':False},'C1129.1<->U1105.16':{'connected':False}},
                        {'C1111.2<->U1105.12':{'connected':False},'C1129.1<->U1105.16':{'connected':False}},rows,{AGND_IN1})
        self.assertEqual(cls['C1111.2<->U1105.12']['class'],'UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN');self.assertEqual(cls['C1129.1<->U1105.16']['class'],'UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN')
        self.assertEqual(cls['C1129.1<->U1105.16']['unfilled_net_zones'],[PLUS12])
    def test_summarize_cluster_multi_zone(self):
        from types import SimpleNamespace as NS
        layers={'F.Cu':0,'In1.Cu':1,'In4.Cu':10}
        def item(kind,u,net,on,pos=(1,2)):
            return type(kind,(),{'m_Uuid':NS(AsString=lambda:u),'GetNetname':lambda self:net,'IsOnLayer':lambda self,l:l in on,'GetPosition':lambda self:NS(x=pos[0],y=pos[1]),
                                 'GetDrillValue':lambda self:3,'GetIsRuleArea':lambda self:False})()
        polys=[(AGND_IN1,'In1.Cu',NS(Contains=lambda p:p.x==1)),(PLUS12,'In4.Cu',NS(Contains=lambda p:True))]
        items=[item('PAD','p1','AGND',[0]),item('PCB_VIA','v1','AGND',[0,1,10]),item('PCB_VIA','v2','AGND',[0,1,10],(9,9)),item('ZONE',AGND_IN1,'AGND',[1]),item('ZONE',AGND_F,'AGND',[0])]
        s=dp.summarize_cluster(items,layers,{'p1':'C1111.2'},{AGND_IN1},polys)
        self.assertTrue(s['selected_zone_member']);self.assertEqual([(v['uuid'],v['inside_selected_fill']) for v in s['vias']],[('v1',[PLUS12,AGND_IN1]),('v2',[PLUS12])])
        self.assertEqual([(zz['uuid'],zz['selected']) for zz in s['zones']],sorted([(AGND_IN1,True),(AGND_F,False)]))
        self.assertIsNone(dp.summarize_cluster(items[:1],layers,{},set(),[])['vias'] or None)
    def test_stage_tables_and_caps(self):
        self.assertEqual(set(dp.EVALUATE_GROUP),set(dp.EVALUATE_STAGES));self.assertEqual(set(dp.EVALUATE_GROUP.values()),set(dp.EVALUATE_CAPS))
        self.assertLessEqual(sum(dp.EVALUATE_CAPS.values()),dp.PAYLOAD_SECONDS-dp.WORKER_RESERVE);self.assertEqual(sum(dp.DERIVE_CAPS.values()),dp.PAYLOAD_SECONDS)
        rows=b''.join((json.dumps({'seq':i+1,'phase':'zone','stage':s,'event':e,'monotonic_seconds':float(i)})+'\n').encode() for i,(s,e) in enumerate((s,e) for s in dp.EVALUATE_STAGES for e in ('start','complete')))
        self.assertTrue(z.parse_stages(rows,dp.EVALUATE_STAGES)['complete'])
        with self.assertRaises(ValueError):z.parse_stages(rows)
    def test_run_worker_uses_given_script_and_caps(self):
        with tempfile.TemporaryDirectory() as t:
            scratch=Path(t);(scratch/'zone-substages.jsonl').write_text(json.dumps({'seq':1,'phase':'zone','stage':'load_derived','event':'start','monotonic_seconds':0.0})+'\n')
            record={};seen={}
            class Proc:
                pid=os.getpid();returncode=None
                def poll(self): return None
                def wait(self,timeout=None): self.returncode=-9
            def popen(argv,**kw): seen['argv']=argv;return Proc()
            with patch.object(z.subprocess,'Popen',side_effect=popen),patch.object(z.os,'killpg'),patch.object(z.time,'monotonic',side_effect=[10.0,300.0,300.0,300.0,300.0,300.0]),patch.object(z.time,'sleep'):
                with self.assertRaises(TimeoutError) as caught: z.run_worker(scratch,10000.0,record,script=dp.__file__,stage_group=dp.EVALUATE_GROUP,stage_caps=dp.EVALUATE_CAPS)
            self.assertIn('verify stage cap',str(caught.exception));self.assertEqual(Path(seen['argv'][2]).name,'osc_derived_fill_payload.py');self.assertEqual(seen['argv'][3],'--worker')

def full_table(filled):
    nets={PLUS12:'+12V',AGND_IN1:'AGND',AGND_F:'AGND',AGND_B:'AGND'}
    rows=[{'uuid':u,'net':n,'rule_area':False,'layers':['In1.Cu'],'counts':{'In1.Cu':1 if u in filled else 0}} for u,n in nets.items()]
    rows+=[{'uuid':'%08x-0000-4000-8000-000000000000'%i,'net':'','rule_area':True,'layers':['F.Cu'],'counts':{'F.Cu':0}} for i in range(z.COUNTS['zone']-len(nets))]
    return sorted(rows,key=lambda r:r['uuid'])

def good_detail(mode,zones=(AGND_IN1,),pairs=(('C1111.2','U1105.12'),('C1129.1','U1105.16')),classes=('UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN','UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN')):
    stages=dp.DERIVE_STAGES if mode=='derive' else dp.EVALUATE_STAGES
    rows=[{'seq':i+1,'phase':'zone','stage':s,'event':e,'monotonic_seconds':float(i)} for i,(s,e) in enumerate((s,e) for s in stages for e in ('start','complete'))]
    frame=lambda p,q:{'phase':p,'point':q,'values':{'memory.max':fill.MEMORY_CAP,'memory.swap.max':0,'memory.peak':1},'events_since_baseline':{'oom':0,'oom_kill':0}}
    ident=d.identity(fill.PINS,list(zones),IMAGE_ID)
    keys=[a+'<->'+b for a,b in pairs]
    classification={k:{'class':cls,'connected_before':False,'connected_after':cls.startswith('CONNECTED'),'net_zones':[PLUS12] if 'U1105.16' in k else [AGND_F,AGND_B,AGND_IN1],
                       'unfilled_net_zones':([] if cls.startswith('CONNECTED') or cls=='OPEN_WITH_ALL_NET_ZONES_FILLED' else ([PLUS12] if 'U1105.16' in k else [AGND_F,AGND_B])),'selected_net_zones':[],'repair_basis':False} for k,cls in zip(keys,classes)}
    connected={phase:{k:classification[k]['connected_after'] if phase!='before' else False for k in keys} for phase in ('before','after','reloaded')}
    detail={'status':dp.STATUSES[mode],'mode':mode,'budget':'standard','board_acceptance':False,'repair_basis':False,'full_board_fill':False,'refill_zones_option_used':False,'input_before':dict(fill.PINS),'input_after':dict(fill.PINS),
            'source_nonfill':'a'*64,'identity':ident,'identity_key':d.identity_key(ident),'tooling_sha':'t'*40,'spec':{'zones':list(zones),'pairs':[list(p) for p in pairs],'note':''},
            'command':{'status':'COMPLETE','exit_code':0},'worker_substages':{'zone':{'complete':True,'rows':rows}},'memory_telemetry':[frame(p,q) for p in ('preflight','zone','verify') for q in ('before','after')],
            'worker_summary':{'fill':{'returned':True,'seconds':70.0,'zones':list(zones)} if mode=='derive' else None,'counts':dict(z.COUNTS),'connected':connected,'unconnected_count':{'before':4283,'after':3802,'reloaded':3802},
                              'classification':classification,'failure':None},'exported_receipts':{'zone.json':'1'*64,'zone-substages.jsonl':'2'*64},'elapsed_seconds':200}
    if mode=='derive': detail.update(nonfill_after='a'*64,after_owners={'zones':351,'filled_polygon_by_zone':{u:1 for u in zones}},manifest_sha256='3'*64)
    else: detail.update(reuse={'reusable':True,'reason':'all recomputed checks match'},evaluation_sha256='4'*64)
    return detail

class PayloadValidation(unittest.TestCase):
    def test_good_results(self):
        dp.validate_result(good_detail('derive'),'derive');dp.validate_result(good_detail('evaluate'),'evaluate')
        dp.validate_result(good_detail('derive',(PLUS12,),(('C1129.1','U1105.16'),('C1131.1','U1106.8')),('CONNECTED_VIA_SELECTED_FILL','CONNECTED_VIA_SELECTED_FILL')),'derive')
    def test_regressions_are_refused(self):
        cases={'mid_failure':lambda r:r.update(failure={'type':'ValueError','message':'Fill not true'}),'timeout':lambda r:r.update(elapsed_seconds=421),
               'stage_cap_failed_command':lambda r:r['command'].update(status='FAILED',error='TimeoutError: fill stage cap'),'incomplete_substages':lambda r:r['worker_substages']['zone']['rows'].pop(),
               'incomplete_receipt':lambda r:r.update(worker_receipt_failure='Expecting value'),'rejected_status':lambda r:r.update(status=dp.REJECTED_STATUS),
               'oom':lambda r:r['memory_telemetry'][3]['events_since_baseline'].update(oom_kill=1),'class_flags_disagree':lambda r:r['worker_summary']['classification']['C1111.2<->U1105.12'].update(connected_after=True),
               'unknown_class':lambda r:r['worker_summary']['classification']['C1111.2<->U1105.12'].update({'class':'CONNECTED'}),'repair_basis_claimed':lambda r:r['worker_summary']['classification']['C1111.2<->U1105.12'].update(repair_basis=True),
               'identity_key_tampered':lambda r:r.update(identity_key='0'*64),'ownership_outside_selection':lambda r:r['after_owners']['filled_polygon_by_zone'].update({PLUS12:1}),
               'semantic_change':lambda r:r.update(nonfill_after='b'*64),'fill_zones_differ':lambda r:r['worker_summary']['fill'].update(zones=[PLUS12]),'counts_differ':lambda r:r['worker_summary'].update(counts={}),
               'pair_missing':lambda r:r['worker_summary']['connected']['reloaded'].pop('C1129.1<->U1105.16'),'full_board_claimed':lambda r:r.update(full_board_fill=True)}
        for name,mutate in cases.items():
            r=good_detail('derive');mutate(r)
            with self.assertRaises(ValueError,msg=name):dp.validate_result(r,'derive')
        r=good_detail('evaluate');r['reuse']={'reusable':False,'reason':'stale'}
        with self.assertRaises(ValueError):dp.validate_result(r,'evaluate')
        with self.assertRaises(ValueError):dp.validate_result(good_detail('evaluate'),'derive')
    def test_budget_echo_and_deadline_follow_the_profile(self):
        probe=good_detail('derive',(AGND_F,));probe.update(budget='fill-520-probe',elapsed_seconds=700)
        dp.validate_result(probe,'derive','fill-520-probe')
        with self.assertRaises(ValueError):dp.validate_result(probe,'derive')                      # controller ran the standard chain
        with self.assertRaises(ValueError):dp.validate_result(good_detail('derive'),'derive','fill-520-probe')   # payload echoed the standard chain
        probe['elapsed_seconds']=761
        with self.assertRaises(ValueError):dp.validate_result(probe,'derive','fill-520-probe')
        missing=good_detail('derive');del missing['budget']
        with self.assertRaises(ValueError):dp.validate_result(missing,'derive')
    def test_compact_summary_drops_cluster_listings(self):
        worker={'fill':{'returned':True,'seconds':1,'zones':[AGND_IN1]},'counts':dict(z.COUNTS),'before':{'pairs':{'a<->b':{'connected':False,'cluster_a':{'vias':[1]*500}},'ratsnest':{'unconnected_count':4283}}},
                'after':{'zones':[{'uuid':AGND_IN1}],'pairs':{'a<->b':{'connected':True},'ratsnest':{'unconnected_count':4000}}},'reloaded':{'pairs':{'a<->b':{'connected':True},'ratsnest':{'unconnected_count':4000}}},'classification':{'a<->b':{'class':'x'}}}
        s=dp.compact(worker);self.assertEqual(s['connected'],{'before':{'a<->b':False},'after':{'a<->b':True},'reloaded':{'a<->b':True}});self.assertEqual(s['unconnected_count']['before'],4283)
        self.assertNotIn('cluster_a',json.dumps(s));self.assertIsNone(s['failure'])

class Budget(unittest.TestCase):
    def test_profiles_nest_and_match_the_approval(self):
        s=d.budget('standard');p=d.budget('fill-520-probe')
        self.assertEqual((s['payload'],s['stage_caps'],s['attach'],s['wrapper'],s['controller'],s['outer_stop'],s['launch_reserve'],s['worker_deadline']),(420,{'prepare':60,'fill':260,'verify':100},430,450,590,600,497,380))
        self.assertEqual((p['payload'],p['stage_caps'],p['attach'],p['wrapper'],p['controller'],p['outer_stop'],p['post_stop_cleanup']),(760,{'prepare':60,'fill':520,'verify':100},780,800,890,900,60))
        self.assertEqual((p['launch_reserve'],p['worker_deadline'],p['heavy_guard_max_run'],p['pcb_limit'],p['modes'],p['zones']),(847,720,1020,128*1024*1024,('derive',),[AGND_F]))
        self.assertIsNone(s['zones']);self.assertEqual(set(s['modes']),set(l.MODES))
        for name in d.BUDGETS: self.assertEqual(d.budget(name)['name'],name)
    def test_broken_chains_are_defects(self):
        base=d.BUDGETS['fill-520-probe']
        breaks={'fill cap past worker deadline':{'stage_caps':{'prepare':60,'fill':721,'verify':100}},'attach below payload':{'attach':769},'wrapper below attach':{'wrapper':796},
                'controller without setup window':{'controller':886},'outer stop not above controller':{'outer_stop':890},'guard cap too short':{'heavy_guard_max_run':1019},
                'board bound beyond tmpfs':{'pcb_limit':256*1024*1024},'bad zone':{'zones':['nope']},'empty zones':{'zones':[]}}
        for name,over in breaks.items():
            with patch.dict(d.BUDGETS,{'broken':{**base,**over}}):
                with self.assertRaises(ValueError,msg=name):d.budget('broken')
        with self.assertRaises(ValueError):d.budget('unknown')
    def test_allowance(self):
        p=d.budget('fill-520-probe');s=d.budget('standard')
        d.budget_allows(p,'derive',[AGND_F]);d.budget_allows(s,'derive',[AGND_F]);d.budget_allows(s,'evaluate',[AGND_IN1,PLUS12]);d.budget_allows(s,'zone',None)
        for mode,zones in (('evaluate',[AGND_F]),('zone',None),('derive',[AGND_IN1]),('derive',[AGND_F,AGND_B]),('derive',None)):
            with self.assertRaises(ValueError,msg=mode):d.budget_allows(p,mode,zones)
        d.budget_allows(s,'derive',[AGND_F],chained=True)
        with self.assertRaises(ValueError):d.budget_allows(p,'derive',[AGND_F],chained=True)

class ControllerDerived(unittest.TestCase):
    def spec_file(self,t,**over):
        spec={'zones':[AGND_IN1],'pairs':[['C1111.2','U1105.12'],['C1129.1','U1105.16']],'note':'test'};spec.update(over)
        p=Path(t)/'spec.json';p.write_text(json.dumps(spec));return p
    def test_extra_mounts_with_spec(self):
        args=['run','--volume','/src:/work:ro',c.IMAGE,'x']
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'out';out.mkdir();spec=Path(t)/'spec';spec.mkdir()
            with self.assertRaises(ValueError):l.extra_mounts(args,str(out),None,str(spec))
            (spec/'spec.json').write_text('{}');(spec/'context.json').write_text('{}')
            got=l.extra_mounts(args,str(out),None,str(spec));self.assertIn(str(spec)+':/spec:ro',got);self.assertLess(got.index(str(spec)+':/spec:ro'),got.index(c.IMAGE))
    def test_argument_validation_has_no_side_effects(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'out';before=dict(c.PINS);spec=self.spec_file(t)
            base=['run',str(Path(t)/'src'),str(out),'--state',str(Path(t)/'s'),'--authorization','offline unit test authorization note']
            for extra in (['--payload','derive','--output',str(Path(t)/'o')],['--payload','evaluate','--output',str(Path(t)/'o'),'--spec',str(spec)],
                          ['--payload','zone','--spec',str(spec)],['--payload','derive','--spec',str(spec)]):
                with self.assertRaises(ValueError,msg=' '.join(extra)):l.run(l.parse(base+extra))
                self.assertFalse(out.exists());self.assertFalse((Path(t)/'o').exists())
            bad=self.spec_file(t,pairs=[['C1111.2','U1105.16']])
            with self.assertRaises(ValueError):l.run(l.parse(base+['--payload','derive','--output',str(Path(t)/'o'),'--spec',str(bad)]))
            self.assertFalse(out.exists());self.assertEqual(c.PINS,before)
    def test_probe_budget_arguments_fail_closed(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'out';probe=Path(t)/'probe.json';probe.write_text(self.spec_file(t,zones=[AGND_F]).read_text());in1=self.spec_file(t)
            base=['run',str(Path(t)/'src'),str(out),'--state',str(Path(t)/'s'),'--authorization','offline unit test authorization note','--payload','derive','--output',str(Path(t)/'o')]
            clean={k:v for k,v in os.environ.items() if k not in ('GITHUB_ACTIONS','RUNNER_ENVIRONMENT','CI','DOCKER_HOST','DOCKER_CONTEXT','HEAVY_GUARD_HELD','OSC_LOCAL_ADAPTER','OSC_OUTER_STOP_SECONDS')}
            cases=(({},['--budget','fill-520-probe','--spec',str(probe)],'wrapper did not confirm'),({'OSC_OUTER_STOP_SECONDS':'600'},['--budget','fill-520-probe','--spec',str(probe)],'differs from budget'),
                   ({'OSC_OUTER_STOP_SECONDS':'900'},['--budget','fill-520-probe','--spec',str(in1)],'different zone set'),({'OSC_OUTER_STOP_SECONDS':'900'},['--budget','standard','--spec',str(probe)],'differs from budget'),
                   ({'OSC_OUTER_STOP_SECONDS':'900'},['--budget','fill-520-probe','--spec',str(probe),'--candidate',str(Path(t)/'parent')],'chained derivation'))
            (Path(t)/'parent').mkdir()
            for extra_env,extra,message in cases:
                with patch.dict(os.environ,{**clean,**extra_env},clear=True):
                    with self.assertRaises(ValueError) as caught:l.run(l.parse(base+extra))
                    self.assertIn(message,str(caught.exception))
                self.assertFalse(out.exists(),message);self.assertFalse((Path(t)/'o').exists(),message)
            with self.assertRaises(SystemExit),contextlib.redirect_stderr(io.StringIO()):l.parse(base+['--budget','fill-1000'])
    def test_probe_budget_receipt_records_the_whole_chain(self):
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'src';source.mkdir();out=Path(t)/'out';spec=self.spec_file(t,zones=[AGND_F])
            args=l.parse(['run',str(source),str(out),'--state',str(Path(t)/'s'),'--authorization','offline unit test authorization note','--payload','derive','--output',str(Path(t)/'o'),'--spec',str(spec),'--budget','fill-520-probe'])
            environment={k:v for k,v in os.environ.items() if k not in ('GITHUB_ACTIONS','RUNNER_ENVIRONMENT','CI','DOCKER_HOST','DOCKER_CONTEXT','HEAVY_GUARD_HELD','OSC_LOCAL_ADAPTER')};environment.update(TOOLING_SHA='a'*40,OSC_OUTER_STOP_SECONDS='900')
            with patch.dict(os.environ,environment,clear=True),patch.object(c,'run_command') as runner,contextlib.redirect_stdout(io.StringIO()):
                code=l.run(args)
            receipt=json.loads((out/'receipt.json').read_text());policy=receipt['deadline_policy']
            self.assertEqual(code,1);self.assertIn('heavy-guard',receipt['error']);runner.assert_not_called()
            self.assertEqual({k:policy[k] for k in ('budget','total_seconds','outer_stop_seconds','outer_stop_confirmed_by_wrapper','payload_seconds','attach_seconds','wrapper_seconds','launch_reserve_seconds','worker_deadline_seconds','post_stop_cleanup_seconds','heavy_guard_max_run_seconds','pcb_limit_bytes','stage_caps')},
                             {'budget':'fill-520-probe','total_seconds':890,'outer_stop_seconds':900,'outer_stop_confirmed_by_wrapper':True,'payload_seconds':760,'attach_seconds':780,'wrapper_seconds':800,'launch_reserve_seconds':847,'worker_deadline_seconds':720,
                              'post_stop_cleanup_seconds':60,'heavy_guard_max_run_seconds':1020,'pcb_limit_bytes':128*1024*1024,'stage_caps':{'prepare':60,'fill':520,'verify':100}})
            self.assertAlmostEqual(policy['deadline_monotonic']-policy['started_monotonic'],890,places=3);self.assertEqual(receipt['spec']['zones'],[AGND_F]);self.assertIs(receipt['repair_basis'],False)
    def test_derive_run_fails_closed_before_commands_and_records_spec(self):
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'src';source.mkdir();out=Path(t)/'out';spec=self.spec_file(t)
            args=l.parse(['run',str(source),str(out),'--state',str(Path(t)/'s'),'--authorization','offline unit test authorization note','--payload','derive','--output',str(Path(t)/'o'),'--spec',str(spec)])
            environment={k:v for k,v in os.environ.items() if k not in ('GITHUB_ACTIONS','RUNNER_ENVIRONMENT','CI','DOCKER_HOST','DOCKER_CONTEXT','HEAVY_GUARD_HELD','OSC_LOCAL_ADAPTER')};environment['TOOLING_SHA']='a'*40
            with patch.dict(os.environ,environment,clear=True),patch.object(c,'run_command') as runner,contextlib.redirect_stdout(io.StringIO()):
                code=l.run(args)
            receipt=json.loads((out/'receipt.json').read_text())
            self.assertEqual(code,1);self.assertIn('heavy-guard',receipt['error']);runner.assert_not_called()
            self.assertEqual(receipt['spec']['zones'],[AGND_IN1]);self.assertIsNone(receipt['target_zone']);self.assertIs(receipt['repair_basis'],False);self.assertTrue(receipt['drc'].startswith('NOT RUN: '))
    def test_adopt_legacy_writes_sidecar_once(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/'cand';root.mkdir();(root/'after').mkdir()
            manifest={'status':d.LEGACY_STATUS,'target_zone':PLUS12,'input':dict(fill.PINS),'exported':{'after':{'osc-core.kicad_pcb':'9'*64}},'board_acceptance':False};(root/'manifest.json').write_text(json.dumps(manifest))
            def receipt_for(manifest_sha):
                detail={'status':d.LEGACY_STATUS,'manifest_sha256':manifest_sha,'exported':manifest['exported']}
                return {'status':d.LEGACY_STATUS,'image':c.IMAGE,'image_identity':{'id':IMAGE_ID,'repo_digests':[c.IMAGE]},'tooling_sha':'1'*40,'tool_hashes':{},
                        'commands':[{'argv':['git','rev-parse','HEAD'],'output':'x'},{'argv':['bash','scripts/kicad/run.sh','python3','-B','/analysis/osc_zone_drc_payload.py','candidate'],'output':json.dumps(detail)}]}
            receipt=Path(t)/'receipt.json';receipt.write_text(json.dumps(receipt_for('0'*64)))
            args=l.parse(['adopt-legacy',str(root),str(receipt),'--attestation','image id and pcbnew 10.0.6 from the recorded candidate run 2 receipt'])
            with self.assertRaises(ValueError):l.adopt_legacy(args)   # receipt describes a different candidate directory
            receipt.write_text(json.dumps(receipt_for(c.sha(root/'manifest.json'))))
            with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(l.adopt_legacy(args),0)
            side=json.loads((root/d.SIDECAR).read_text());self.assertEqual(side['identity']['zones'],[PLUS12]);self.assertEqual(side['identity']['image_id'],IMAGE_ID);self.assertEqual(side['manifest_sha256'],c.sha(root/'manifest.json'))
            with self.assertRaises(FileExistsError):l.adopt_legacy(args)
            (root/d.SIDECAR).unlink();receipt.write_text(json.dumps({'status':'FAILED','image':c.IMAGE,'image_identity':{'id':IMAGE_ID,'repo_digests':[c.IMAGE]}}))
            with self.assertRaises(ValueError):l.adopt_legacy(args)
    def derive_fixture(self,t):
        root=Path(t)/'root';src=root/'boards'/'osc-core';write_board(src/'osc-core.kicad_pcb')
        (src/'osc-core.kicad_pro').write_text('pro');(src/'osc-core.kicad_dru').write_text('dru')
        pins={n:c.sha(src/n) for n in d.BOARD_FILES}
        output=Path(t)/'output';output.mkdir();(output/'after').mkdir()
        write_board(output/'after'/'osc-core.kicad_pcb',[AGND_IN1])
        for name in ('osc-core.kicad_pro','osc-core.kicad_dru'):(output/'after'/name).write_text((src/name).read_text())
        exported={n:c.sha(output/'after'/n) for n in d.BOARD_FILES}
        table=full_table({AGND_IN1})
        pairs={'C1111.2<->U1105.12':{'connected':False},'C1129.1<->U1105.16':{'connected':False},'ratsnest':{'unconnected_count':1}}
        selected=[r for r in table if r['uuid']==AGND_IN1]
        worker={'failure':None,'counts':dict(z.COUNTS),'before':{'pairs':pairs},'after':{'pairs':pairs,'zones':selected},'reloaded':{'pairs':pairs,'zones':selected,'zone_table':table}}
        (output/'zone.json').write_text(json.dumps(worker));(output/'zone-substages.jsonl').write_text('')
        receipts={n:c.sha(output/n) for n in ('zone.json','zone-substages.jsonl')}
        detail=good_detail('derive');detail['exported_receipts']=receipts
        ident=d.identity(pins,[AGND_IN1],IMAGE_ID);detail['identity']=ident;detail['identity_key']=d.identity_key(ident)
        detail['source_nonfill']=fill.semantic_hash(src/'osc-core.kicad_pcb');detail['nonfill_after']=detail['source_nonfill']
        manifest={'status':d.MANIFEST_STATUS,'identity':ident,'identity_key':detail['identity_key'],'exported':{'after':exported},'classification':detail['worker_summary']['classification'],'board_acceptance':False,'budget':'standard','stage_caps':d.budget('standard')['stage_caps']}
        (output/'manifest.json').write_text(json.dumps(manifest));detail['manifest_sha256']=c.sha(output/'manifest.json')
        receipt={'tooling_sha':'t'*40,'image_identity':{'id':IMAGE_ID},'spec':{'zones':[AGND_IN1],'pairs':[['C1111.2','U1105.12'],['C1129.1','U1105.16']]}}
        return root,output,detail,receipt,pins,manifest
    def test_verify_derived_output_recomputes_everything(self):
        with tempfile.TemporaryDirectory() as t:
            root,output,detail,receipt,pins,manifest=self.derive_fixture(t)
            with patch.dict(fill.PINS,pins):
                v=l.verify_derived_output('derive',detail,output,None,root,receipt)
                self.assertTrue(v['reuse']['reusable']);self.assertEqual(v['recomputed_connectivity']['C1111.2<->U1105.12'],{'before':False,'after':False})
                tampered=json.loads(json.dumps(detail));tampered['worker_summary']['classification']['C1111.2<->U1105.12'].update({'class':'CONNECTED_VIA_SELECTED_FILL','connected_after':True})
                manifest['classification']=tampered['worker_summary']['classification'];(output/'manifest.json').write_text(json.dumps(manifest));tampered['manifest_sha256']=c.sha(output/'manifest.json')
                with self.assertRaises(ValueError):l.verify_derived_output('derive',tampered,output,None,root,receipt)
                # Class contradicts consistent flags: both phases open in zone.json, class claims a connection.
                lying=json.loads(json.dumps(detail));lying['worker_summary']['classification']['C1111.2<->U1105.12'].update({'class':'CONNECTED_VIA_SELECTED_FILL'})
                manifest['classification']=lying['worker_summary']['classification'];(output/'manifest.json').write_text(json.dumps(manifest));lying['manifest_sha256']=c.sha(output/'manifest.json')
                with self.assertRaises(ValueError) as caught:l.verify_derived_output('derive',lying,output,None,root,receipt)
                self.assertIn('classification class',str(caught.exception))
                (output/'after'/'osc-core.kicad_pcb').write_text(board_text([AGND_IN1])+'\n')
                manifest['classification']=detail['worker_summary']['classification'];(output/'manifest.json').write_text(json.dumps(manifest));detail['manifest_sha256']=c.sha(output/'manifest.json')
                with self.assertRaises(ValueError):l.verify_derived_output('derive',detail,output,None,root,receipt)

if __name__=='__main__':unittest.main()


class PayloadIntegration(unittest.TestCase):
    """Parent-side payload flow with a fake worker: spec/context, source checks, parent and reuse verification, export, manifest, validation, host verification."""
    ZONES=[r['uuid'] for r in full_table(set())]
    def text(self,filled=()):
        body=''.join('\t(zone\n\t\t(net "x")\n\t\t(uuid "%s")\n%s\t)\n'%(u,'\t\t(filled_polygon\n\t\t\t(pts)\n\t\t)\n' if u in filled else '') for u in self.ZONES)
        return '(kicad_pcb\n\t(version 20250101)\n%s)\n'%body
    def setup(self,t,budget='standard'):
        root=Path(t)/'work';(root).mkdir();(root/'osc-core.kicad_pcb').write_text(self.text());(root/'osc-core.kicad_pro').write_text('pro');(root/'osc-core.kicad_dru').write_text('dru')
        pins={n:c.sha(root/n) for n in d.BOARD_FILES}
        spec_dir=Path(t)/'spec';spec_dir.mkdir()
        (spec_dir/'spec.json').write_text(json.dumps({'zones':[AGND_IN1],'pairs':[['C1111.2','U1105.12'],['C1129.1','U1105.16']],'note':'fake worker'}))
        (spec_dir/'context.json').write_text(json.dumps({'image_id':IMAGE_ID,'kicad':'10.0.6','source_pins':pins,'process':d.PROCESS_VERSION,'tooling_sha':'t'*40,'budget':budget}))
        return root,pins,spec_dir
    def fake_worker(self,connected_after=False,fail=False):
        self.supervision=[]
        def run_worker(scratch,deadline,record,script=None,stage_group=None,stage_caps=None,pcb_limit=None):
            self.supervision.append({'stage_caps':stage_caps,'pcb_limit':pcb_limit,'deadline':deadline})
            spec=json.loads((scratch/'spec.json').read_text());stages=dp.DERIVE_STAGES if spec['mode']=='derive' else dp.EVALUATE_STAGES
            log=z.StageLog(scratch/'zone-substages.jsonl')
            for s in stages:
                with log.stage(s):
                    if s=='save' and spec['mode']=='derive': (scratch/'after'/'osc-core.kicad_pcb').write_text(self.text(set(spec['input_zones'])|set(spec['zones'])))
                    if fail and s=='fill': log.close();record.update(status='FAILED',error='TimeoutError: fill stage cap',exit_code=-9);raise TimeoutError('fill stage cap')
            log.close()
            table=full_table(set(spec['zones'])|set(spec['input_zones']))
            pairs=lambda on:{'C1111.2<->U1105.12':{'connected':on,'cluster_a':{'vias':[]}},'C1129.1<->U1105.16':{'connected':False,'cluster_a':{'vias':[]}},'ratsnest':{'unconnected_count':4283 if not on else 4000}}
            cls=dp.classify([('C1111.2','U1105.12'),('C1129.1','U1105.16')],pairs(False),pairs(connected_after),table,set(spec['zones']))
            worker={'board_acceptance':False,'mode':spec['mode'],'repair_basis':False,'counts':dict(z.COUNTS),'duplicates_before':[],'input_zone_owners':sorted(spec['input_zones']),
                    'fill':{'returned':True,'seconds':1.5,'zones':sorted(spec['zones'])} if spec['mode']=='derive' else None,
                    'before':{'pairs':pairs(False)},'after':{'zones':[r for r in table if r['uuid'] in spec['zones']],'pairs':pairs(connected_after)},
                    'reloaded':{'zones':[r for r in table if r['uuid'] in spec['zones']],'zone_table':table,'pairs':pairs(connected_after)},'classification':cls}
            (scratch/'zone.json').write_text(json.dumps(worker));record.update(status='COMPLETE',exit_code=0)
        return run_worker
    def frames(self,result,phase,point):
        result.setdefault('memory_telemetry',[]).append({'phase':phase,'point':point,'values':{'memory.max':fill.MEMORY_CAP,'memory.swap.max':0,'memory.peak':7},'events_since_baseline':{'oom':0,'oom_kill':0}})
    def run_payload(self,mode,t,root,spec_dir,candidate,output,worker):
        result={'status':'FAILED','mode':mode,'board_acceptance':False,'repair_basis':False,'full_board_fill':False,'refill_zones_option_used':False}
        with patch.object(z,'run_worker',side_effect=worker),patch.object(fill,'record_memory',side_effect=self.frames):
            try: dp.run(mode,root,spec_dir,candidate,Path(t)/('scratch-'+mode+output.name),output,result)
            except Exception as exc: result['failure']={'type':type(exc).__name__,'message':str(exc)};result['status']=result['status'] if result['status']==dp.REJECTED_STATUS else 'FAILED'
        result['elapsed_seconds']=1.0
        return result
    def test_derive_then_evaluate_then_rejections(self):
        with tempfile.TemporaryDirectory() as t:
            root,pins,spec_dir=self.setup(t);absent=Path(t)/'absent'
            with patch.dict(fill.PINS,pins):
                out1=Path(t)/'out1';out1.mkdir()
                r=self.run_payload('derive',t,root,spec_dir,absent,out1,self.fake_worker(connected_after=True))
                self.assertEqual(r['status'],dp.DERIVE_STATUS,r.get('failure'));dp.validate_result(r,'derive');self.assertEqual(r['budget'],'standard');self.assertIn('budget standard: payload 420 s',r['limits'])
                self.assertEqual(self.supervision,[{'stage_caps':{'prepare':60,'fill':260,'verify':100},'pcb_limit':64*1024*1024,'deadline':self.supervision[0]['deadline']}])
                manifest=json.loads((out1/'manifest.json').read_text());self.assertEqual(manifest['identity']['zones'],[AGND_IN1]);self.assertEqual(manifest['classification']['C1111.2<->U1105.12']['class'],'CONNECTED_VIA_SELECTED_FILL');self.assertEqual(manifest['budget'],'standard')
                self.assertEqual(manifest['classification']['C1129.1<->U1105.16']['class'],'UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN');self.assertEqual(set(manifest['after_owners']['filled_polygon_by_zone']),{AGND_IN1})
                receipt={'tooling_sha':'t'*40,'image_identity':{'id':IMAGE_ID},'spec':{'zones':[AGND_IN1],'pairs':[['C1111.2','U1105.12'],['C1129.1','U1105.16']]},'expected_identity_key':r['identity_key']}
                fake_root=Path(t)/'fake-root';(fake_root/'boards').mkdir(parents=True);(fake_root/'boards'/'osc-core').symlink_to(root)
                v=l.verify_derived_output('derive',r,out1,None,fake_root,receipt);self.assertTrue(v['reuse']['reusable'])
                # Evaluate the exported derivation: reuse accepted, no fill, classification recomputed on the derived board.
                out2=Path(t)/'out2';out2.mkdir()
                e=self.run_payload('evaluate',t,root,spec_dir,out1,out2,self.fake_worker(connected_after=True))
                self.assertEqual(e['status'],dp.EVALUATE_STATUS,e.get('failure'));dp.validate_result(e,'evaluate');self.assertTrue(e['reuse']['reusable']);self.assertIsNone(e['worker_summary']['fill'])
                v=l.verify_derived_output('evaluate',e,out2,out1,fake_root,{**receipt,'expected_identity_key':e['identity_key']});self.assertTrue(v['reuse']['reusable'])
                # Stale derived board: a byte appended after the manifest was written is rejected before any native work.
                (out1/'after'/'osc-core.kicad_pcb').write_text(self.text([AGND_IN1])+'\n')
                out3=Path(t)/'out3';out3.mkdir()
                e=self.run_payload('evaluate',t,root,spec_dir,out1,out3,self.fake_worker())
                self.assertEqual(e['status'],dp.REJECTED_STATUS);self.assertIn('stale or altered',e['failure']['message']);self.assertFalse(any(out3.iterdir()))
                with self.assertRaises(ValueError):dp.validate_result(e,'evaluate')
                (out1/'after'/'osc-core.kicad_pcb').write_text(self.text([AGND_IN1]))
                # Changed source: the current source's non-fill semantics differ, so the saved derivation is not reusable.
                (root/'osc-core.kicad_pcb').write_text(self.text().replace('(version 20250101)','(version 20250102)'))
                with patch.dict(fill.PINS,{'osc-core.kicad_pcb':c.sha(root/'osc-core.kicad_pcb')}):
                    (spec_dir/'context.json').write_text(json.dumps({'image_id':IMAGE_ID,'kicad':'10.0.6','source_pins':dict(fill.PINS),'process':d.PROCESS_VERSION,'tooling_sha':'t'*40,'budget':'standard'}))
                    out4=Path(t)/'out4';out4.mkdir()
                    e=self.run_payload('evaluate',t,root,spec_dir,out1,out4,self.fake_worker())
                    self.assertEqual(e['status'],dp.REJECTED_STATUS);self.assertIn('identity key mismatch in source',e['failure']['message'])
    def test_chained_derivation_and_worker_failure(self):
        with tempfile.TemporaryDirectory() as t:
            root,pins,spec_dir=self.setup(t);absent=Path(t)/'absent'
            with patch.dict(fill.PINS,pins):
                out1=Path(t)/'out1';out1.mkdir()
                r=self.run_payload('derive',t,root,spec_dir,absent,out1,self.fake_worker());self.assertEqual(r['status'],dp.DERIVE_STATUS,r.get('failure'))
                (spec_dir/'spec.json').write_text(json.dumps({'zones':[AGND_F],'pairs':[['C1111.2','U1105.12'],['C1129.1','U1105.16']],'note':'chain'}))
                out2=Path(t)/'out2';out2.mkdir()
                r2=self.run_payload('derive',t,root,spec_dir,out1,out2,self.fake_worker(connected_after=True))
                self.assertEqual(r2['status'],dp.DERIVE_STATUS,r2.get('failure'));dp.validate_result(r2,'derive')
                manifest=json.loads((out2/'manifest.json').read_text());self.assertEqual(manifest['parent']['zones'],[AGND_IN1]);self.assertEqual(manifest['identity']['parent_key'],r['identity_key'])
                self.assertEqual(set(manifest['after_owners']['filled_polygon_by_zone']),{AGND_IN1,AGND_F});self.assertEqual(manifest['classification']['C1111.2<->U1105.12']['class'],'CONNECTED_VIA_SELECTED_FILL')
                receipt={'tooling_sha':'t'*40,'image_identity':{'id':IMAGE_ID},'spec':{'zones':[AGND_F],'pairs':[['C1111.2','U1105.12'],['C1129.1','U1105.16']]}}
                fake_root=Path(t)/'fake-root';(fake_root/'boards').mkdir(parents=True);(fake_root/'boards'/'osc-core').symlink_to(root)
                self.assertTrue(l.verify_derived_output('derive',r2,out2,out1,fake_root,receipt)['reuse']['reusable'])
                # Overlapping selection with the parent is refused before any worker runs.
                (spec_dir/'spec.json').write_text(json.dumps({'zones':[AGND_IN1],'pairs':[['C1111.2','U1105.12']]}))
                out3=Path(t)/'out3';out3.mkdir()
                r3=self.run_payload('derive',t,root,spec_dir,out1,out3,self.fake_worker());self.assertEqual(r3['status'],'FAILED');self.assertIn('overlap',r3['failure']['message'])
                # Evaluate refuses chained derivations explicitly.
                (spec_dir/'spec.json').write_text(json.dumps({'zones':[AGND_F],'pairs':[['C1111.2','U1105.12']]}))
                out4=Path(t)/'out4';out4.mkdir()
                e=self.run_payload('evaluate',t,root,spec_dir,out2,out4,self.fake_worker());self.assertEqual(e['status'],'FAILED');self.assertIn('chained',e['failure']['message'])
                # Mid-run worker failure (stage cap) leaves a FAILED result with the partial substage log and no export.
                (spec_dir/'spec.json').write_text(json.dumps({'zones':[AGND_F],'pairs':[['C1111.2','U1105.12']]}))
                out5=Path(t)/'out5';out5.mkdir()
                f=self.run_payload('derive',t,root,spec_dir,absent,out5,self.fake_worker(fail=True))
                self.assertEqual(f['status'],'FAILED');self.assertIn('fill stage cap',f['failure']['message']);self.assertFalse(any(out5.iterdir()))
                with self.assertRaises(ValueError):dp.validate_result(f,'derive')
    def test_probe_budget_is_bound_to_its_zone_and_mode(self):
        with tempfile.TemporaryDirectory() as t:
            root,pins,spec_dir=self.setup(t,budget='fill-520-probe');absent=Path(t)/'absent'
            with patch.dict(fill.PINS,pins):
                # The probe profile refuses the In1 zone the fixture spec selects, before any worker runs or export happens.
                out1=Path(t)/'out1';out1.mkdir()
                r=self.run_payload('derive',t,root,spec_dir,absent,out1,self.fake_worker());self.assertEqual(r['status'],'FAILED');self.assertIn('different zone set',r['failure']['message']);self.assertEqual(self.supervision,[]);self.assertFalse(any(out1.iterdir()))
                (spec_dir/'spec.json').write_text(json.dumps({'zones':[AGND_F],'pairs':[['C1111.2','U1105.12'],['C1129.1','U1105.16']],'note':'probe'}))
                out2=Path(t)/'out2';out2.mkdir()
                r=self.run_payload('derive',t,root,spec_dir,absent,out2,self.fake_worker());self.assertEqual(r['status'],dp.DERIVE_STATUS,r.get('failure'))
                self.assertEqual(self.supervision[0]['stage_caps'],{'prepare':60,'fill':520,'verify':100});self.assertEqual(self.supervision[0]['pcb_limit'],128*1024*1024);self.assertEqual(r['budget'],'fill-520-probe')
                manifest=json.loads((out2/'manifest.json').read_text());self.assertEqual((manifest['budget'],manifest['stage_caps']['fill']),('fill-520-probe',520))
                r['elapsed_seconds']=700;dp.validate_result(r,'derive','fill-520-probe')
                with self.assertRaises(ValueError):dp.validate_result(r,'derive')
                receipt={'tooling_sha':'t'*40,'image_identity':{'id':IMAGE_ID},'spec':{'zones':[AGND_F],'pairs':[['C1111.2','U1105.12'],['C1129.1','U1105.16']]},'deadline_policy':{'budget':'fill-520-probe'}}
                fake_root=Path(t)/'fake-root';(fake_root/'boards').mkdir(parents=True);(fake_root/'boards'/'osc-core').symlink_to(root)
                self.assertTrue(l.verify_derived_output('derive',r,out2,None,fake_root,receipt)['reuse']['reusable'])
                with self.assertRaises(ValueError) as caught:l.verify_derived_output('derive',r,out2,None,fake_root,{**receipt,'deadline_policy':{'budget':'standard'}})
                self.assertIn('budget',str(caught.exception))
                # Evaluate is outside the probe profile even for its zone.
                out3=Path(t)/'out3';out3.mkdir()
                e=self.run_payload('evaluate',t,root,spec_dir,out2,out3,self.fake_worker());self.assertEqual(e['status'],'FAILED');self.assertIn('does not cover payload evaluate',e['failure']['message']);self.assertFalse(any(out3.iterdir()))
                # The standard chain still evaluates the probe's board: budgets bound the run, not the derived board's identity.
                (spec_dir/'context.json').write_text(json.dumps({'image_id':IMAGE_ID,'kicad':'10.0.6','source_pins':pins,'process':d.PROCESS_VERSION,'tooling_sha':'t'*40,'budget':'standard'}))
                out4=Path(t)/'out4';out4.mkdir()
                e=self.run_payload('evaluate',t,root,spec_dir,out2,out4,self.fake_worker());self.assertEqual(e['status'],dp.EVALUATE_STATUS,e.get('failure'));self.assertTrue(e['reuse']['reusable']);self.assertEqual(self.supervision[0]['stage_caps'],dp.EVALUATE_CAPS)
                (spec_dir/'context.json').write_text(json.dumps({'image_id':IMAGE_ID,'kicad':'10.0.6','source_pins':pins,'process':d.PROCESS_VERSION,'tooling_sha':'t'*40,'budget':'bogus'}))
                out5=Path(t)/'out5';out5.mkdir()
                e=self.run_payload('evaluate',t,root,spec_dir,out2,out5,self.fake_worker());self.assertEqual(e['status'],'FAILED');self.assertIn('unknown budget profile',e['failure']['message'])
