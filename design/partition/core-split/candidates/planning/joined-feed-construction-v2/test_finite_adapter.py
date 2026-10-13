"""Real small fixtures for the E16 finite adapter and coupled solver.

Tolerances were declared before results were inspected (coupled-network-config.json
numerical_tolerances); analytic 1-D fixtures use 1-3 % for P1 discretisation.
"""
import copy,gzip,hashlib,json,math,sys,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import shapely
sys.path.insert(0,str(Path(__file__).resolve().parent))
import connectivity,fragments as F,finite_adapter as A,finite_units as U,finite_solve as S
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
CASE=dict(rho_ohm_mm=2e-5,inner_copper_mm=.07,outer_copper_mm=.07,barrel_plating_mm=.018)
UNIFORM={'foil_mm':.07,'dielectric_mm':[.236]*5,'board_mm':1.6}
UPPER=dict(UNIFORM,legacy_leg_mm=1.6)
RS=CASE['rho_ohm_mm']/CASE['outer_copper_mm']
def rect(x0,y0,x1,y1):return [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]
def pad(i,net,poly,layers=('B.Cu',),**k):
 x0,y0=np.min(poly,axis=0);x1,y1=np.max(poly,axis=0);return dict(id=i,kind='pad',net=net,layers=list(layers),polygon_mm=poly,center_mm=[(x0+x1)/2,(y0+y1)/2],ref=k.get('ref',i),pad=k.get('pad','1'))
def seg(i,net,a,b,w,layer='B.Cu'):return dict(id=i,kind='segment',net=net,layers=[layer],path_mm=[a,b],width_mm=w)
def via(i,net,x,y):return dict(id=i,kind='via',net=net,layers=LAYERS,center_mm=[x,y],diameter_mm=.6,drill_mm=.3)
def sheet(i,poly,holes=()):return dict(id=i,polygon_mm=poly,holes_mm=list(holes))
def operator(objects,sheets,net,pitch=1.,face=.25,origin=(0.,0.)):
 src={'board':'KA','objects':objects,'loads':[]};planes={'board':'KA','new_objects':[],'clipped_sheets':{net:sheets}}
 frag=F.NetFragments(src,planes,net);desc=A.describe(frag);items=[A.mesh_item(desc,g,t,pitch,face,origin) for g,t in A.tiles(desc,pitch,6.,origin)]
 return frag,desc,A.Assembly(desc,items)
def two_point(asm,a,b,depth=UNIFORM):
 """Average-potential resistance between two finite supports under unit current."""
 K,_,rec=asm.matrix(CASE,depth);(na,wa),(nb,wb)=asm.supports[a],asm.supports[b];f=np.zeros(asm.N);f[na]+=wa;f[nb]-=wb
 keep=np.arange(1,asm.N);v=np.zeros(asm.N);v[keep]=spla.spsolve(K[keep][:,keep].tocsc(),f[keep])
 return float(wa@v[na]-wb@v[nb]),rec,K,v,f

