"""Adversarial additive-scope/partition controls; no physical claims."""
from pathlib import Path
import copy,importlib.util,json,sys,unittest
from collections import Counter
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('stage53_accept',HERE/'accept.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
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
 def test_actual_native_gate_absolute_paths(self):
  base=a.ROOT/'.circuit-cache/stage49-fresh';candidate=a.ROOT/'.circuit-cache/stage53-trial1'
  if not (candidate/'connectivity-pass1.json').exists():self.skipTest('ignored native inputs unavailable')
  self.assertEqual(a.evaluate(base,candidate,HERE/'trial1-proposal.json','pass1'),a.read(candidate/'acceptance-pass1.json'))
 def test_settlement_and_retained_evidence(self):
  d=a.read(HERE/'settlement.json');self.assertTrue(d['accepted_bounded_native_repair']);self.assertEqual(d['independent_native_builds'],2)
  self.assertEqual(d['connectivity']['new_opens'],115);self.assertEqual(d['connectivity']['added_objects'],21)
  self.assertEqual(d['drc']['rule_errors'],0);self.assertEqual(d['drc']['parity'],0)
  for path,sha in d['evidence_sha256'].items():
   if '/stage53-' in path and ('/drc-' in path or '/acceptance-' in path):
    folder=Path(path).parent.name.replace('stage53-','');self.assertEqual(a.sha(HERE/'evidence'/(folder+'-'+Path(path).name)),sha)
 def test_review_bindings(self):
  for name,sha in a.read(HERE/'review-bindings.json')['sha256'].items():self.assertEqual(a.sha(a.ROOT/name),sha,name)
 def test_scope(self):
  p=a.read(HERE/'trial1-proposal.json');self.assertFalse(p['removed_uuids']);self.assertEqual(len(p['copper']),21)
  self.assertTrue(all(r['net']==a.NET for r in p['copper']))
  self.assertEqual(Counter(r.get('layer','via') for r in p['copper']),Counter({'In4.Cu':19,'B.Cu':1,'via':1}))
  v=next(r for r in p['copper'] if r['kind']=='via');self.assertEqual((v['diameter_nm'],v['drill_nm']),(600000,300000))
 def test_search_source_evidence(self):
  d=a.read(HERE/'evidence/coarse.search.json');self.assertEqual(d['parameters']['allowed_layers'],['In4.Cu'])
  self.assertTrue(all(r['path'] for r in d['results']));self.assertEqual(a.read(HERE/'evidence/coarse.json'),a.read(HERE/'trial1-proposal.json'))
 def test_in4_preflight_not_acceptance(self):
  d=a.read(HERE/'preflight.json');self.assertEqual(d['baseline_plus12_groups'],[1025]);self.assertEqual(len(d['exits']),6)
  self.assertTrue(d['seed_retained_partitions_unchanged']);self.assertGreater(d['entry_clearance_surplus_mm'],0)
  self.assertEqual(a.read(HERE/'topology.json')['results'][1]['components'],1)
 def test_all_actual_partitions(self):
  base=a.ROOT/'.circuit-cache/stage49-fresh/connectivity-passfresh.json';new=a.ROOT/'.circuit-cache/stage53-trial1/connectivity-pass1.json'
  if not base.exists() or not new.exists():self.skipTest('ignored native snapshots unavailable')
  old=a.read(base);after=a.read(new);p=a.read(HERE/'trial1-proposal.json');a.connectivity(old,after,p)
  # An otherwise matching snapshot with one detached supply member must reject.
  group=after['groups']['+12V'][0];after['groups']['+12V'].append([group.pop()]);after['native_open_edges']+=1
  with self.assertRaisesRegex(ValueError,'unexpected partition: [+]12V'):a.connectivity(old,after,p)
 def test_balanced_partition_regression(self):
  base=a.ROOT/'.circuit-cache/stage49-fresh/connectivity-passfresh.json';new=a.ROOT/'.circuit-cache/stage53-trial1/connectivity-pass1.json'
  if not base.exists() or not new.exists():self.skipTest('ignored native snapshots unavailable')
  old=a.read(base);after=a.read(new);p=a.read(HERE/'trial1-proposal.json')
  group=after['groups']['+12V'][0];after['groups']['+12V'].append([group.pop()])
  after['groups']['AGND'][0]+=after['groups']['AGND'].pop()
  self.assertEqual(after['native_open_edges'],115);a.validate_snapshot(after)
  with self.assertRaisesRegex(ValueError,'unexpected partition: [+]12V'):a.connectivity(old,after,p)
if __name__=='__main__':unittest.main()
