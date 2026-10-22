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
import osc_fill_check as f
import osc_frozen_fill as fill
import osc_single_zone_payload as z
import osc_single_zone_local as l

GUARD={'HEAVY_GUARD_HELD':'1'}

def env(**extra):
    base={k:v for k,v in os.environ.items() if k not in ('GITHUB_ACTIONS','RUNNER_ENVIRONMENT','CI','DOCKER_HOST','DOCKER_CONTEXT','HEAVY_GUARD_HELD','OSC_LOCAL_ADAPTER')}
    base.update(extra);return base

class Payload(unittest.TestCase):
    def test_constants_and_stage_registration(self):
        self.assertEqual(z.PAYLOAD_SECONDS,420);self.assertEqual(sum(z.STAGE_CAPS.values()),420)
        self.assertNotIn('zone',fill.SUBSTAGES);self.assertEqual(set(z.STAGE_GROUP),set(z.STAGES))
        self.assertEqual(z.TARGET_ZONE,'265b1369-38aa-5a3a-b488-eb0aae22e998');self.assertEqual(len(z.DUPLICATE_UUIDS),6)
        self.assertEqual(z.PAIRS,[('C1129.1','U1105.16'),('C1131.1','U1106.8')])
    def test_summarize_cluster_and_bridging(self):
        from types import SimpleNamespace as NS
        layers={'F.Cu':0,'In4.Cu':10,'B.Cu':2}
        def item(kind,u,net,on,pos=(1,2)):
            return type(kind,(),{'m_Uuid':NS(AsString=lambda:u),'GetNetname':lambda self:net,'IsOnLayer':lambda self,l:l in on,'GetPosition':lambda self:NS(x=pos[0],y=pos[1]),
                                 'GetDrillValue':lambda self:3,'GetIsRuleArea':lambda self:False})()
        poly=NS(Contains=lambda p:p.x==1)
        items=[item('PAD','p1','+12V',[0]),item('PCB_VIA','v1','+12V',[0,10,2]),item('PCB_VIA','v2','+12V',[0,10,2],(9,9)),item('ZONE',z.TARGET_ZONE,'+12V',[10]),item('PCB_TRACK','t1','+12V',[0])]
        proxy=type('PCB_TRACK',(),{'Cast':lambda self:items[1]})();items.append(proxy)
        s=z.summarize_cluster(items,layers,{'p1':'C1129.1'},None,poly)
        self.assertEqual(s['size'],6);self.assertTrue(s['selected_zone_member']);self.assertEqual(s['pads'],['C1129.1']);self.assertEqual(s['counts']['PCB_VIA'],3)
        self.assertEqual([(v['uuid'],v['inside_selected_fill']) for v in s['vias']],[('v1',True),('v1',True),('v2',False)]);self.assertEqual(s['layers'],{'F.Cu':5,'In4.Cu':4,'B.Cu':3})
    def test_via_listing_truncates_instead_of_failing(self):
        from types import SimpleNamespace as NS
        def via(u): return type('PCB_VIA',(),{'m_Uuid':NS(AsString=lambda:u),'GetNetname':lambda self:'+12V','IsOnLayer':lambda self,l:True,'GetPosition':lambda self:NS(x=0,y=0),'GetDrillValue':lambda self:3})()
        s=z.summarize_cluster([via('v%d'%i) for i in range(z.VIA_LIMIT+5)],{'F.Cu':0},{},None,None)
        self.assertEqual(len(s['vias']),z.VIA_LIMIT);self.assertEqual(s['vias_truncated'],5);self.assertGreaterEqual(z.VIA_LIMIT,490)
    def good_result(self):
        rows=[{'seq':i+1,'phase':'zone','stage':s,'event':e,'monotonic_seconds':float(i)} for i,(s,e) in enumerate((s,e) for s in z.STAGES for e in ('start','complete'))]
        frame=lambda p,q:{'phase':p,'point':q,'values':{'memory.max':fill.MEMORY_CAP,'memory.swap.max':0,'memory.peak':1},'events_since_baseline':{'oom':0,'oom_kill':0}}
        pair={'connected':True,'symmetric':True}
        pairs={'C1129.1<->U1105.16':pair,'C1131.1<->U1106.8':pair,'ratsnest':{'unconnected_count':1}}
        return {'status':z.STATUS,'board_acceptance':False,'input_before':dict(fill.PINS),'input_after':dict(fill.PINS),'nonfill_input':'a'*64,'nonfill_after':'a'*64,
            'after_owners':{'zones':351,'filled_polygon_by_zone':{z.TARGET_ZONE:3}},'command':{'status':'COMPLETE','exit_code':0},'worker_substages':{'zone':{'complete':True,'rows':rows}},
            'memory_telemetry':[frame(p,q) for p in ('preflight','zone','verify') for q in ('before','after')],'elapsed_seconds':100,
            'worker':{'fill':{'returned':True},'counts':dict(z.COUNTS),'before':{'pairs':pairs},'after':{'pairs':pairs,'counts':dict(z.COUNTS),'selected':{'counts':{'In4.Cu':2}}},'reloaded':{'pairs':pairs,'counts':dict(z.COUNTS)}}}
    def test_validate_result(self):
        z.validate_result(self.good_result())
        def broken(mutate):
            r=self.good_result();mutate(r)
            with self.assertRaises(ValueError):z.validate_result(r)
        broken(lambda r:r.update(status='FAILED'));broken(lambda r:r.update(failure={'x':1}));broken(lambda r:r.update(nonfill_after='b'*64))
        broken(lambda r:r['after_owners']['filled_polygon_by_zone'].update({'other':1}));broken(lambda r:r['command'].update(exit_code=1))
        broken(lambda r:r['worker_substages']['zone']['rows'].pop());broken(lambda r:r['memory_telemetry'][3]['events_since_baseline'].update(oom_kill=1))
        broken(lambda r:r['worker']['after']['pairs']['C1129.1<->U1105.16'].update(symmetric=False));broken(lambda r:r['worker']['after']['selected']['counts'].update({'In4.Cu':0}))
        broken(lambda r:r.update(elapsed_seconds=421));broken(lambda r:r['worker'].update(counts={}))
    def test_worker_reserve(self):
        self.assertEqual(z.WORKER_RESERVE,40);self.assertEqual(sum(z.STAGE_CAPS.values()),z.PAYLOAD_SECONDS)
    def test_cluster_bound(self):
        conn=type('C',(),{'GetConnectedItems':lambda self,i:[0]*(z.CLUSTER_LIMIT+1)})()
        with self.assertRaises(ValueError):z.cluster(conn,None)
    def test_zone_fill_owners_pinned_format(self):
        text='(kicad_pcb\n\t(zone\n\t\t(net 1)\n\t\t(uuid "a")\n\t\t(filled_polygon\n\t\t\t(pts)\n\t\t)\n\t\t(filled_polygon\n\t\t)\n\t)\n\t(zone\n\t\t(uuid "b")\n\t)\n\t(segment\n\t)\n)\n'
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'x.kicad_pcb';p.write_text(text)
            self.assertEqual(z.zone_fill_owners(p),{'zones':2,'filled_polygon_by_zone':{'a':2}})
    def test_read_rows_ignores_partial_line(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'log.jsonl';p.write_bytes(b'{"seq":1,"stage":"load","event":"start","monotonic_seconds":1.0}\n{"seq":2,"sta')
            self.assertEqual([r['stage'] for r in z.read_rows(p)],['load']);self.assertEqual(z.read_rows(Path(t)/'absent'),[])
    def test_stage_cap_enforced_by_substage_log(self):
        with tempfile.TemporaryDirectory() as t:
            scratch=Path(t);log=scratch/'zone-substages.jsonl'
            log.write_text(json.dumps({'seq':1,'phase':'zone','stage':'fill','event':'start','monotonic_seconds':0.0})+'\n')
            record={}
            class Proc:
                pid=os.getpid();returncode=None
                def poll(self): return None
                def wait(self,timeout=None): self.returncode=-9
            with patch.object(z.subprocess,'Popen',return_value=Proc()),patch.object(z.os,'killpg'),patch.object(z.time,'monotonic',side_effect=[10.0,500.0,500.0,500.0,500.0,500.0]),\
                 patch.object(z.time,'sleep'):
                with self.assertRaises(TimeoutError) as caught: z.run_worker(scratch,10000.0,record)
            self.assertIn('fill stage cap',str(caught.exception));self.assertEqual(record['status'],'FAILED');self.assertEqual(record['stage_group_starts'],{'fill':0.0})
    def test_stage_log_and_parser(self):
        with tempfile.TemporaryDirectory() as t:
            log=z.StageLog(Path(t)/'zone-substages.jsonl')
            with log.stage('load'): pass
            log.write('identity','start');log.close()
            data=(Path(t)/'zone-substages.jsonl').read_bytes()
            parsed=z.parse_stages(data);self.assertEqual([(r['stage'],r['event']) for r in parsed['rows']],[('load','start'),('load','complete'),('identity','start')]);self.assertFalse(parsed['complete'])
            result={}
            with self.assertRaises(ValueError):z.capture_stages(result,Path(t),require_complete=True)
            self.assertFalse(result['worker_substages']['zone']['complete']);self.assertEqual(len(result['worker_substages']['zone']['rows']),3)
            with self.assertRaises(ValueError):z.parse_stages(b'{"seq":1,"phase":"zone","stage":"fill","event":"start","monotonic_seconds":1}\n')
    def test_pins_restored_when_output_exists(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'out';out.mkdir()
            args=l.parse(['run',str(Path(t)/'src'),str(out),'--state',str(Path(t)/'s'),'--authorization','offline unit test authorization note'])
            before=dict(c.PINS)
            with self.assertRaises(FileExistsError):l.run(args)
            self.assertEqual(c.PINS,before)
    def test_counts_pinned(self):
        self.assertEqual(z.COUNTS,{'segment':123905,'via':9646,'zone':351,'copper_zone':5})

class Controller(unittest.TestCase):
    def test_budget_constants_match_hosted_fill(self):
        self.assertEqual(l.TOTAL_SECONDS,590);self.assertEqual(l.PAYLOAD_SECONDS,420);self.assertEqual(l.ATTACH_SECONDS,430)
        self.assertEqual(l.OUTER_STOP_SECONDS,600);self.assertEqual(l.LAUNCH_RESERVE,497);self.assertEqual(set(l.BUNDLE),{'osc_single_zone_payload.py','osc_zone_drc_payload.py','osc_frozen_fill.py','osc_frozen_topology.py'})
    def test_board_pins_extend_source_allowlist(self):
        pins=l.board_pins();self.assertEqual(set(pins),set(c.PINS)|{'boards/osc-core/'+n for n in fill.PINS})
        self.assertEqual(pins['boards/osc-core/osc-core.kicad_pcb'],'fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10')
    def test_adapter_requires_local_marker(self):
        with patch.dict(os.environ,env(),clear=True):
            with self.assertRaises(ValueError):l.adapter(['run'])
    def test_adapter_payload_policy(self):
        with tempfile.TemporaryDirectory() as t:
            state=Path(t)/'state';state.mkdir()
            argv=['run','--rm','--platform','linux/amd64','--network','none','--user','1:1','--volume','/src:/work','--volume','/h:/tmp/kicad-home','--workdir','/work','--entrypoint','/bin/sh',c.IMAGE,'-c','x','kicad-oracle','python3','-B','/analysis/osc_single_zone_payload.py']
            environment=env(OSC_LOCAL_ADAPTER='1',OSC_INPUT_ROOT='/src',OSC_PAYLOAD='/bundle',OSC_STATE=str(state),OSC_DEADLINE=str(10**9),OSC_COMMAND_DEADLINE=str(10**9),OSC_REAL_DOCKER='/usr/bin/docker')
            with patch.dict(os.environ,environment,clear=True),patch.object(l,'resource_preflight'),patch.object(c,'DEADLINE',10**9),patch.object(c,'adapter',return_value=0) as inner:
                self.assertEqual(l.adapter(argv),0)
            self.assertEqual(inner.call_args.kwargs,{'memory_policy':'fill-2g-noswap','execution_policy':'fill-430'})
            self.assertIn('--read-only',inner.call_args.args[0]);self.assertIn('/src:/work:ro',inner.call_args.args[0])
    def test_resource_preflight_refuses_ci_and_records(self):
        with tempfile.TemporaryDirectory() as t:
            state=Path(t)/'state';state.mkdir()
            with patch.dict(os.environ,env(OSC_STATE=str(state),CI='true',OSC_DEADLINE='1',OSC_REAL_DOCKER='/usr/bin/docker'),clear=True):
                with self.assertRaises(ValueError):l.resource_preflight()
            record=json.loads(next(state.glob('resource-*.json')).read_text());self.assertEqual(record['status'],'FAILED');self.assertIn('CI',record['error'])
    def test_run_gate_failure_before_commands(self):
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'src';source.mkdir();out=Path(t)/'out';state=Path(t)/'state'
            args=l.parse(['run',str(source),str(out),'--state',str(state),'--authorization','offline unit test authorization note'])
            with patch.dict(os.environ,env(TOOLING_SHA='a'*40),clear=True),patch.object(c,'run_command') as runner,contextlib.redirect_stdout(io.StringIO()):
                code=l.run(args)
            receipt=json.loads((out/'receipt.json').read_text())
            self.assertEqual(code,1);self.assertIn('heavy-guard',receipt['error']);runner.assert_not_called();self.assertFalse(state.exists())
            self.assertEqual(receipt['deadline_policy']['payload_seconds'],420);self.assertIs(receipt['board_acceptance'],False);self.assertTrue(receipt['drc'].startswith('NOT RUN: '))
            self.assertNotIn('boards/osc-core/osc-core.kicad_pcb',c.PINS)
    def test_summarize_bounded(self):
        row={'connected':True,'symmetric':True,'cluster_a':{'size':9,'selected_zone_member':True,'vias':[{'x':1}]*100},'cluster_b':{'size':9,'selected_zone_member':True,'vias':[]},'bridging_vias':{'from_a_side':[1],'from_b_side':[1,2],'new_in_merged_cluster':[]}}
        detail={'status':z.STATUS,'elapsed_seconds':1,'worker':{'fill':{'returned':True,'seconds':2},'after':{'selected':{'counts':{'In4.Cu':3}},'pairs':{'C1129.1<->U1105.16':row,'ratsnest':{'unconnected_count':4}}}},'memory_telemetry':[{'values':{'memory.peak':5}}]}
        s=json.loads(l.summarize({'status':z.STATUS,'cleanup':[{'status':'REMOVED_CONFIRMED'}],'before':1,'after':1},detail))
        pair=s['pairs']['after']['C1129.1<->U1105.16'];self.assertTrue(s['source_hashes_unchanged']);self.assertEqual(pair['connected'],True);self.assertEqual(pair['bridging'],{'from_a_side':1,'from_b_side':2,'new_in_merged_cluster':0})
        self.assertNotIn('vias',json.dumps(pair));self.assertEqual(s['pairs']['after']['ratsnest']['unconnected_count'],4);self.assertEqual(s['memory_peak'],5)

class CandidateAndDrc(unittest.TestCase):
    def test_extra_mounts(self):
        import osc_zone_drc_payload as d
        args=['run','--volume','/src:/work:ro',c.IMAGE,'x']
        self.assertEqual(l.extra_mounts(args,None,None),args)
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'out';out.mkdir();cand=Path(t)/'cand';cand.mkdir()
            with self.assertRaises(ValueError):l.extra_mounts(args,str(out),str(cand))
            (cand/'manifest.json').write_text('{}')
            got=l.extra_mounts(args,str(out),str(cand))
            self.assertEqual(got[:2],['run','--volume']);self.assertIn(str(out)+':/output',got);self.assertIn(str(cand)+':/candidate:ro',got);self.assertLess(got.index(str(out)+':/output'),got.index(c.IMAGE))
            with self.assertRaises(ValueError):l.extra_mounts(args,'relative/dir',None)
    def test_bundle_sources_exist_and_match_names(self):
        sources=l.bundle_sources();self.assertEqual(set(sources),set(l.BUNDLE))
        for name,path in sources.items(): self.assertEqual(path.name,name);self.assertTrue(path.is_file())
    def test_missing_output_argument_has_no_side_effects(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'out';before=dict(c.PINS)
            args=l.parse(['run',str(Path(t)/'src'),str(out),'--state',str(Path(t)/'s'),'--authorization','offline unit test authorization note','--payload','candidate'])
            with self.assertRaises(ValueError):l.run(args)
            self.assertFalse(out.exists());self.assertEqual(c.PINS,before)
    def test_modes(self):
        self.assertEqual(set(l.MODES),{'zone','candidate','drc'});self.assertEqual(l.MODES['drc'][1],['drc']);self.assertEqual(l.MODES['candidate'][0],'osc_zone_drc_payload.py')
        args=l.parse(['run','s','o','--state','st','--authorization','x'*20,'--payload','drc','--output','/o','--candidate','/c'])
        self.assertEqual((args.payload,args.output,args.candidate),('drc','/o','/c'))
    def test_classify_and_summarize(self):
        import osc_zone_drc_payload as d
        bag={'["violations","clearance","error","Clearance +12V vs AGND",["a"]]':2,'["unconnected_items","unconnected_items","error","Missing connection between items",["'+z.TARGET_ZONE+'","b"]]':1,'["violations","silk_overlap","warning","Silkscreen overlap",["c"]]':3}
        related,other=d.classify(bag);self.assertEqual(sum(related.values()),3);self.assertEqual(sum(other.values()),3)
        s=d.summarize_identities(bag,sample=2);self.assertEqual((s['count'],s['distinct'],s['sample_complete'],len(s['sample'])),(6,3,False,2))
    def frames(self):
        return [{'phase':'preflight','point':'before','values':{'memory.max':fill.MEMORY_CAP,'memory.swap.max':0,'memory.peak':1},'events_since_baseline':{'oom':0,'oom_kill':0}}]
    def test_verify_output_drc(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'out';out.mkdir();cand=Path(t)/'cand';cand.mkdir();(cand/'manifest.json').write_text('{"status":"x"}')
            report={'kicad_version':'10.0.6','violations':[{'type':'clearance','severity':'error','description':'d','items':[{'uuid':'u1'}]}],'unconnected_items':[],'schematic_parity':[]}
            detail={'status':l.MODES['drc'][2],'board_acceptance':False,'refill_zones_option_used':False,'memory_telemetry':self.frames(),'elapsed_seconds':10,'commands':{},'mode':'drc'}
            for kind in ('before','after'):
                p=out/('drc-'+kind+'.json');p.write_text(json.dumps(report));counts,ids=fill.drc_summary(p)
                detail['drc_'+kind]={'report_sha256':c.sha(p),'counts':counts,'identities':{'identity_sha256':fill.digest(sorted(ids.items()))}};detail['commands'][kind]={'status':'COMPLETE','exit_code':0}
            (out/'drc-manifest.json').write_text(json.dumps({'candidate_manifest_sha256':c.sha(cand/'manifest.json'),'reports':{k:detail['drc_'+k]['report_sha256'] for k in ('before','after')}}))
            v=l.verify_output('drc',detail,out,cand);self.assertEqual(v['host_counts_after'],{'violations:clearance':1})
            detail['commands']['after']['exit_code']=1
            with self.assertRaises(ValueError):l.verify_output('drc',detail,out,cand)
            detail['commands']['after']['exit_code']=0;(out/'drc-after.json').write_text(json.dumps(report)+' ')
            with self.assertRaises(ValueError):l.verify_output('drc',detail,out,cand)
    def test_verify_output_candidate_rejects_missing_fill(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'out';exported={}
            text='(kicad_pcb\n\t(zone\n\t\t(uuid "%s")\n%s\t)\n)\n'
            for kind,filled in (('before',''),('after','\t\t(filled_polygon\n\t\t)\n')):
                (out/kind).mkdir(parents=True);(out/kind/'osc-core.kicad_pcb').write_text(text%(z.TARGET_ZONE,filled))
                (out/kind/'osc-core.kicad_pro').write_text('p');(out/kind/'osc-core.kicad_dru').write_text('d')
                exported[kind]={n:c.sha(out/kind/n) for n in ('osc-core.kicad_pcb','osc-core.kicad_pro','osc-core.kicad_dru')}
            nonfill=fill.semantic_hash(out/'before'/'osc-core.kicad_pcb')
            manifest={'exported':exported,'nonfill_sha256':{'input':nonfill}};(out/'manifest.json').write_text(json.dumps(manifest))
            detail={'status':l.MODES['candidate'][2],'board_acceptance':False,'refill_zones_option_used':False,'memory_telemetry':self.frames(),'elapsed_seconds':10,'manifest_sha256':c.sha(out/'manifest.json'),
                    'exported':exported,'input_before':dict(fill.PINS),'input_after':dict(fill.PINS),'worker':{'fill':{'returned':True}},'command':{'status':'COMPLETE'},'normalize':{'status':'COMPLETE'}}
            with patch.dict(fill.PINS,{'osc-core.kicad_pro':exported['before']['osc-core.kicad_pro'],'osc-core.kicad_dru':exported['before']['osc-core.kicad_dru']}):
                detail['input_before']=dict(fill.PINS);detail['input_after']=dict(fill.PINS)
                v=l.verify_output('candidate',detail,out,None)
                self.assertEqual(v['owners_host']['after']['filled_polygon_by_zone'],{z.TARGET_ZONE:1})
                (out/'after'/'osc-core.kicad_pcb').write_text(text%(z.TARGET_ZONE,''));exported['after']['osc-core.kicad_pcb']=c.sha(out/'after'/'osc-core.kicad_pcb')
                (out/'manifest.json').write_text(json.dumps(manifest));detail['manifest_sha256']=c.sha(out/'manifest.json')
                with self.assertRaises(ValueError):l.verify_output('candidate',detail,out,None)

class Wrapper(unittest.TestCase):
    def test_outer_stop_contract(self):
        text=(Path(__file__).with_name('osc_single_zone_local.sh')).read_text()
        self.assertIn('outer_stop_seconds=600',text);self.assertIn('kill -KILL -- "-$pid"',text);self.assertIn('osc_single_zone_local.py" cleanup',text)
        self.assertIn('HEAVY_GUARD_HELD',text);self.assertNotIn('GITHUB_ACTIONS=',text);self.assertIn('TOOLING_SHA=$(git -C "$script_dir" rev-parse HEAD)',text)
        self.assertIn('shift 4',text);self.assertIn('--authorization "$authorization" "$@"',text)

if __name__=='__main__':unittest.main()
