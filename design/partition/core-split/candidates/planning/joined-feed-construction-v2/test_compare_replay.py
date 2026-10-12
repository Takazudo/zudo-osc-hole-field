import copy,gzip,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import compare_replay as cr

PADS=['p1','p2','p3','p4','p5','p6','p7']
CLOSES=dict(zip(cr.ROUNDS,PADS))     # each round closes one pad; p7 stays unresolved

def obj(i,pad=None,width=.25):return {'id':i,'kind':'segment','net':'AGND','width_mm':width,'access_for_pad':pad}

class Fixture:
 """A complete, mutually consistent retained-evidence directory and replay directory."""
 def __init__(self):
  self.root=Path(tempfile.mkdtemp());self.ev=self.root/'ev';self.run=self.root/'run';self.ev.mkdir();self.run.mkdir()
  base=[obj('n1'),obj('n2')]
  self.wj(self.run/'KA-normalized.json',{'objects':base,'loads':[],'input_sha256':'x'})
  residual=list(PADS);objects=list(base);rounds={};deltas={f:[] for f in cr.SPANS}
  self.eval('base',residual);rounds['base']=self.counts(residual)
  for r in cr.ROUNDS:
   pad=CLOSES[r];new=obj('a-'+r,pad);objects=objects+[new]
   deltas[cr.span_of(r)].append(new)
   report={'board':'KA','input_sha256':{'/abs/'+r:'h'},'parameters_mm':{},'results':[{'pad_id':p,'status':'ROUTED' if p==pad else 'NO_ROUTE'} for p in residual]}
   self.wj(self.run/f'KA-access-{r}.json',{'objects':objects});self.wj(self.run/f'KA-access-{r}-report.json',report)
   self.wgz(self.ev/f'KA-access-{r}-report.json.gz',dict(report,input_sha256={'/other/'+r:'h'}))
   residual=[p for p in residual if p!=pad];self.eval(r,residual)
   rounds[r]=self.counts(residual)
   if r in ('r4','t1','t2'):rounds[r]['closed_identities']=[{'pad_id':pad}]
  for f,objs in deltas.items():self.wgz(self.ev/f.replace('K-','KA-',1),objs)
  for r,res in (('r3',PADS[3:]),('t2',PADS[6:])):
   self.wj(self.ev/f'KA-{r}-port-obligations.json',self.census(res,'/other'))
   self.wgz(self.ev/f'KA-{r}-port-graph.json.gz',self.graph(r,'/other'))
  self.wj(self.ev/'index.json',{'boards':{'KA':{'rounds':rounds}}})
  norm=self.rj(self.run/'KA-normalized.json');(self.ev/'replay/20261013-r4-t2').mkdir(parents=True)
  self.wj(self.ev/'replay/20261013-r4-t2/KA-replay-comparison.json',{'checks':{'normalized_objects':{'objects':2,'loads':0,'content_sha256':cr.digest(cr.strip(norm))}}})
 def counts(self,res):return {'unresolved':len(res),'direct':len(res),'supplemental':0}
 def census(self,res,where):return {'unresolved':[{'pad_id':p} for p in res],'physical_pad_count':len(PADS),'input_sha256':{where:'s'},'graph_sha256':where}
 def graph(self,r,where):return {'physical_ports':[{'id':p} for p in PADS],'round':r,'input_sha256':{where:'s'}}
 def eval(self,r,res):
  d=self.run/f'KA-eval-{r}';d.mkdir()
  self.wj(d/'evaluation.json',{'unresolved_physical_pad_count':len(res),'unresolved_direct_load_count':len(res),'unresolved_supplemental_count':0})
  self.wj(d/'port-obligations.json',self.census(res,'/abs'));self.wj(d/'port-graph.json',self.graph(r,'/abs'))
 def wj(self,p,d):p.write_text(json.dumps(d))
 def wgz(self,p,d):p.write_bytes(gzip.compress(json.dumps(d).encode()))
 def rj(self,p):return json.loads(p.read_text())
 def rgz(self,p):return json.loads(gzip.decompress(p.read_bytes()))
 def cli(self,*extra):return cr.main(['--run',str(self.run),'--board','KA','--evidence',str(self.ev),*extra])

