"""Bounded serialized fixtures, never retained numerical artifacts."""
import copy
import gzip
import hashlib
import json
import pickle
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import scipy.sparse as sp
import shapely
from shapely.geometry import box, Point

import attribution_executor as E
import attribution_transport as T
import attribution_uniqueness as U
import finite_adapter as A
import finite_solve as S
import finite_units as F
import resistance_attribution as R
from test_attribution_reconstruction import reductions_from
from test_finite_adapter import CASE, UNIFORM


def bind(root,name,value,fmt='pickle'):
    path = root/name
    raw = pickle.dumps(value,protocol=5) if fmt == 'pickle' else json.dumps(value).encode()
    data = gzip.compress(raw,mtime=0)
    path.write_bytes(data)
    return {'path':str(path),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),
            'decoded_sha256':hashlib.sha256(raw).hexdigest(),'decoded_limit':4*1024**2,
            'format':fmt,'gzip':True}


def packet(root, barrels=False, multiwire=False):
    cfg = json.loads(R.CONFIG.read_text())
    cfg['source_support'] = {'board':'KA','mode':'equipotential_patches',
                            'pads':{'+12V':[{'ref':ref,'pad_id':pid} for ref,pid in E.HELD]}}
    cfg['wires']['pairs'] = {'W1':'+12V'}
    if multiwire: cfg['wires']['pairs']['W2'] = '+12V'
    cfg['wires']['termination_per_end_ohm'] = .002
    cfg['wires']['bulk_ohm'] = .003
    cfg['depth_cases'][E.DEPTH] = UNIFORM
    result = {'config':bind(root,'config.gz',cfg,'json'),
              'cases':bind(root,'cases.gz',{'cases':{E.CASE:CASE}},'json'),
              'solver_sha256':hashlib.sha256(Path(S.__file__).read_bytes()).hexdigest(),
              'source_bindings':{'fixture':'bounded serialized original-Assembly test'},
              'certificate_method':U.REFERENCE_METHOD,
              'certificate_limits':{'max_entries':10000,'max_updates':500000},'boards':{}}
    ops = {}
    for board in ('KA','KB'):
        term = f'CS247-{board}-W1'
        supports = {term:box(3.2,0,4,1)}
        if board == 'KA':
            for j,(_,pid) in enumerate(E.HELD):
                supports[pid] = box(j,0,j+.6,1)
        else:
            supports[E.PAD] = box(0,0,.8,1)
        desc = {'board':board,'net':'+12V','groups':[{'group':0,'layer':'F.Cu','fragments':['overlap-pad','overlap-track'],
                'wkb':shapely.to_wkb(box(0,0,4,1),hex=True)}], 'barrels':{},'terminals':[term],
                'supports':{pid:[{'fragment':pid,'group':0,'wkb':shapely.to_wkb(p,hex=True),
                                 'copper_area_mm2':p.area}] for pid,p in supports.items()}}
        if barrels:
            copper = box(0,0,4,1).difference(Point(3.0,.5).buffer(.15,quad_segs=4)).difference(Point(3.75,.5).buffer(.15,quad_segs=4))
            desc['groups'] = [{'group':g,'layer':layer,'fragments':[f'plane{g}',f'overlap{g}'],
                              'wkb':shapely.to_wkb(copper,hex=True)} for g,layer in enumerate(('F.Cu','In4.Cu','B.Cu'))]
            bid = E.BARREL if board == 'KA' else 'fixture-KB-barrel'
            desc['barrels'] = {bid:{'center_mm':[3.,.5],'drill_mm':.3,
                'taps':[{'group':g,'layer':layer} for g,layer in enumerate(('F.Cu','In4.Cu','B.Cu'))]}}
            desc['barrels'][board+'-second'] = {'center_mm':[3.75,.5],'drill_mm':.3,
                'taps':[{'group':g,'layer':layer} for g,layer in enumerate(('F.Cu','In4.Cu','B.Cu'))]}
            for pid,poly in supports.items():
                desc['supports'][pid][0]['copper_area_mm2'] = poly.intersection(copper).area
            desc['supports'][term][0]['group'] = 2
        if multiwire:
            term2 = f'CS247-{board}-W2'
            desc['terminals'].append(term2)
            poly=box(2.5,0,3,1)
            desc['supports'][term2] = [{'fragment':term2,'group':0,'wkb':shapely.to_wkb(poly,hex=True),'copper_area_mm2':poly.area}]
        source = {'desc':bind(root,board+'-desc.gz',desc,'json')}
        settings = {'pitch':.5,'face_pitch':.5,'tile_mm':24.,'origin':[0.,0.]}
        expected,chunks,_ = F.plan(desc,**settings)
        items = [A.mesh_item(desc,g,t,settings['pitch'],settings['face_pitch'],settings['origin']) for g,t in expected]
        asm = A.Assembly(desc,items)
        op = {'N':asm.N,'Kg_face':asm.Kg['face'],'Kg_inner':asm.Kg['inner'],'rings':asm.rings,
              'barrels':desc['barrels'],'supports':asm.supports,'support_inside':asm.support_inside,
              'terminals':desc['terminals'],'desc_sha256':source['desc']['sha256'],'receipts':asm.receipts,
              **{k:settings[k] for k in ('origin','pitch','face_pitch')}}
        ops[board] = op
        source['operator'] = bind(root,board+'-operator.gz',op)
        source['plan'] = bind(root,board+'-plan.gz',settings|{'desc_sha256':source['desc']['sha256'],
                        'items':len(items),'chunks':chunks},'json')
        source['mesh'] = [bind(root,board+'-chunk.gz',settings|{'desc_sha256':source['desc']['sha256'],
                           'chunk':0,'items':items})]
        result['boards'][board] = source
    reductions = reductions_from(ops,cfg)
    for board in ('KA','KB'):
        source = result['boards'][board]
        reductions[board]['bindings'] = {'operator':source['operator']['sha256'],'config':result['config']['sha256'],
                                       'cases':result['cases']['sha256'],'method':result['solver_sha256']}
        source['reduction'] = bind(root,board+'-reduction.gz',reductions[board])
    return result,ops,cfg,reductions