class Adapter(unittest.TestCase):
 def test_strip_matches_1d_with_finite_pad_supports(self):
  # 1 mm strip: pads [-1,1] and [11,13], trace between; uniform-injection pads add a/3 each.
  objs=[pad('CS247-KA-W1','+12V',rect(-1,0,1,1)),pad('L','+12V',rect(11,0,13,1)),seg('s','+12V',[1,.5],[11,.5],1.)]
  _,_,asm=operator(objs,[],'+12V');R,_,K,v,f=two_point(asm,'L','CS247-KA-W1')
  self.assertAlmostEqual(R,RS*(10+2/3+2/3),delta=.01*RS*11.33)
  self.assertAlmostEqual(asm.receipts['area_mm2'],14.,places=6)
  self.assertGreaterEqual(float(v@(K@v)),0.)
 def test_narrow_neck_kept_and_dominant(self):
  # A 0.1 mm neck is narrower than every cell; the raster model dropped such paths.
  objs=[pad('CS247-KA-W1','+12V',rect(-1,-1,1,1)),pad('L','+12V',rect(3,-1,5,1)),seg('n','+12V',[1,0],[3,0],.1)]
  _,_,asm=operator(objs,[],'+12V');R,*_=two_point(asm,'L','CS247-KA-W1')
  # 20 squares of neck plus a constriction at each abrupt 2 mm -> 0.1 mm step, bounded by (ln(W/w)+1)/pi squares per end.
  self.assertGreater(R,RS*20);self.assertLess(R,RS*(20+2*(math.log(20)+1)/math.pi))
  fine,*_=two_point(operator(objs,[],'+12V',face=.125)[2],'L','CS247-KA-W1');self.assertLess(abs(fine-R)/R,.02)
 def test_mid_span_t_attaches_at_its_actual_junction(self):
  objs=[pad('CS247-KA-W1','+12V',rect(-1,0,0,1)),pad('B','+12V',rect(10,0,11,1)),seg('s','+12V',[0,.5],[10,.5],1.),
        seg('t','+12V',[5,1],[5,6],1.),pad('C','+12V',rect(4.5,6,5.5,7))]
  _,desc,asm=operator(objs,[],'+12V')
  rA,*_=two_point(asm,'C','CS247-KA-W1');rB,*_=two_point(asm,'C','B')
  self.assertAlmostEqual(rA,rB,delta=1e-3*rA)                       # symmetric T: junction is mid-span, not a snapped end
  self.assertEqual(len(desc['groups']),1)
 def test_split_object_keeps_only_its_fed_fragment(self):
  # A foreign drill splits pad P; only the fragment touching the fed trace carries current.
  objs=[pad('CS247-KA-W1','+12V',rect(-1,0,0,1)),seg('s','+12V',[0,.5],[3,.5],1.),pad('P','+12V',rect(3,0,6,1)),via('x','AGND',4.,.5)]
  objs[-1]['diameter_mm']=1.2;objs[-1]['drill_mm']=1.1
  frag,desc,asm=operator(objs,[],'+12V')
  rows=desc['fragment_ledger']['P'];self.assertEqual(len(rows),2);self.assertEqual(sorted(r['fed'] for r in rows),[False,True])
  self.assertFalse(frag.connection('P')['all_fragments_connected_to_feed'])
  n,w=asm.supports['P'];self.assertAlmostEqual(w.sum(),1.,places=12)
 def test_tangent_groups_are_not_joined(self):
  objs=[pad('CS247-KA-W1','+12V',rect(0,0,1,1)),pad('Q','+12V',rect(1,0,2,1))]   # share an edge, zero overlap
  frag,desc,asm=operator(objs,[],'+12V')
  self.assertNotIn('Q',asm.supports);self.assertFalse(desc['fragment_ledger']['Q'][0]['fed'])
 def test_inner_layer_path_and_barrel_intervals_at_declared_depths(self):
  objs=[pad('CS247-KA-W1','+12V',rect(-.5,-.5,.5,.5)),via('v1','+12V',0,0),pad('L','+12V',rect(9.5,-.5,10.5,.5)),via('v2','+12V',10,0)]
  sh=[sheet('KA-+12V-SHEET-0000',rect(-1,-1,11,1))]
  _,desc,asm=operator(objs,sh,'+12V')
  r_u,rec,*_=two_point(asm,'L','CS247-KA-W1');r_l,rec_l,*_=two_point(asm,'L','CS247-KA-W1',UPPER)
  z=A.layer_z(UNIFORM);self.assertTrue(all(abs(r[3]-(z['B.Cu']-z['In4.Cu']))<1e-12 for r in rec if r[1:3]==('In4.Cu','B.Cu')))
  per=lambda L:A.barrel_interval_ohm(CASE['rho_ohm_mm'],L,.3,CASE['barrel_plating_mm'])
  # Each through via also taps its non-functional annuli: five intervals partition F..B once; only In4-B carries this current.
  for v in ('v1','v2'):
   mine=sorted((z[r[1]],z[r[2]]) for r in rec if r[0]==v);self.assertEqual(len(mine),5)
   self.assertTrue(all(a[1]==b[0] for a,b in zip(mine,mine[1:])));self.assertAlmostEqual(sum(b-a for a,b in mine),z['B.Cu']-z['F.Cu'],places=12)
  self.assertAlmostEqual(r_l-r_u,2*(per(1.6)-per(z['B.Cu']-z['In4.Cu'])),delta=1e-9*r_l)
 def test_shared_barrel_interval_is_owned_once(self):
  objs=[pad('CS247-KA-W1','+12V',rect(9.5,-.5,10.5,.5)),via('vt','+12V',10,0),via('v','+12V',0,0),
        pad('LF','+12V',rect(-.5,-.5,.5,.5),layers=('F.Cu',)),pad('LB','+12V',rect(-.5,-.5,.5,.5))]
  _,desc,asm=operator(objs,[sheet('KA-+12V-SHEET-0000',rect(-1,-1,11,1))],'+12V');_,_,rec=asm.matrix(CASE,UNIFORM)
  # One chain per barrel: consecutive taps only, no interval charged twice, and none spanning a tap.
  z=A.layer_z(UNIFORM);mine=sorted((z[r[1]],z[r[2]]) for r in rec if r[0]=='v')
  self.assertEqual(len(mine),len(set(mine)));self.assertTrue(all(a[1]==b[0] for a,b in zip(mine,mine[1:])))
  self.assertAlmostEqual(sum(b-a for a,b in mine),z['B.Cu']-z['F.Cu'],places=12)
 def test_refinement_and_shifted_origin_change_little(self):
  objs=[pad('CS247-KA-W1','+12V',rect(-.5,-.5,.5,.5)),via('v1','+12V',0,0),pad('L','+12V',rect(9.5,-.5,10.5,.5)),via('v2','+12V',10,0)]
  sh=[sheet('KA-+12V-SHEET-0000',rect(-1,-1.5,11,1.5),[[[4,-.2],[6,-.2],[6,.2],[4,.2]]])]
  base,*_=two_point(operator(objs,sh,'+12V')[2],'L','CS247-KA-W1')
  fine,*_=two_point(operator(objs,sh,'+12V',pitch=.5,face=.125)[2],'L','CS247-KA-W1')
  shift,*_=two_point(operator(objs,sh,'+12V',origin=(.37,.21))[2],'L','CS247-KA-W1')
  self.assertLess(abs(fine-base)/base,.05);self.assertLess(abs(shift-base)/base,.05)

