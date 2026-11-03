"""Adversarial additive-scope/partition controls; no physical claims."""
from pathlib import Path
import copy,importlib.util,json,sys,unittest
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('stage51_accept',HERE/'accept.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
def fixture():
 objects={'source':dict(kind='pad',ref='R2316',pin='2',net=a.NET),'target':dict(kind='pad',ref='U2317',pin='10',net=a.NET)}
 main=['target']
 for i in range(49):
  k='track'+str(i);main.append(k);objects[k]=dict(kind='segment',uuid=k,net=a.NET)
 others=[]
 for i in range(116):
  k='other'+str(i);others.append([k]);objects[k]=dict(kind='pad',ref=k,pin='1',net='OTHER')
 old=dict(objects=objects,groups={a.NET:[['source'],main],'OTHER':others},native_open_edges=116)
 new=copy.deepcopy(old);new['groups'][a.NET]=[['source']+main+['new0','new1']];new['native_open_edges']=115
 for k in ['new0','new1']:new['objects'][k]=dict(kind='segment',uuid=k,net=a.NET)
 return old,new,dict(copper=[dict(uuid=k) for k in ['new0','new1']])
class AcceptanceTests(unittest.TestCase):
 def setUp(self):self.old,self.new,self.p=fixture()
 def test_exact_merge(self):self.assertTrue(a.connectivity(self.old,self.new,self.p)['accepted'])
 def test_wrong_target(self):
  self.old['objects']['target']['ref']='wrong'
  with self.assertRaises((ValueError,StopIteration)):a.connectivity(self.old,self.new,self.p)
 def test_other_partition_changed(self):
  self.new['groups']['OTHER'][0]+=self.new['groups']['OTHER'].pop()
  with self.assertRaises(ValueError):a.connectivity(self.old,self.new,self.p)
 def test_retained_deleted(self):
  del self.new['objects']['track0']
  with self.assertRaises(ValueError):a.connectivity(self.old,self.new,self.p)
 def test_retained_net_changed(self):
  self.new['objects']['track0']['net']='OTHER'
  with self.assertRaises(ValueError):a.connectivity(self.old,self.new,self.p)
 def test_new_only_island(self):
  self.new['groups'][a.NET][0].remove('new0');self.new['groups'][a.NET].append(['new0'])
  with self.assertRaises(ValueError):a.connectivity(self.old,self.new,self.p)
 def test_duplicate_membership(self):
  self.new['groups'][a.NET][0].append('source')
  with self.assertRaises(ValueError):a.connectivity(self.old,self.new,self.p)
 def test_added_wrong_net(self):
  self.new['objects']['new0']['net']='OTHER'
  with self.assertRaises(ValueError):a.connectivity(self.old,self.new,self.p)
 def test_unapproved_addition(self):
  self.new['objects']['extra']=dict(kind='via',uuid='extra',net=a.NET)
  with self.assertRaises(ValueError):a.connectivity(self.old,self.new,self.p)
 def test_changed_count(self):
  self.new['native_open_edges']=114
  with self.assertRaises(ValueError):a.connectivity(self.old,self.new,self.p)
 def test_tenting_override_rejected(self):
  p=a.read(HERE/'proposal.json');raw='(kicad_pcb '+''.join(a.exact_added_block(x) for x in p['copper'])+')';a.exact_added_properties(raw,p)
  with self.assertRaises(ValueError):a.exact_added_properties(raw.replace('(size 0.6)','(tenting (front no)) (size 0.6)'),p)
 def test_new_warning_rejected(self):
  with self.assertRaises(ValueError):a.warning_gate({'violations':[]},{'violations':[dict(type='via_dangling',severity='warning',items=[dict(uuid='new')])]})
 def test_capped_non_silk_rejected(self):
  d={'violations':[dict(type='via_dangling',severity='warning',items=[dict(uuid=str(i))]) for i in range(199)]}
  with self.assertRaises(ValueError):a.warning_gate(d,d)
 def test_local_proposal_shift_rejected(self):
  p=a.read(HERE/'proposal.json');base=a.ROOT/'.circuit-cache/stage49-fresh/osc-jack-left.kicad_pcb'
  if not base.exists():self.skipTest('ignored native input unavailable')
  p['copper'][1]['at_nm'][0]+=1000
  with self.assertRaisesRegex(ValueError,'exact authorized proposal'):a.identity(base.read_text(),base.read_text(),p)
 def test_proposal_hash(self):self.assertEqual(a.sha(HERE/'proposal.json'),a.PROPOSAL_SHA)
class EvidenceTests(unittest.TestCase):
 def test_review_bindings(self):
  for name,sha in a.read(HERE/'review-bindings.json')['sha256'].items():self.assertEqual(a.sha(a.ROOT/name),sha,name)
 def test_rejected_native_outcomes(self):
  d=a.read(HERE/'audit.json');self.assertFalse(d['accepted_repair'])
  full=d['trials']['trial1'];seed=d['trials']['seed']
  self.assertEqual(full['opens'],117);self.assertEqual(seed['opens'],116)
  self.assertEqual(full['rejection'],'unexpected partition: -12V')
  self.assertEqual(set(full['retained_partition_changes']),{a.NET,'-12V'})
  self.assertEqual(full['retained_partition_changes']['-12V']['after_sizes'],[15,23,977])
  self.assertEqual(seed['retained_partition_changes'],{})
 def test_retained_report_hashes(self):
  d=a.read(HERE/'audit.json')
  for name,trial in d['trials'].items():
   for path,sha in trial['bindings'].items():
    if '/drc-' in path:self.assertEqual(a.sha(HERE/'evidence'/(name+'-'+Path(path).name)),sha)
 def test_guard_rejected(self):
  d=a.read(HERE/'evidence/guarded.search.json')
  self.assertTrue(any(x['reason']=='fill_guard_disconnection' for x in d['diagnostics']))
if __name__=='__main__':unittest.main()