class CompareReplay(unittest.TestCase):
 def setUp(self):self.f=Fixture()
 def result(self,rounds=cr.ROUNDS):return cr.compare('KA',self.f.run,self.f.ev,list(rounds))
 def test_consistent_replay_passes_through_t2_and_cli_exits_zero(self):
  out=self.result();self.assertTrue(out['all_equal'],out['failed'])
  self.assertTrue(out['checks']['span_K-access-delta-r4-t2.json.gz_equal']);self.assertEqual(self.f.cli(),0)
 def test_through_r3_needs_no_r4_t2_delta(self):
  (self.f.ev/'KA-access-delta-r4-t2.json.gz').unlink()
  self.assertTrue(self.result(cr.ROUNDS[:3])['all_equal'])
 def test_same_count_identity_swap_fails(self):
  p=self.f.run/'KA-eval-r2/port-obligations.json';d=self.f.rj(p)
  d['unresolved'][0]['pad_id']='p1'                        # p3 replaced by already-closed p1: same count
  self.f.wj(p,d);out=self.result()
  self.assertFalse(out['all_equal']);self.assertIn('r2.residual_identities_equal',out['failed'])
  self.assertTrue(out['rounds']['r2']['counts_equal'],'the count alone would have passed')
  self.assertEqual(self.f.cli(),1)
 def test_final_census_identity_swap_fails(self):
  for p in (self.f.run/'KA-eval-t2/port-obligations.json',):
   d=self.f.rj(p);d['unresolved']=[{'pad_id':'p6'}];self.f.wj(p,d)
  out=self.result();self.assertIn('t2.residual_identities_equal',out['failed']);self.assertIn('final_census_equal_excluding_seals',out['failed'])
 def test_altered_copper_in_later_round_fails(self):
  for r in ('r4','t1','t2'):
   p=self.f.run/f'KA-access-{r}.json';d=self.f.rj(p)
   for o in d['objects']:
    if o['id']=='a-r4':o['width_mm']=.2
   self.f.wj(p,d)
  out=self.result();self.assertIn('r4.added_objects_in_own_span_delta',out['failed'])
  self.assertIn('span_K-access-delta-r4-t2.json.gz_equal',out['failed'])
 def test_changed_base_copper_fails_even_if_connectivity_is_unchanged(self):
  p=self.f.run/'KA-normalized.json';d=self.f.rj(p);d['objects'][1]['width_mm']=.3;self.f.wj(p,d)
  for r in cr.ROUNDS:                                  # keep every later round consistent with the altered base
   q=self.f.run/f'KA-access-{r}.json';e=self.f.rj(q);e['objects'][1]['width_mm']=.3;self.f.wj(q,e)
  out=self.result();self.assertIn('normalized_content_equals_retained',out['failed']);self.assertEqual(self.f.cli(),1)
 def test_rewritten_prior_object_fails_prefix(self):
  p=self.f.run/'KA-access-t1.json';d=self.f.rj(p);d['objects'][0]['width_mm']=.3;self.f.wj(p,d)
  self.assertIn('t1.source_objects_prefix_preserved',self.result()['failed'])
 def test_missing_delta_bundle_fails_cli(self):
  (self.f.ev/'KA-access-delta-r4-t2.json.gz').unlink()
  self.assertEqual(self.f.cli(),1)
 def test_duplicate_or_cross_span_delta_ids_fail(self):
  p=self.f.ev/'KA-access-delta.json.gz';d=self.f.rgz(p);self.f.wgz(p,d+[copy.deepcopy(d[0])])
  self.assertEqual(self.f.cli(),1)
  self.f=Fixture();p=self.f.ev/'KA-access-delta-r4-t2.json.gz';d=self.f.rgz(p);self.f.wgz(p,d+[obj('a-r1','p1')])
  self.assertEqual(self.f.cli(),1)
 def test_retained_delta_with_unproduced_object_fails(self):
  p=self.f.ev/'KA-access-delta-r4-t2.json.gz';self.f.wgz(p,self.f.rgz(p)+[obj('ghost','p6')])
  self.assertIn('span_K-access-delta-r4-t2.json.gz_equal',self.result()['failed'])
 def test_newly_disconnected_identity_fails(self):
  p=self.f.run/'KA-eval-r4/port-obligations.json';d=self.f.rj(p);d['unresolved'].append({'pad_id':'p1'});self.f.wj(p,d)
  out=self.result();self.assertIn('r4.newly_disconnected',out['failed']);self.assertIn('r4.residual_identities_equal',out['failed'])
 def test_changed_report_fails_and_legacy_allowance_is_exact(self):
  p=self.f.run/'KA-access-r2-report.json';d=self.f.rj(p)
  for x in d['results']:x['new_via']=False
  self.f.wj(p,d);out=self.result();self.assertTrue(out['all_equal'],out['failed'])
  self.assertEqual(out['rounds']['r2']['documented_legacy_report_fields_removed'],['results[].new_via'])
  for x in d['results']:x['new_via']=True                  # a different value is not the documented addition
  self.f.wj(p,d);self.assertIn('r2.access_report_equal_excluding_seals',self.result()['failed'])
  self.f=Fixture();p=self.f.run/'KA-access-t2-report.json';d=self.f.rj(p);d['results'][-1]['status']='ROUTED'
  self.f.wj(p,d);self.assertIn('t2.access_report_equal_excluding_seals',self.result()['failed'])

if __name__=='__main__':unittest.main()
