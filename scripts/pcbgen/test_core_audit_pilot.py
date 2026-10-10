import copy,json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from scripts.pcbgen import audit_fixture_tasks as a,core_audit_pilot as p
from scripts.pcbgen import test_audit_fixture_tasks as fixtures
class PilotTests(unittest.TestCase):
 setUp=fixtures.TaskTests.setUp
 bundle=fixtures.TaskTests.bundle
 verify=fixtures.TaskTests.verify
 def test_registered_wrapper_preserves_original_jobs_and_exact_host_steps(self):
  import subprocess,re
  repo=Path(__file__).resolve().parents[2]
  original=subprocess.check_output(['git','show','803dcd00b83b5182857e0c3fc1c345152d831cff:.github/workflows/routing-benchmark.yml'],cwd=repo,text=True)
  wrapped=(repo/'.github/workflows/routing-benchmark.yml').read_text()
  def jobs(text):
   parts=re.split(r'^  ([a-z][a-z-]*):\n',text.split('jobs:\n',1)[1],flags=re.M)
   return dict(zip(parts[1::2],parts[2::2]))
  old=jobs(original);new=jobs(wrapped)
  self.assertEqual(set(new),set(old)|{'core-audit-task-pilot'})
  for key,body in old.items():
   condition=next(line for line in body.splitlines() if line.startswith('    if: '))
   replacement='    if: ${{ !inputs.core_audit_task_pilot && ('+condition[len('    if: '):]+') }}'
   self.assertEqual(new[key],body.replace(condition,replacement,1))
  standalone=(repo/'.github/workflows/core-audit-task-pilot.yml').read_text()
  self.assertEqual(new['core-audit-task-pilot'].split('    steps:\n',1)[1],standalone.split('    steps:\n',1)[1])
  self.assertIn('    timeout-minutes: 50',new['core-audit-task-pilot'])
  self.assertIn('      group: issue189-core-audit-task-pilot',new['core-audit-task-pilot'])
  self.assertIn('        default: false',wrapped.split('      core_audit_task_pilot:',1)[1].split('      reviewed_commit:',1)[0])
  self.assertIn('.github/workflows/routing-benchmark.yml',p.ORCHESTRATION_FILES)
 def test_aggregate_guard_and_shared_deadline(self):
  sample=dict(available_kib=2097152,total_rss_kib=12582912)
  self.assertIsNone(p.stop_reason(sample,2399,2400))
  self.assertIn('40_MINUTE',p.stop_reason(sample,2400,2400))
  for changed in (dict(available_kib=2097151),dict(total_rss_kib=12582913)):
   self.assertIn('MEMORY',p.stop_reason(sample|changed,0,2400))
 def test_authenticated_artifact_mutations(self):
  artifact=dict(id=42,expired=False,digest='sha256:'+('a'*64),workflow_run=dict(id=8,head_sha='b'*40));run=dict(id=8,head_sha='b'*40)
  for changes in ({},{'digest':'sha256:'+'c'*64},{'workflow_run':dict(id=9,head_sha='b'*40)},{'expired':True}):
   with patch.object(a,'github_json',side_effect=[artifact|changes,run]):
    if changes:
     with self.assertRaises(ValueError):a.authenticate_artifact(42,8,'b'*40,'a'*64)
    else:a.authenticate_artifact(42,8,'b'*40,'a'*64)
 def test_uuid_parser_is_kernel_dependency(self):
  self.assertIn('scripts/pcbgen/uuid_tools.py',a.KERNEL_FILES)
 def test_final_verifier_reads_lazy_fixtures_without_eager_aggregation(self):
  accesses=[];bundles=[]
  for original in self.bundles:
   b=a.Bundle(original);blob=b['fixture'];b['fixture']=lambda blob=blob:(accesses.append('pcb') or blob);bundles.append(b)
  original=a.verify_result
  def intercept(access,*paths):
   # One reconstruction per leaf during validation, none during access-map build.
   self.assertEqual(len(accesses),2)
   return original(access,*paths)
  with patch.object(a,'verify_result',side_effect=intercept):a.final_union(self.m,*self.paths,bundles,self.kernel,self.bindings)
 def test_unauthenticated_json_producer_cannot_import_checkpoints(self):
  approval=self.root/'approval.json';approval.write_text('{}')
  with self.assertRaisesRegex(ValueError,'approval hash'):p.authenticate_checkpoints('absent',approval,'0'*64,self.m,self.kernel,self.root,self.root/'out')
 def test_self_consistent_fabricated_checkpoint_approval_rejected_by_authenticated_metadata(self):
  approval=self.root/'fabricated-approval.json';commit='b'*40;orchestration={'sha256':'forged'}
  pin=dict(manifest_sha256=a.identity(self.m),policy=self.kernel,orchestration=orchestration,producer_commit=commit,artifact_id=42,run=8,artifact_sha256='a'*64,ledgers={})
  a.atomic(approval,pin)
  artifact=dict(id=42,expired=False,digest='sha256:'+'c'*64,workflow_run=dict(id=8,head_sha=commit));run=dict(id=8,head_sha=commit,path='.github/workflows/routing-benchmark.yml')
  with patch.object(p,'revision',return_value=orchestration),patch.object(a,'github_json',side_effect=[artifact,run]):
   with self.assertRaisesRegex(ValueError,'authenticated artifact'):p.authenticate_checkpoints('fabricated.zip',approval,a.SHA(approval.read_bytes()),self.m,self.kernel,self.root,self.root/'fabricated-output')
 def test_packet_scope_overlap_budget_mutations(self):
  tasks=[];bindings={};packets=[]
  for start in (15,23):
   packet=[]
   for index in range(start,start+8):
    t=dict(task_id=str(index),zone_uuid='e389d344-872d-538e-9bfc-39577adb1686',layer='B.Cu',stage=0,batch_index=index,expected_geometry={'native':'bound'});tasks.append(t);packet.append(t['task_id']);bindings[a.identity(t['expected_geometry'])]='a'*64
   packets.append(packet)
  m={'tasks':tasks};plan=dict(packets=packets,max_workers=2,command_seconds=2400,job_minutes=50,maximum_aggregate_rss_kib=12582912,minimum_available_kib=2097152)
  p.validate_packets(m,{},plan,bindings)
  for field,value in [('packets',[packets[0],packets[0]]),('command_seconds',4800),('max_workers',3)]:
   with self.assertRaises(ValueError):p.validate_packets(m,{},plan|{field:value},bindings)
 def test_preflight_failure_seals_partial_output_and_never_spawns(self):
  out=self.root/'pilot-output'
  with patch.dict('os.environ',{'GITHUB_RUN_ID':'42'}),patch.object(p,'revision',return_value={}),patch.object(p.subprocess,'check_output',return_value='wrong'),patch.object(p.subprocess,'Popen') as spawn:
   with self.assertRaises(ValueError):p.controller(self.root,self.root,self.root,out,'a'*40,2400)
  spawn.assert_not_called();receipt=json.loads((out/'producer.json').read_bytes());self.assertFalse(receipt['adopted']);self.assertEqual(receipt['ledgers'],{})
 def test_two_worker_memory_stop_cleans_and_seals_under_shared_budget(self):
  import subprocess,sys,time
  from types import SimpleNamespace
  rows=[];packets=[]
  for start in (15,23):
   packet=[]
   for i in range(start,start+8):
    t=dict(task_id=str(i),zone_uuid='e389d344-872d-538e-9bfc-39577adb1686',layer='B.Cu',stage=0,batch_index=i,expected_geometry={});rows.append(t);packet.append(str(i))
   packets.append(packet)
  rows.extend(dict(task_id='cached-'+str(i)) for i in range(410));m={'tasks':rows};leaves={'cached-'+str(i):{} for i in range(235)};bindings={a.identity({}):'a'*64}
  plan=dict(packets=packets,max_workers=2,command_seconds=2400,job_minutes=50,maximum_aggregate_rss_kib=12582912,minimum_available_kib=2097152)
  config=self.root/'config';config.mkdir()
  for name,value in [('manifest.json',m),('native-geometry-bindings.json',bindings),('pilot-plan.json',plan),('orchestration-revision.json',{})]:a.atomic(config/name,value)
  a.atomic(self.root/'metadata.json',{});out=self.root/'guarded';children=[];created=[];actual_spawn=subprocess.Popen
  def check(cmd,**kwargs):
   if cmd[:2]==['git','rev-parse']:return 'a'*40
   if cmd[:2]==['git','status']:return ''
   if cmd[:3]==['docker','image','inspect']:return 'sha256:image'
   if cmd[:2]==['docker','create']:
    cid='cid-'+str(len(created));created.append(cid);return cid
   if cmd[:2]==['docker','inspect']:
    i=int(cmd[2].split('-')[1]);child=children[i] if i<len(children) else None;running=child is not None and child.poll() is None
    return json.dumps([dict(Config={'Image':a.IMAGE},Image='sha256:image',State=dict(Pid=child.pid if running else 0,Running=running))])
   raise AssertionError(cmd)
  def spawn(cmd,**kwargs):
   child=actual_spawn([sys.executable,'-c','import time; time.sleep(60)'],**kwargs);children.append(child);return child
  try:
   with patch.dict('os.environ',{'GITHUB_RUN_ID':'42'}),patch.object(p,'revision',return_value={}),patch.object(a,'policy',return_value=self.kernel),patch.object(a,'validate_manifest'),patch.object(a,'reviewed_legacy_anchor'),patch.object(a,'import_legacy',return_value=(leaves,bindings)),patch.object(p.subprocess,'check_output',side_effect=check),patch.object(p.subprocess,'run',return_value=SimpleNamespace(returncode=0)),patch.object(p.subprocess,'Popen',side_effect=spawn),patch.object(p.resource,'available',side_effect=[99999999,99999999,99999999,1]):
    with self.assertRaises(SystemExit):p.controller(self.root,self.root,config,out,'a'*40,time.monotonic()+2400)
   self.assertEqual(len(children),2);self.assertTrue(all(c.poll() is not None for c in children));result=json.loads((out/'producer.json').read_bytes());self.assertEqual(result['status'],'INCOMPLETE_MEMORY_GUARD');self.assertEqual(result['owned_containers_remaining'],[]);self.assertEqual(result['process_tree_after_cleanup'],{})
  finally:
   for c in children:
    if c.poll() is None:c.kill();c.wait()
if __name__=='__main__':unittest.main()
