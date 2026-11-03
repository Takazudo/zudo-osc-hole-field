"""Adversarial additive-scope/partition controls; no physical claims."""
from pathlib import Path
import copy,importlib.util,json,sys,unittest
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('stage52_accept',HERE/'accept.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
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
  p=a.read(HERE/'trial1-proposal.json');raw='(kicad_pcb '+''.join(a.exact_added_block(x) for x in p['copper'])+')';a.exact_added_properties(raw,p)
  with self.assertRaises(ValueError):a.exact_added_properties(raw.replace('(size 0.6)','(tenting (front no)) (size 0.6)'),p)
 def test_new_warning_rejected(self):
  with self.assertRaises(ValueError):a.warning_gate({'violations':[]},{'violations':[dict(type='via_dangling',severity='warning',items=[dict(uuid='new')])]})
 def test_capped_non_silk_rejected(self):
  d={'violations':[dict(type='via_dangling',severity='warning',items=[dict(uuid=str(i))]) for i in range(199)]}
  with self.assertRaises(ValueError):a.warning_gate(d,d)
 def test_local_proposal_shift_rejected(self):
  p=a.read(HERE/'trial1-proposal.json');base=a.ROOT/'.circuit-cache/stage49-fresh/osc-jack-left.kicad_pcb'
  if not base.exists():self.skipTest('ignored native input unavailable')
  p['copper'][1]['at_nm'][0]+=1000
  with self.assertRaisesRegex(ValueError,'exact authorized proposal'):a.identity(base.read_text(),base.read_text(),p)
 def test_proposal_hash(self):self.assertEqual(a.sha(HERE/'trial1-proposal.json'),a.PROPOSAL_SHA)
class EvidenceTests(unittest.TestCase):
 def test_absolute_receipt_path(self):
  from unittest.mock import patch
  base=a.ROOT/'.circuit-cache/stage49-fresh';candidate=a.ROOT/'.circuit-cache/stage52-trial1'
  if not (candidate/'drc-pass1.json').exists():self.skipTest('ignored native receipt unavailable')
  # Bypass the intentionally rejected partition only to reach receipt validation;
  # the still-failing117-open gate must reject, never return an acceptance.
  with patch.object(a,'identity',return_value={}),patch.object(a,'connectivity',return_value={}):
   with self.assertRaisesRegex(ValueError,'native DRC/parity/open gate'):
    a.evaluate(base,candidate,HERE/'trial1-proposal.json','pass1')
 def test_rejected_native(self):
  d=a.read(HERE/'audit.json');self.assertFalse(d['accepted_repair']);self.assertTrue(d['independent_build_board_and_snapshot_identical'])
  for t in d['trials'].values():
   self.assertFalse(t['accepted']);self.assertEqual(t['opens'],117);self.assertEqual(t['rule_errors'],0);self.assertEqual(t['parity'],0)
   self.assertEqual(t['changes']['-12V']['after_sizes'],[38,977]);self.assertEqual(t['changes'][a.NET]['after_sizes'],[51])
   self.assertIn(['C2247:2','C2249:2','RB2216:2'],t['changes']['AGND']['small_after_pad_groups'])
 def test_reports(self):
  for name,t in a.read(HERE/'audit.json')['trials'].items():
   for path,sha in t['bindings'].items():
    if '/drc-' in path:self.assertEqual(a.sha(HERE/'evidence'/(name+'-'+Path(path).name)),sha)
 def test_review_bindings(self):
  for name,sha in a.read(HERE/'review-bindings.json')['sha256'].items():self.assertEqual(a.sha(a.ROOT/name),sha,name)
 def test_compose_replay(self):
  sp=importlib.util.spec_from_file_location('stage52_compose',HERE/'compose.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
  self.assertEqual(m.run(HERE/'evidence/lower-01.json',HERE/'evidence/upper-mid-005.json'),a.read(HERE/'trial1-proposal.json'))
 def test_check_never_repairs(self):
  import tempfile
  sp=importlib.util.spec_from_file_location('stage52_audit',HERE/'audit.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as name:
   source=Path(name)/'source';target=Path(name)/'target';source.write_bytes(b'expected');target.write_bytes(b'drift')
   with self.assertRaisesRegex(ValueError,'retained evidence drift'):m.retain(source,target,True)
   self.assertEqual(target.read_bytes(),b'drift');m.retain(source,target,False);m.retain(source,target,True)
 def test_diagnostic_bindings(self):
  expected={'source-half':[1015],'target-half':[15,23,977],'omit-16':[38,977],'omit-17':[38,977],'omit-25':[23,992]}
  for name,sizes in expected.items():
   d=a.read(HERE/'evidence'/('stage52-'+name+'-probe.json'));self.assertEqual(d['proposal_sha256'],a.sha(HERE/'evidence'/(name+'.json')));self.assertEqual([r['size'] for r in d['groups']['-12V']],sizes)
 def test_bridge_scope(self):
  for name in ['lower-01','upper-mid-005']:
   p=a.read(HERE/'evidence'/(name+'.json'));self.assertFalse(p['removed_uuids'])
   self.assertTrue(all(r['net']==a.NET and (r['kind']=='via' or r['layer'] in ['F.Cu','In2.Cu','B.Cu']) for r in p['copper']))
class HoleScreenTests(unittest.TestCase):
 def test_same_net_track_termination_and_foreign_holes(self):
  try:
   from shapely.geometry import LineString
   sp=importlib.util.spec_from_file_location('stage52_sites',HERE/'sites.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
  except ModuleNotFoundError:self.skipTest('Shapely source-screen dependency unavailable')
  d={'board_sha256':a.BASE,'layers':['F.Cu','In3.Cu','B.Cu'],'tracks':[],'pads':[],'keepouts':[],'edges':[],'vias':[{'uuid':'v','net':a.NET,'xy':[230000000,105000000],'diameter':600000,'drill':300000}]}
  line=LineString([(230,105),(231,105)])
  self.assertGreater(m.Screen(d).margin(line,.1,['In3.Cu'])[0],0)
  d['vias'][0]['net']='OTHER';self.assertLess(m.Screen(d).margin(line,.1,['In3.Cu'])[0],0)
 def test_new_via_hole_constraint_retained(self):
  try:
   from shapely.geometry import Point
   sp=importlib.util.spec_from_file_location('stage52_sites',HERE/'sites.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
  except ModuleNotFoundError:self.skipTest('Shapely source-screen dependency unavailable')
  d={'board_sha256':a.BASE,'layers':['F.Cu','In3.Cu','B.Cu'],'tracks':[],'pads':[],'keepouts':[],'edges':[],'vias':[{'uuid':'v','net':a.NET,'xy':[230000000,105000000],'diameter':600000,'drill':300000}]}
  self.assertLess(m.Screen(d).margin(Point(230.4,105),.3,d['layers'],True)[0],0)
if __name__=='__main__':unittest.main()