class ReviewRegressions(unittest.TestCase):
 def loop(self,touch):
  # T and L are joined by a long 0.2 mm loop; they also touch each other along an edge or at a corner only.
  L=rect(1,0,2,1) if touch=='edge' else rect(1,1,2,2)
  objs=[pad('CS247-KA-W1','+12V',rect(0,0,1,1)),pad('L','+12V',L),seg('a','+12V',[.5,.5],[.5,6],.2),seg('b','+12V',[.5,6],[1.5,6],.2),seg('c','+12V',[1.5,6],[1.5,(L[0][1]+L[2][1])/2],.2)]
  frag,desc,asm=operator(objs,[],'+12V');return two_point(asm,'L','CS247-KA-W1')[0],desc
 def test_tangent_edge_and_point_contacts_do_not_conduct(self):
  for touch,squares in (('edge',(5.5+1+5.5)/.2),('point',(5.5+1+4)/.2)):
   R,desc=self.loop(touch);self.assertEqual(len(desc['groups']),1);self.assertGreaterEqual(desc['groups'][0]['tangent_slits'],1)
   self.assertGreater(R,.8*RS*squares,touch);self.assertLess(desc['groups'][0]['slit_area_mm2'],1e-4)
 def test_supports_are_unit_partitions_and_held_nodes_stay_inside_their_land(self):
  objs=[pad('CS247-KA-W1','+12V',rect(-.5,-.5,.5,.5)),via('v1','+12V',0,0),pad('L','+12V',rect(9.5,-.5,10.5,.5)),via('v2','+12V',10,0)]
  _,desc,asm=operator(objs,[sheet('KA-+12V-SHEET-0000',rect(-1,-1,11,1))],'+12V')
  for pid,poly in (('L',rect(9.5,-.5,10.5,.5)),('CS247-KA-W1',rect(-.5,-.5,.5,.5))):
   n,w=asm.supports[pid];self.assertAlmostEqual(w.sum(),1.,places=12);inside=asm.support_inside[pid];self.assertGreaterEqual(inside.sum(),3)
   self.assertTrue(all(shapely.Polygon(poly).buffer(1e-6).covers(shapely.Point(q)) for q in asm.node_xy[n[inside]]),pid)
   self.assertTrue(np.isnan(asm.node_xy[n[~inside]]).any() or not all(shapely.Polygon(poly).buffer(1e-6).covers(shapely.Point(q)) for q in asm.node_xy[n[~inside]]))
 def test_coaxial_bores_fail_closed(self):
  objs=[pad('CS247-KA-W1','+12V',rect(-.5,-.5,.5,.5)),via('v1','+12V',0,0),via('v1b','+12V',0,0)]
  with self.assertRaises(ValueError):operator(objs,[sheet('KA-+12V-SHEET-0000',rect(-1,-1,3,1))],'+12V')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Coupled(unittest.TestCase):
 """Two synthetic boards with all four nets, run through the real units; reduction vs monolithic."""
 @classmethod
 def setUpClass(cls):
  cls.d=Path(tempfile.mkdtemp());cfg=json.loads((Path(__file__).parent/'evidence/e16/coupled-network-config.json').read_text())
  cases={'cases':{'c':CASE}};(cls.d/'cases.json').write_text(json.dumps(cases))
  band={'+12V':(0,2,'In4.Cu'),'-12V':(4,6,'In3.Cu'),'+5V':(8,10,'In2.Cu'),'AGND':(12,16,'In1.Cu')}
  records=[];lands={}
  for b in ('KA','KB'):
   objs=[];sheets={};loads=[]
   for net,(y0,y1,_) in band.items():
    ym=(y0+y1)/2;sheets[net]=[sheet(f'{b}-{net}-SHEET-0000',rect(-1,y0,21,y1))]
    ws={'+12V':[(1,1)],'-12V':[(2,1)],'+5V':[(3,1)],'AGND':[(4,1),(5,10),(6,19)]}[net]
    for w,x in ws:objs+=[pad(f'CS247-{b}-W{w}',net,rect(x-.5,ym-.5,x+.5,ym+.5)),via(f'{b}-tv{w}',net,x,ym)]
    for k,x in enumerate((7,15)):
     pid=f'{b}-L{net}-{k}';ref=f'U{k if net in ("+12V","-12V") else k+2}';pin={'+12V':'4','-12V':'11','+5V':'14','AGND':'7'}[net]
     objs+=[pad(pid,net,rect(x-.5,ym-.5,x+.5,ym+.5),layers=('F.Cu',),ref=ref,pad=pin),via(f'{b}-lv{net}{k}',net,x,ym)];loads.append({'pad_id':pid,'net':net})
     I={'+12V':.01,'-12V':-.01,'+5V':.002,'AGND':-.002}[net]*(k+1);records.append({'scenario_id':'normal-typ-v1','board':b,'net':net,'pad_id':pid,'ref':ref,'pad':pin,'pad_class':'ic_supply_pin','current_A':I,'provenance':'supported_pin_current'})
    if b=='KA':
     pid=f'KA-LAND{net}';objs+=[pad(pid,net,rect(10.5,ym-.5,11.5,ym+.5),layers=('F.Cu',),ref='TP'),via('KA-landv'+net,net,11,ym)];lands[net]=[{'ref':'TP','pad_id':pid}]
   src={'board':b,'objects':objs,'loads':loads};planes={'board':b,'new_objects':[],'clipped_sheets':sheets,'input_sha256':{}}
   sp_=cls.d/f'{b}-src.json';pp=cls.d/f'{b}-planes.json';sp_.write_text(json.dumps(src));pp.write_text(json.dumps(planes))
   g=connectivity.build(src,planes);g['input_sha256']={str(sp_):sha(sp_),str(pp):sha(pp)};gp=cls.d/f'{b}-graph.json';gp.write_text(json.dumps(g))
   un=[{'pad_id':p['id']} for p in g['physical_ports'] if not p['all_port_fragments_connected_to_feed']]
   cp=cls.d/f'{b}-census.json';cp.write_text(json.dumps({'board':b,'graph_sha256':sha(gp),'unresolved':un}))
   U.main(['split','--planes',str(pp),'--outdir',str(cls.d)])
   for net in band:
    (cls.d/f'planes-{net}.json.gz').rename(cls.d/f'{b}-planes-{net}.json.gz')
    desc=cls.d/f'{b}-desc-{net}.json.gz'
    U.main(['describe','--source',str(sp_),'--planes',str(cls.d/f'{b}-planes-{net}.json.gz'),'--graph',str(gp),'--census',str(cp),f'--net={net}','--output',str(desc)])
    plan=cls.d/f'{b}-plan-{net}.json';U.main(['plan','--desc',str(desc),'--tile-mm','8','--output',str(plan)])
    meshes=[]
    for k in range(len(json.loads(plan.read_text())['chunks'])):
     m=cls.d/f'{b}-mesh-{net}-{k}.pkl.gz';U.main(['mesh','--desc',str(desc),'--tile-mm','8','--chunk',str(k),'--output',str(m)]);meshes.append(str(m))
    U.main(['assemble','--desc',str(desc),'--tile-mm','8','--mesh',*meshes,'--graph',str(gp),'--census',str(cp),'--operator',str(cls.d/f'{b}-op-{net}.pkl.gz'),'--output',str(cls.d/f'{b}-cov-{net}.json.gz')])
  devices=[{'board':b,'ref':f'U{k}','symbol':'OPA4197IPWR' if k<2 else 'SN74HC14DR',
   'supply_pins':{'4':'+12V','11':'-12V'} if k<2 else {'14':'+5V','7':'AGND'}} for b in ('KA','KB') for k in range(4)]
  led={'records':records,'interface_demands':[],'allowances':[]};h=hashlib.sha256(json.dumps(led,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  led.update(scenarios={'normal-typ-v1':'synthetic complete quiescent loads'},census={'fitted_ics':{'devices':devices}})
  cfg['source_support']={'board':'KA','pads':lands,'excluded':[]};cfg['scenario']={'id':'normal-typ-v1','ledger_sha256':h}
  (cls.d/'config.json').write_text(json.dumps(cfg));(cls.d/'ledger.json').write_text(json.dumps(dict(led,ledger_sha256=h)))
  S.main(['service','--config',str(cls.d/'config.json'),'--ledger',str(cls.d/'ledger.json'),
          '--coverage',*[str(cls.d/f'{b}-cov-{net}.json.gz') for b in ('KA','KB') for net in band],'--output',str(cls.d/'service.json')])
  cls.cfg=cfg;cls.records=records
  for net in band:
   for b in ('KA','KB'):
    S.main(['reduce','--operator',str(cls.d/f'{b}-op-{net}.pkl.gz'),'--coverage',str(cls.d/f'{b}-cov-{net}.json.gz'),'--ledger',str(cls.d/'ledger.json'),'--service',str(cls.d/'service.json'),'--config',str(cls.d/'config.json'),
            '--cases',str(cls.d/'cases.json'),'--case','c','--depth','uniform-dielectric','--board',b,f'--net={net}','--output',str(cls.d/f'{b}-red-{net}.pkl.gz')])
   dps={}
   for b in ('KA','KB'):
    dps[b]=[]
    for k,(lo,hi) in enumerate(((0,1),(1,10**6))):
     f=cls.d/f'{b}-dp-{net}-{k}.pkl.gz';dps[b].append(str(f))
     S.main(['dpoint','--operator',str(cls.d/f'{b}-op-{net}.pkl.gz'),'--coverage',str(cls.d/f'{b}-cov-{net}.json.gz'),'--config',str(cls.d/'config.json'),'--cases',str(cls.d/'cases.json'),
             '--case','c','--depth','uniform-dielectric','--board',b,f'--net={net}','--start',str(lo),'--stop',str(hi),'--output',str(f)])
   original_apply=S.apply_board;seen=[]
   def check_precision(K,sup,Rt,vm,vt):
    seen.append(vm.dtype)
    assert vm.dtype==np.dtype(np.longdouble),'coupled node reconstruction discarded load precision'
    return original_apply(K,sup,Rt,vm,vt)
   with patch.object(S,'apply_board',side_effect=check_precision):
    S.main(['couple','--ka-dp',*dps['KA'],'--kb-dp',*dps['KB'],'--ka-red',str(cls.d/f'KA-red-{net}.pkl.gz'),'--kb-red',str(cls.d/f'KB-red-{net}.pkl.gz'),'--ka-op',str(cls.d/f'KA-op-{net}.pkl.gz'),'--kb-op',str(cls.d/f'KB-op-{net}.pkl.gz'),
            '--config',str(cls.d/'config.json'),'--cases',str(cls.d/'cases.json'),'--case','c','--depth','uniform-dielectric',f'--net={net}','--output',str(cls.d/f'res-{net}.json.gz')])
   assert seen,'coupled KCL path was not exercised'
   for b in ('KA','KB'):
    red=U.pload(cls.d/f'{b}-red-{net}.pkl.gz')
    assert red['g'].dtype==np.dtype(np.float64),'small interface RHS must remain supported by numpy.linalg'
    assert red['S'].dtype==np.dtype(np.float64),'small interface matrix must remain supported by numpy.linalg'
    assert red['Y'].dtype==np.dtype(np.longdouble),'serialized terminal basis discarded reconstruction precision'
 def res(self,net):return json.loads(gzip.decompress((self.d/f'res-{net}.json.gz').read_bytes()))
 def test_coverage_is_complete_and_graph_reproduced(self):
  for b in ('KA','KB'):
   for net in ('+12V','AGND'):
    cov=U.jload(self.d/f'{b}-cov-{net}.json.gz');self.assertEqual(cov['obligated_without_finite_path'],[]);self.assertTrue(cov['terminals_covered'])
 def test_reduction_equals_monolithic_reference(self):
  for net,state,removed in (('AGND','all-present',set()),('AGND','remove-W4-W6',{4,6}),('+12V','all-present',set())):
   MA,fA,tA=S.full_matrix(U.pload(self.d/f'KA-op-{net}.pkl.gz'),CASE,UNIFORM,self.cfg,'KA',net);MB,fB,tB=S.full_matrix(U.pload(self.d/f'KB-op-{net}.pkl.gz'),CASE,UNIFORM,self.cfg,'KB',net)
   nA,nB=MA.shape[0],MB.shape[0];M=sp.lil_matrix(sp.block_diag([MA,MB]))
   NA=nA-len(tA);NB=nB-len(tB);gw=1/self.cfg['wires']['bulk_ohm']
   for k,t in enumerate(tA):
    if S.wire_of(t) in removed:continue
    i,j=NA+k,nA+NB+k;M[i,i]+=gw;M[j,j]+=gw;M[i,j]-=gw;M[j,i]-=gw
   f=np.zeros(nA+nB)
   for r in self.records:
    if r['net']!=net:continue
    op=U.pload(self.d/f'{r["board"]}-op-{net}.pkl.gz');n,w=op['supports'][r['pad_id']];f[n+(0 if r['board']=='KA' else nA)]-=r['current_A']*w
   fixed=np.zeros(nA+nB,bool);fixed[:NA][fA]=True;self.assertTrue(fA.sum()>0);keep=np.flatnonzero(~fixed);v=np.zeros(nA+nB)
   v[keep]=spla.spsolve(M.tocsr()[keep][:,keep].tocsc(),f[keep])
   got=self.res(net)['states'][state]['boards']
   for b,off in (('KA',0),('KB',nA)):
    op=U.pload(self.d/f'{b}-op-{net}.pkl.gz')
    for pid,V in got[b]['pad_potential_V'].items():
     n,w=op['supports'][pid];ref=float(w@v[off+n]);self.assertAlmostEqual(V,ref,delta=1e-8*max(abs(ref),1e-12)+1e-15)
 def test_kcl_energy_and_reciprocity(self):
  for net in ('+12V','-12V','+5V','AGND'):
   r=self.res(net)
   for name,st in r['states'].items():
    self.assertLess(st['checks']['global_kcl_relative'],1e-9);self.assertLess(st['checks']['energy_minus_load_work_relative'],1e-9);self.assertTrue(st['checks']['nonnegative_energy'])
    self.assertLess(st['checks']['wire_terminal_balance_A'],1e-12)
   for b in ('KA','KB'):self.assertLess(r['reduction_checks'][b]['reciprocity_relative'],1e-9)
 def test_return_removal_states_and_open_classification(self):
  r=self.res('AGND');self.assertEqual(len(r['states']),7);self.assertIn('all-three-open',r['not_solved'])
  st=r['states']['remove-W4-W5'];self.assertAlmostEqual(st['wire_current_A']['W4'],0.);self.assertAlmostEqual(st['wire_current_A']['W5'],0.)
  base=sum(r['states']['all-present']['wire_current_A'].values());self.assertAlmostEqual(st['wire_current_A']['W6'],base,delta=1e-12)
 def test_tampered_ledger_is_refused(self):
  bad=json.loads((self.d/'ledger.json').read_text());bad['records'][0]['current_A']*=2;(self.d/'ledger-bad.json').write_text(json.dumps(bad))
  with self.assertRaises(ValueError):
   S.main(['reduce','--operator',str(self.d/'KA-op-+12V.pkl.gz'),'--coverage',str(self.d/'KA-cov-+12V.json.gz'),'--ledger',str(self.d/'ledger-bad.json'),'--service',str(self.d/'service.json'),'--config',str(self.d/'config.json'),
           '--cases',str(self.d/'cases.json'),'--case','c','--depth','uniform-dielectric','--board','KA','--net=+12V','--output',str(self.d/'never.pkl.gz')])
 def service_paths(self):
  return [self.d/f'{b}-cov-{net}.json.gz' for b in ('KA','KB') for net in ('+12V','-12V','+5V','AGND')]
 def validate(self,path=None,coverage=None,net='+12V'):
  return S.validate_service(path or self.d/'service.json',self.d/'config.json',self.d/'ledger.json',coverage or self.d/f'KA-cov-{net}.json.gz','KA',net,U.pload(self.d/f'KA-op-{net}.pkl.gz'))
 def test_complete_device_service_is_content_bound_and_balanced(self):
  manifest=self.validate();service=manifest['device_service']
  self.assertEqual(service['summary'],{'supported':8,'partial':0,'unserved':0,'unmapped':0})
  self.assertEqual(len(service['eligible_pad_ids']),16);self.assertEqual(service['included_global_residual_A'],0)
  self.assertEqual(len(manifest['bindings']['coverage']),8)
  for b in ('KA','KB'):
   currents=[I for net in ('+12V','-12V','+5V','AGND') for I,_ in S.injected(self.cfg,U.jload(self.d/'ledger.json'),b,net,manifest)[0].values()]
   self.assertAlmostEqual(math.fsum(currents),0,places=15)
 def test_missing_return_coverage_excludes_both_supply_rows_in_real_reduce(self):
  paths=self.service_paths();original=self.d/'KA-cov--12V.json.gz';cov=U.jload(original)
  row=next(r for r in cov['rows'] if r['pad_id']=='KA-L-12V-0');row.update(obligated=False,structurally_unresolved=True,finite_path_to_feed=False,support_nodes=0)
  changed=self.d/'KA-cov-partial.json.gz';U.jsave(changed,cov);paths[paths.index(original)]=changed
  manifest=S.service_manifest(self.d/'config.json',self.d/'ledger.json',paths);service=manifest['device_service']
  self.assertEqual(service['summary']['partial'],1);self.assertEqual(service['included_global_residual_A'],0)
  self.assertNotIn('KA-L+12V-0',service['eligible_pad_ids']);self.assertNotIn('KA-L-12V-0',service['eligible_pad_ids'])
  service_path=self.d/'service-partial.json';service_path.write_text(json.dumps(manifest));led=U.jload(self.d/'ledger.json')
  self.assertNotIn('KA-L+12V-0',S.injected(self.cfg,led,'KA','+12V',manifest)[0])
  self.assertNotIn('KA-L-12V-0',S.injected(self.cfg,led,'KA','-12V',manifest)[0])
  for net,coverage in (('+12V',self.d/'KA-cov-+12V.json.gz'),('-12V',changed)):
   output=self.d/f'partial-red-{net}.pkl.gz'
   S.main(['reduce','--operator',str(self.d/f'KA-op-{net}.pkl.gz'),'--coverage',str(coverage),'--ledger',str(self.d/'ledger.json'),'--service',str(service_path),
    '--config',str(self.d/'config.json'),'--cases',str(self.d/'cases.json'),'--case','c','--depth','uniform-dielectric','--board','KA',f'--net={net}','--output',str(output)])
   self.assertEqual(len(U.pload(output)['loads']),1)
 def test_omitted_duplicate_or_incomplete_coverage_is_refused(self):
  paths=self.service_paths()
  with self.assertRaisesRegex(ValueError,'all eight'):S.service_manifest(self.d/'config.json',self.d/'ledger.json',paths[:-1])
  with self.assertRaisesRegex(ValueError,'duplicate'):S.service_manifest(self.d/'config.json',self.d/'ledger.json',paths[:-1]+[paths[0]])
  for field,value in (('terminals_covered',False),('floating_finite_components',[0]),('obligated_without_finite_path',['missing'])):
   with self.subTest(field=field):
    cov=U.jload(paths[0]);cov[field]=value;bad=self.d/'coverage-incomplete.json.gz';U.jsave(bad,cov)
    with self.assertRaisesRegex(ValueError,'incomplete'):S.service_manifest(self.d/'config.json',self.d/'ledger.json',[bad,*paths[1:]])
 def test_tampered_coverage_service_and_method_binding_are_refused(self):
  for field in ('eligible','method','census'):
   with self.subTest(field=field):
    manifest=U.jload(self.d/'service.json')
    if field=='eligible':manifest['device_service']['eligible_pad_ids'].pop()
    elif field=='method':manifest['bindings']['methods']['load_ledger.py']='0'*64
    else:manifest['device_service']['summary']['supported']+=1
    # Even recomputing the superficial content hash cannot bypass recomputed eligibility.
    import load_ledger as LL
    manifest.pop('service_sha256');manifest['service_sha256']=hashlib.sha256(LL.canon(manifest).encode()).hexdigest()
    bad=self.d/'service-bad.json';bad.write_text(json.dumps(manifest))
    with self.assertRaisesRegex(ValueError,'service manifest differs'):self.validate(bad)
  cov=U.jload(self.d/'KA-cov-+12V.json.gz');cov['desc_sha256']='0'*64;bad=self.d/'local-cov-bad.json.gz';U.jsave(bad,cov)
  with self.assertRaisesRegex(ValueError,'local coverage differs'):self.validate(coverage=bad)
  op=U.pload(self.d/'KA-op-+12V.pkl.gz');op['desc_sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'operator differs'):S.validate_service(self.d/'service.json',self.d/'config.json',self.d/'ledger.json',self.d/'KA-cov-+12V.json.gz','KA','+12V',op)
 def test_changed_bound_coverage_is_rejected_even_for_another_net(self):
  path=self.d/'KB-cov-AGND.json.gz';original=path.read_bytes()
  try:
   cov=U.jload(path);cov['mesh_sha256']['invented']='0'*64;U.jsave(path,cov)
   with self.assertRaisesRegex(ValueError,'service manifest differs'):self.validate()
  finally:path.write_bytes(original)
 def test_omitted_service_refuses_individual_pad_fallback(self):
  with self.assertRaisesRegex(ValueError,'explicit scenario device service'):S.injected(self.cfg,U.jload(self.d/'ledger.json'),'KA','+12V',None)

 def test_tampered_driving_point_input_bindings_are_refused(self):
  for field in ('config','cases','method'):
   with self.subTest(field=field):
    data=U.pload(self.d/'KA-dp-+12V-0.pkl.gz');data['bindings'][field]='0'*64
    bad=self.d/'KA-dp-bad.pkl.gz';U.psave(bad,data)
    with self.assertRaisesRegex(ValueError,'driving-point chunk configuration'):
     S.main(['couple','--ka-dp',str(bad),str(self.d/'KA-dp-+12V-1.pkl.gz'),
      '--kb-dp',str(self.d/'KB-dp-+12V-0.pkl.gz'),str(self.d/'KB-dp-+12V-1.pkl.gz'),
      '--ka-red',str(self.d/'KA-red-+12V.pkl.gz'),'--kb-red',str(self.d/'KB-red-+12V.pkl.gz'),
      '--ka-op',str(self.d/'KA-op-+12V.pkl.gz'),'--kb-op',str(self.d/'KB-op-+12V.pkl.gz'),
      '--config',str(self.d/'config.json'),'--cases',str(self.d/'cases.json'),'--case','c','--depth','uniform-dielectric','--net=+12V','--output',str(self.d/'never-stale.json.gz')])
 def test_wire_bulk_charged_once_and_copper_share(self):
  r=self.res('+12V')['states']['all-present'];dp=r['driving_point']['KB'];Rw=self.cfg['wires']['bulk_ohm'];Rt=self.cfg['wires']['termination_per_end_ohm']
  for rdp,rcu in zip(dp['R_driving_point_ohm'],dp['R_copper_ohm']):self.assertAlmostEqual(rdp-rcu,Rw+2*Rt,delta=1e-12)

if __name__=='__main__':unittest.main()