class Certificates(unittest.TestCase):
    def check(self,a,**kw):
        return U.certify(sp.csr_matrix(a,dtype=float),{'held':[0]},{'held':[0]},**kw)

    def test_spd_positive_offdiagonal(self):
        self.assertEqual(self.check([[2,1],[1,2]])['status'],'EXACT_STORED_OPERATOR_SPD')

    def test_floating_singular_indefinite_unresolved(self):
        for a in ([[1,-1],[-1,1]],[[1,2],[2,1]],[[0,0],[0,1]],[[1,1],[1,np.nextafter(1.,2.)]]):
            with self.subTest(a=a),self.assertRaisesRegex(ValueError,'UNRESOLVED'):
                self.check(a)

    def test_nonfinite_asymmetric_stale(self):
        for a in ([[np.nan,0],[0,1]],[[1,np.inf],[np.inf,1]],[[2,1],[0,2]]):
            with self.assertRaises(ValueError):self.check(a)
        with self.assertRaisesRegex(ValueError,'stale'):
            U.certify(sp.eye(2,format='csr'),{'held':[1]},{'held':[0]})

    def test_exact_reciprocity_witness_is_bounded_and_does_not_change_operator(self):
        a=sp.csr_matrix([[2.,1.],[np.nextafter(1.,2.),2.]])
        before=U.matrix_hash(a)
        with self.assertRaisesRegex(ValueError,'nonreciprocal exact certificate operator: ') as caught:
            U.certify(a,{'held':[0]},{'held':[0]})
        reason=str(caught.exception);self.assertLess(len(reason.encode()),2048)
        report=json.loads(reason.split(': ',1)[1])
        self.assertEqual(report['matrix_sha256'],before);self.assertEqual(U.matrix_hash(a),before)
        self.assertEqual(report['mismatched_entries'],2);self.assertFalse(report['symmetrized'])
        self.assertEqual(report['global_skew_norm'],'NOT_COMPUTED')
        for w in report['witnesses']:
            self.assertEqual(float.fromhex(w['a_ij_hex']),a[w['row'],w['column']])
            self.assertEqual(float.fromhex(w['a_ji_hex']),a[w['column'],w['row']])
        many=sp.diags([np.ones(9),np.ones(10)*4],[1,0],shape=(10,10),format='csr')
        with self.assertRaises(ValueError) as caught:U.certify(many,{'held':[0]},{'held':[0]})
        report=json.loads(str(caught.exception).split(': ',1)[1])
        self.assertEqual(report['mismatched_entries'],18);self.assertEqual(len(report['witnesses']),4)

    def test_sparse_caps(self):
        for work in (U.Work(max_entries=1),U.Work(max_updates=0)):
            with self.assertRaisesRegex(ValueError,'cap'):self.check([[2,1],[1,2]],work=work)

    def test_border_and_coupled_exact(self):
        work=U.Work()
        ka=self.check([[2]],border=(np.array([[-1.]]),np.array([[1.]])),work=work)
        kb=self.check([[1]],border=(np.array([[-1.]]),np.array([[1.]])),work=work)
        self.assertEqual(U.certify_coupled(ka['schur_intervals'],kb['schur_intervals'],1,[True],work)['status'],'EXACT_COUPLED_SCHUR_SPD')
        with self.assertRaisesRegex(ValueError,'UNRESOLVED'):
            U.certify_coupled(ka['schur_intervals'],kb['schur_intervals'],1,[False],work)

    def test_random_integer_gram_spd(self):
        rng=np.random.default_rng(12)
        for _ in range(20):
            m=rng.integers(-3,4,(6,6));a=m.T@m+np.eye(6)*2
            self.check(a)


