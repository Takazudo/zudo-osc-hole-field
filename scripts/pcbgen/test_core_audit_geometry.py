import copy,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from scripts.pcbgen import audit_fixture_tasks as a,core_audit_geometry as g
class GeometryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.paths=[];self.ids=['601e02b2-8ccb-5c28-83e5-03789d47fbbd',g.TARGET[0]];self.kernel={'image':a.IMAGE,'version':a.VERSION}
  for stage in (0,1):
   path=self.root/str(stage)/'osc-core.kicad_pcb';path.parent.mkdir();path.write_text('(kicad_pcb '+ ' '.join('(zone (uuid "'+uid+'") (layer "'+layer+'") (polygon (pts (xy '+str(stage)+' 0))))' for uid,layer in zip(self.ids,['F.Cu','B.Cu']))+')');self.paths.append(path)
   for suffix in ('.kicad_pro','.kicad_dru'):path.with_suffix(suffix).write_text('{}')
  paths,raw,texts,ctx=a.sources(*self.paths);self.m=dict(source_sha256=[a.SHA(b) for b in raw],context_sha256={s:a.SHA(v) for s,v in ctx.items()},tasks=[])
  for stage in (0,1):
   for uid,layer in zip(self.ids,['F.Cu','B.Cu']):self.m['tasks'].append(dict(zone_uuid=uid,layer=layer,stage=stage,expected_geometry=dict(method='exact_native_coordinates_no_arcs',source_board_sha256=self.m['source_sha256'][stage],zone_uuid=uid,layer=layer,source_zone_bytes_sha256=a.SHA(a.zone_blocks(texts[stage])[uid].encode()))))
  self.rule_area=False;self.arcs=False;self.net='AGND';self.layers=False;self.loads=[]
  owner=self
  class Poly:
   def __init__(self,uid,stage):self.uid=uid;self.stage=stage
   def ArcCount(self):return int(owner.arcs)
   def Format(self):return self.uid+str(self.stage)
  def zone(uid,layer,stage):return SimpleNamespace(m_Uuid=SimpleNamespace(AsString=lambda:uid),GetIsRuleArea=lambda:owner.rule_area,GetLayerSet=lambda:SimpleNamespace(Seq=lambda:[layer,8] if owner.layers else [layer]),GetNetname=lambda:owner.net,GetFilledPolysList=lambda lid:Poly(uid,stage))
  def load(path):
   stage=int(Path(path).parent.name);owner.loads.append(stage);return SimpleNamespace(Zones=lambda:[zone(owner.ids[0],0,stage),zone(owner.ids[1],2,stage)])
  self.native=SimpleNamespace(F_Cu=0,B_Cu=2,GetBuildVersion=lambda:a.VERSION,LoadBoard=load,SaveBoard=lambda *args:(_ for _ in ()).throw(AssertionError('must never save')),ZONE_FILLER=lambda *args:(_ for _ in ()).throw(AssertionError('must never refill')))
 def snap(self):
  with patch.object(a,'validate_manifest'),patch.object(g.subprocess,'check_output',return_value=a.VERSION):return g.snapshot(self.m,*self.paths,self.kernel,self.native)
 def receipt(self):
  snap=self.snap();target=a.identity(g.references(self.m)[g.TARGET]);bindings={r['reference_sha256']:r['signature'] for r in snap['rows'] if r['reference_sha256']!=target};receipt=dict(independent_reloads=[snap,copy.deepcopy(snap)],completed_drc_tasks=0,refilled=False,saved=False,rerouted=False);return receipt,bindings
 def test_readonly_two_boards_controls_and_after_binding_without_tasks(self):
  receipt,bindings=self.receipt();out=g.validate_receipt(self.m,self.kernel,bindings,receipt);self.assertEqual(self.loads,[0,1]);self.assertEqual(out['completed_drc_tasks'],0);self.assertTrue(out['requires_stage_review']);self.assertEqual(out['reference'],g.references(self.m)[g.TARGET])
 def test_fake_matches_digest_pinned_zone_binding_contract(self):
  contract=json.loads((Path(__file__).parent/'core_audit_geometry_api_contract.json').read_bytes())
  self.assertEqual(contract['image'],a.IMAGE)
  self.assertIn('GetIsRuleArea',contract['classes']['ZONE'])
  zone=self.native.LoadBoard(str(self.paths[0])).Zones()[0]
  self.assertFalse(hasattr(zone,'IsRuleArea'))
  for method in ('GetIsRuleArea','GetLayerSet','GetNetname','GetFilledPolysList'):
   self.assertIn(method,contract['classes']['ZONE']);self.assertTrue(callable(getattr(zone,method)))
  self.assertEqual(contract['classes']['ZONE']['GetLayerSet']['declared_by'],'BOARD_ITEM')
  self.assertEqual(contract['classes']['ZONE']['GetNetname']['declared_by'],'BOARD_CONNECTED_ITEM')
 def test_wrong_net_layer_arcs_version_or_context_rejected(self):
  for field,value in [('rule_area',True),('net','wrong'),('layers',True),('arcs',True)]:
   setattr(self,field,value)
   with self.assertRaises(ValueError):self.snap()
   setattr(self,field,{'rule_area':False,'net':'AGND','layers':False,'arcs':False}[field])
  with patch.object(a,'validate_manifest'),patch.object(g.subprocess,'check_output',return_value='9.0.2'):
   with self.assertRaises(ValueError):g.snapshot(self.m,*self.paths,self.kernel,self.native)
 def test_reload_disagreement_controls_and_scope_mutations(self):
  receipt,bindings=self.receipt()
  for mutate in (lambda r:r['independent_reloads'][1]['rows'][0].update(signature='a'*64),lambda r:r.update(completed_drc_tasks=1),lambda r:r.update(saved=True),lambda r:r['independent_reloads'][0]['context_sha256'].update(x='changed')):
   r=copy.deepcopy(receipt);mutate(r)
   with self.assertRaises(ValueError):g.validate_receipt(self.m,self.kernel,bindings,r)
  bad=dict(bindings);bad[next(iter(bad))]='f'*64
  with self.assertRaisesRegex(ValueError,'controls'):g.validate_receipt(self.m,self.kernel,bad,receipt)
if __name__=='__main__':unittest.main()
