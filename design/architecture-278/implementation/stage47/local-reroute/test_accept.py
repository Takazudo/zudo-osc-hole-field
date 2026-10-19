"""Adversarial partition controls; synthetic acceptance is not hardware evidence."""
from pathlib import Path
import copy,importlib.util,json,sys,unittest
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('stage47_accept',HERE/'accept.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

def fixture():
 objects={'source':dict(kind='pad',ref='R8270',pin='2',net='AGND'),'main':dict(kind='via',uuid=a.TARGET,net='AGND'),'retire':dict(kind='segment',uuid=a.RETIRE,net=a.NET),'signal-a':dict(kind='pad',ref='A',pin='1',net=a.NET),'signal-b':dict(kind='pad',ref='B',pin='1',net=a.NET)}
 ground=[['source'],['main']]
 for i in range(13):
  k='island'+str(i);objects[k]=dict(kind='pad',ref=k,pin='1',net='AGND');ground.append([k])
 other=[]
 for i in range(104):
  k='other'+str(i);objects[k]=dict(kind='pad',ref=k,pin='1',net='OTHER');other.append([k])
 old=dict(objects=objects,groups={'AGND':ground,a.NET:[['retire','signal-a','signal-b']],'OTHER':other},native_open_edges=117)
 new=copy.deepcopy(old);del new['objects']['retire'];new['groups']['AGND']=[['source','main','new-via']]+ground[2:];new['groups'][a.NET]=[['signal-a','signal-b']+['new'+str(i) for i in range(4)]];new['native_open_edges']=116
 copper=[]
 for i in range(4):
  k='new'+str(i);new['objects'][k]=dict(kind='segment',uuid=k,net=a.NET);copper.append(dict(uuid=k))
 new['objects']['new-via']=dict(kind='via',uuid='new-via',net='AGND');copper.append(dict(uuid='new-via'))
 return old,new,dict(copper=copper)

class AcceptanceTests(unittest.TestCase):
 def setUp(self):self.old,self.new,self.proposal=fixture()
 def test_exact_merge(self):self.assertTrue(a.connectivity(self.old,self.new,self.proposal)['accepted'])
 def test_wrong_ground_merge(self):
  self.new['groups']['AGND'][0]=['source','island0','new-via'];self.new['groups']['AGND'][1]=['main']
  with self.assertRaises(ValueError):a.connectivity(self.old,self.new,self.proposal)
 def test_other_signal_merge_even_if_count_claim_unchanged(self):
  self.new['groups']['OTHER'][0]+=self.new['groups']['OTHER'].pop()
  with self.assertRaises(ValueError):a.connectivity(self.old,self.new,self.proposal)
 def test_retained_net_changed(self):
  self.new['objects']['signal-a']['net']='AGND'
  with self.assertRaises(ValueError):a.connectivity(self.old,self.new,self.proposal)
 def test_missing_retained_object(self):
  del self.new['objects']['signal-a']
  with self.assertRaises(ValueError):a.connectivity(self.old,self.new,self.proposal)
 def test_new_only_island(self):
  self.new['groups'][a.NET][0].remove('new0');self.new['groups'][a.NET].append(['new0'])
  with self.assertRaises(ValueError):a.connectivity(self.old,self.new,self.proposal)
 def test_unexpected_added_object(self):
  self.new['objects']['extra']=dict(kind='via',uuid='extra',net='AGND')
  with self.assertRaises(ValueError):a.connectivity(self.old,self.new,self.proposal)
 def test_duplicate_component_membership(self):
  self.new['groups']['AGND'][0].append('main')
  with self.assertRaises(ValueError):a.connectivity(self.old,self.new,self.proposal)
 def test_omitted_new_object_from_groups(self):
  self.new['groups'][a.NET][0].remove('new0')
  with self.assertRaises(ValueError):a.connectivity(self.old,self.new,self.proposal)
 def test_wrong_open_count(self):
  self.new['native_open_edges']=117
  with self.assertRaises(ValueError):a.connectivity(self.old,self.new,self.proposal)
 def test_hidden_non_silk_warning_cap(self):
  d={'violations':[dict(type='via_dangling',severity='warning',items=[dict(uuid=str(i))]) for i in range(199)]}
  with self.assertRaisesRegex(ValueError,'capped warning'):a.warning_gate(d,d)
 def test_new_uncapped_warning(self):
  d={'violations':[dict(type='via_dangling',severity='warning',items=[dict(uuid='new')])]}
  with self.assertRaises(ValueError):a.warning_gate({'violations':[]},d)
 def test_existing_silk_cap_explicitly_unresolved(self):
  d={'violations':[dict(type='silk_overlap',severity='warning',items=[dict(uuid=str(i))]) for i in range(199)]}
  self.assertEqual(a.warning_gate(d,d)['capped_silkscreen_identity_nonregression'],'UNRESOLVED')
 def test_local_false_retirement_contract(self):
  base=a.ROOT/'.circuit-cache/stage44-b2-fresh/osc-jack-left.kicad_pcb';proposal=a.ROOT/'.circuit-cache/stage47/proposal.json'
  if not base.exists() or not proposal.exists():self.skipTest('ignored native inputs unavailable')
  p=a.read(proposal);p['retirements'][0]['contract'][-1]='AGND'
  with self.assertRaisesRegex(ValueError,'retirement metadata/geometry'):a.identity(base.read_text(),base.read_text(),p)
 def test_local_false_removed_allowlist(self):
  base=a.ROOT/'.circuit-cache/stage44-b2-fresh/osc-jack-left.kicad_pcb';proposal=a.ROOT/'.circuit-cache/stage47/proposal.json'
  if not base.exists() or not proposal.exists():self.skipTest('ignored native inputs unavailable')
  p=a.read(proposal);p['removed_uuids'].append('unapproved')
  with self.assertRaisesRegex(ValueError,'retirement metadata/geometry'):a.identity(base.read_text(),base.read_text(),p)
 def test_local_saved_board_replay(self):
  base=a.ROOT/'.circuit-cache/stage44-b2-fresh';candidate=a.ROOT/'.circuit-cache/stage47-trial2';proposal=a.ROOT/'.circuit-cache/stage47/proposal.json'
  paths=[base/'osc-jack-left.kicad_pcb',base/'connectivity-passfresh.json',candidate/'osc-jack-left.kicad_pcb',candidate/'connectivity-pass1.json',proposal]
  if not all(p.exists() for p in paths):self.skipTest('ignored native replay artifacts unavailable')
  p=a.read(proposal)
  self.assertTrue(a.identity(paths[0].read_text(),paths[2].read_text(),p)['accepted'])
  self.assertTrue(a.connectivity(a.read(paths[1]),a.read(paths[3]),p)['accepted'])
if __name__=='__main__':unittest.main()