class SerializedPipeline(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.packet,self.ops,self.cfg,self.red=packet(self.root)
    def tearDown(self):self.temp.cleanup()
    def run_pipeline(self,**kw):
        return E.run_pipeline(self.packet,self.root/'output',T.Budget(**kw))

    def test_complete_selected_path_matches_independent_monolithic(self):
        r=self.run_pipeline();self.assertEqual(r['status'],'COMPLETE')
        from attribution_reconstruction import reconstruct_fixture
        obs={'board':'KB','pad_uuid':E.PAD,'ref':'U7105','pin':'4','net':E.NET,'process_case':E.CASE,'depth_case':E.DEPTH}
        direct=reconstruct_fixture(self.ops,self.red,self.cfg,CASE,UNIFORM,obs)
        matrix=direct['matrix'];fixed,_=S.held_nodes(self.ops['KA'],self.cfg,'KA',E.NET)
        held=np.r_[fixed,np.zeros(matrix.shape[0]-len(fixed),dtype=bool)]
        free=np.flatnonzero(~held);f=direct['injection']
        v=np.linalg.solve(matrix[free][:,free].toarray(),np.asarray(f[free],dtype=float))
        self.assertAlmostEqual(r['summary']['total_ohm'],float(f[free]@v),places=12)
        rows=[json.loads(x) for x in (self.root/'output/components.jsonl').read_text().splitlines()]
        self.assertEqual(len(rows),5)
        self.assertEqual(sum(x['kind']=='wire_bulk' for x in rows),1)
        self.assertEqual(len(r['summary']['boards']['KA']['source_reactions_A']),3)
        self.assertLess(r['summary']['normalization_max_global_nodal_injection_A'],1)
        self.assertFalse(r['adopted'])
        self.assertEqual(hashlib.sha256((self.root/'output/components.jsonl').read_bytes()).hexdigest(),r['components_sha256'])

    def test_barrel_intervals_and_zero_energy_retained(self):
        self.packet,self.ops,self.cfg,self.red=packet(self.root,barrels=True)
        result=self.run_pipeline()
        rows=[json.loads(x) for x in (self.root/'output/components.jsonl').read_text().splitlines()]
        barrels=[x for x in rows if x['kind']=='barrel']
        self.assertEqual(len(barrels),8)
        self.assertEqual(result['summary']['boards']['KA']['barrel_intervals'],[['F.Cu','In4.Cu'],['In4.Cu','B.Cu']])
        self.assertEqual(sum(x['kind']=='sheet_union' for x in rows),6)

    def test_removed_wire_pipeline_preserves_both_terminations(self):
        self.packet,self.ops,self.cfg,self.red=packet(self.root,multiwire=True)
        self.packet.update(fixture_only=True,fixture_removed=[1])
        r=self.run_pipeline()
        rows=[json.loads(x) for x in (self.root/'output/components.jsonl').read_text().splitlines()]
        self.assertEqual(len([x for x in rows if x['kind']=='termination']),4)
        self.assertEqual([x['object_ids'] for x in rows if x['kind']=='wire_bulk'],[['W2']])
        self.assertEqual(r['summary']['identity']['return_state'],'remove-W1')

    def test_selected_retained_comparison_and_stale_refusal(self):
        self.packet,self.ops,self.cfg,self.red=packet(self.root,barrels=True)
        r=self.run_pipeline()['summary']
        bindings={'config':self.packet['config']['sha256'],'method':self.packet['solver_sha256']}
        for board in ('KA','KB'):
            for key in ('operator','reduction'):
                bindings[board.lower()+'_'+key]=self.packet['boards'][board][key]['sha256']
        retained={'net':E.NET,'case':E.CASE,'depth':E.DEPTH,'bindings':bindings,
                  'states':{'all-present':{'driving_point':{'KB':{'pads':[E.PAD],
                             'R_driving_point_ohm':[r['total_ohm']], 'R_copper_ohm':[r['copper_ohm']]}}}}}
        self.packet['comparison']=bind(self.root,'comparison.gz',retained,'json')
        compare=lambda:E.compare_retained(self.packet,r['boards'],r['total_ohm'],r['copper_ohm'],T.Budget())
        outcome=compare()
        self.assertEqual(outcome['retained_comparison']['status'],'PASS')
        self.assertIn(outcome['stage_C'],('REJECTED','INCONCLUSIVE','SUPPORTED'))
        for mutation in ('binding','pad','value'):
            bad=copy.deepcopy(retained)
            projection=bad['states']['all-present']['driving_point']['KB']
            if mutation=='binding':bad['bindings']['config']='0'*64
            if mutation=='pad':projection['pads']=['wrong-observation']
            if mutation=='value':projection['R_copper_ohm'][0]*=1.01
            self.packet['comparison']=bind(self.root,'bad-comparison.gz',bad,'json')
            with self.assertRaises(ValueError):compare()

    def test_stale_input_fails_before_interpretation(self):
        Path(self.packet['boards']['KA']['operator']['path']).write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError,'size changed'):self.run_pipeline()
        self.assertEqual(json.loads((self.root/'output/terminal.json').read_text())['status'],'INCOMPLETE')

    def test_missing_chunk(self):
        self.packet['boards']['KA']['mesh']=[]
        with self.assertRaisesRegex(ValueError,'chunk plan'):self.run_pipeline()

    def test_reordered_chunk(self):
        source=self.packet['boards']['KA'];chunk=T.decode(source['mesh'][0],T.Budget());chunk['chunk']=1
        source['mesh'][0]=bind(self.root,'reordered.gz',chunk)
        with self.assertRaisesRegex(ValueError,'reordered mesh chunk'):self.run_pipeline()

    def test_oversized_decode(self):
        self.packet['boards']['KA']['operator']['decoded_limit']=8
        with self.assertRaisesRegex(ValueError,'decoded payload'):self.run_pipeline()

    def test_quota_exhaustion_retains_negative_receipt(self):
        with self.assertRaisesRegex(ValueError,'quota'):self.run_pipeline(output_bytes=T.RECEIPT_RESERVE+100)
        self.assertFalse((self.root/'output/components.jsonl').exists())
        self.assertEqual(json.loads((self.root/'output/terminal.json').read_text())['status'],'INCOMPLETE')

    def test_timeout_and_cancel(self):
        budget=T.Budget();budget.cancelled=True
        with self.assertRaisesRegex(ValueError,'CANCELLED'):
            E.run_pipeline(self.packet,self.root/'cancel',budget)
        now=[0.];budget=T.Budget(seconds=1,clock=lambda:now[0]);now[0]=2
        with self.assertRaisesRegex(ValueError,'TIMEOUT'):
            E.run_pipeline(self.packet,self.root/'timeout',budget)

    def test_incorrect_held(self):
        source=self.packet['boards']['KA'];red=T.decode(source['reduction'],T.Budget());red['source_pads'].reverse()
        source['reduction']=bind(self.root,'badheld.gz',red)
        with self.assertRaisesRegex(ValueError,'held/source'):self.run_pipeline()

    def test_bad_basis(self):
        source=self.packet['boards']['KA'];red=T.decode(source['reduction'],T.Budget());red['Y']*=1.01
        source['reduction']=bind(self.root,'badbasis.gz',red)
        with self.assertRaisesRegex(ValueError,'basis residual'):self.run_pipeline()

    def test_missing_final_item_does_not_publish(self):
        real=E.C.copper_stream
        def incomplete(*args):
            yield from real(*args)
            raise ValueError('incomplete last iterator')
        with patch.object(E.C,'copper_stream',incomplete),self.assertRaisesRegex(ValueError,'incomplete'):
            self.run_pipeline()
        self.assertFalse((self.root/'output/components.jsonl').exists())

    def test_duplicate_output_cannot_resume(self):
        self.run_pipeline()
        with self.assertRaises(FileExistsError):self.run_pipeline()

    def test_trailing_pickle(self):
        b=bind(self.root,'trailing.gz',{})
        raw=pickle.dumps({})+b'junk';data=gzip.compress(raw);Path(b['path']).write_bytes(data)
        b.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        with self.assertRaisesRegex(ValueError,'trailing'):T.decode(b,T.Budget())


if __name__=='__main__':unittest.main()
