"""Run only as this file; enforces synthetic worker resource limits before SciPy."""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
import resource
resource.setrlimit(resource.RLIMIT_AS, (512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_CPU, (20,20))
import copy
from fractions import Fraction as F
import json
import math
import unittest
import numpy as np
from scipy.sparse import csr_matrix
import prototype as P

CONTEXT = {'fixture_only': True, 'experiment': 'KB U7105.4 +12V nominal-average uniform-dielectric all-present 1A',
           'held_sources': ['TP990002','TP990014','TP990026'], 'termination': 'distributed rank-one',
           'assembly': 'synthetic stored coefficients; not production metadata'}
RESULTS = {}


def csr(a):
    a = csr_matrix(a, dtype=np.float64)
    a.eliminate_zeros(); a.sort_indices()
    return a


def exact_inverse(a):
    # Dense Fraction operations are an INDEPENDENT TINY FIXTURE ORACLE only.
    return exact_inverse_values([[F(float(a[i,j])) for j in range(a.shape[0])] for i in range(a.shape[0])])

def exact_inverse_values(a):
    n=len(a)
    assert n <= 16
    rows = [list(a[i]) + [F(int(i==j)) for j in range(n)] for i in range(n)]
    for k in range(n):
        pivot = next((i for i in range(k,n) if rows[i][k]), None)
        if pivot is None: raise ValueError('singular exact fixture')
        rows[k], rows[pivot] = rows[pivot], rows[k]
        d = rows[k][k]; rows[k] = [v/d for v in rows[k]]
        for i in range(n):
            if i != k:
                d = rows[i][k]; rows[i] = [x-d*y for x,y in zip(rows[i], rows[k])]
    return [r[n:] for r in rows]


def exact_norm(a):
    return max(sum(map(abs,r)) for r in exact_inverse(a))


def run(a, name, full=True):
    meter = P.Meter()
    w, h = P.produce(a, CONTEXT, P.pattern_of(a,full), meter)
    cert = P.verify(a, CONTEXT, w, h, meter)
    RESULTS[name] = {k:v for k,v in cert.items() if k != 'residual_row_upper'}
    if cert['status'] == 'CERTIFIED' and a.shape[0] <= 16:
        assert F(cert['inverse_infinity_upper']) >= exact_norm(a)
    assert cert['updates'] == sum(cert['phase_updates'].values())
    return cert, w


def joined(ground=1.):
    # Fixture only: two 2-node copper blocks and two interfaces.
    # KA grounded, KB floating before termination/wire coupling.
    a = np.zeros((6,6))
    def edge(i,j,g):
        a[i,i] += g; a[j,j] += g; a[i,j] -= g; a[j,i] -= g
    edge(0,1,2.); edge(2,3,3.); a[0,0] += ground
    for ns,w,t in [([0,1],[.25,.75],4),([2,3],[1/3,2/3],5)]:
        rt = .7
        # Mirror independently rounded production coefficients, NOT algebraically
        # exact rank-one real coefficients when weights/Rt are non-dyadic.
        for i,wi in zip(ns,w):
            for j,wj in zip(ns,w): a[i,j] += float(wi*wj/rt)
            a[i,t] -= float(wi/rt); a[t,i] -= float(wi/rt)
        a[t,t] += float(1/rt)
    edge(4,5,4.)
    return csr(a)


def grid(side, ground=1.):
    n = side*side; a = np.zeros((n,n))
    for i in range(n):
        for j in [i+1 if i%side < side-1 else -1, i+side if i+side<n else -1]:
            if j >= 0:
                a[i,i] += 1.; a[j,j] += 1.; a[i,j] -= 1.; a[j,i] -= 1.
    a[0,0] += ground
    return csr(a)


def separated_fixture(ground=1., nonsymmetric=False, wire=4.):
    a=joined(ground)
    blocks=[]
    for start in [0,2]:
        A=a[start:start+2,start:start+2].copy()
        if nonsymmetric and start==0:
            A[0,1]=float(A[0,1])+.2
        B=a[start:start+2,4:6].toarray()
        blocks.append((A,B))
    raw=float(1/.7)
    d=[[P.I.add((raw,raw),(wire,wire)),(-wire,-wire)],
       [(-wire,-wire),P.I.add((raw,raw),(wire,wire))]]
    exact=[[F(0) for _ in range(6)] for _ in range(6)]
    for start,(A,B) in zip([0,2],blocks):
        for i in range(2):
            for j in range(2): exact[start+i][start+j]=F(float(A[i,j]))
            for j in range(2): exact[start+i][4+j]=exact[4+j][start+i]=F(float(B[i,j]))
    for i in range(2):
        for j in range(2):exact[4+i][4+j]=(F(raw)+F(wire)) if i==j else -F(wire)
    return blocks,d,exact


class Tests(unittest.TestCase):
    def test_signed_factor_solve_negative_pivot(self):
        a=csr([[-2.,1.],[1.,2.]])
        meter=P.Meter();w,h=P.produce(a,CONTEXT,P.pattern_of(a,True),meter)
        c=P.verify(a,CONTEXT,w,h,meter)
        self.assertEqual(c['status'],'CERTIFIED')
        rhs=[.3,-.5];enclosed=P.signed_factor_solve(w,rhs,meter)
        exact=[sum(v*F(b) for v,b in zip(row,rhs)) for row in exact_inverse(a)]
        for value,(lo,hi) in zip(exact,enclosed):
            self.assertLessEqual(F(lo),value);self.assertGreaterEqual(F(hi),value)

    def test_factor_only_block_schur(self):
        for name,ground,nonsym in [('strong',1.,False),('weak',2**-30,False),('nonsymmetric',1.,True)]:
            blocks,d,exact=separated_fixture(ground,nonsym)
            meter=P.Meter();c=P.block_certificate(blocks,d,CONTEXT,meter)
            inv=exact_inverse_values(exact);norm=max(sum(map(abs,r)) for r in inv)
            self.assertGreaterEqual(F(c['inverse_infinity_upper']),norm)
            # Exact Schur of original nonsymmetric stored free blocks, with exact
            # original D+wire sum; check every entry against factor-only intervals.
            exact_s=[[exact[4+i][4+j] for j in range(2)] for i in range(2)]
            for A,B in blocks:
                ai=exact_inverse(A)
                for i in range(2):
                    for j in range(2):
                        exact_s[i][j]-=sum(F(float(B[k,i]))*ai[k][l]*F(float(B[l,j])) for k in range(2) for l in range(2))
            for i in range(2):
                for j in range(2):
                    lo,hi=c['schur_intervals'][i][j]
                    self.assertLessEqual(F(lo),exact_s[i][j]);self.assertGreaterEqual(F(hi),exact_s[i][j])
            self.assertEqual(c['updates'],sum(c['phase_updates'].values()))
            RESULTS['block_schur_'+name]=c
            if name=='weak':
                error=P.I.upper_mul(c['inverse_infinity_upper'],1e-8)
                self.assertGreater(error,1.)
                self.assertEqual(P.V.screen((-error,error),(-error,error),(-error,error))['status'],'INCONCLUSIVE')

    def test_block_input_types_and_global_binding(self):
        blocks,d,_=separated_fixture()
        original=P.block_certificate(blocks,d,CONTEXT,P.Meter())
        for dtype in [np.longdouble,np.int64,np.bool_]:
            changed=[(A,B.astype(dtype)) for A,B in blocks]
            with self.assertRaisesRegex(ValueError,'B must be finite binary64'):
                P.block_certificate(changed,d,CONTEXT,P.Meter())
        for bad in [1,True,np.longdouble(1.),(1.,float('inf')),(2.,1.)]:
            changed=copy.deepcopy(d);changed[0][0]=bad
            with self.assertRaises(ValueError):P.block_certificate(blocks,changed,CONTEXT,P.Meter())
        changed=copy.deepcopy(blocks);changed[0][1][0,0]+=1e-8
        result=P.block_certificate(changed,d,CONTEXT,P.Meter())
        self.assertNotEqual(result['global_input_sha256'],original['global_input_sha256'])
        changed=copy.deepcopy(d);changed[0][0]=P.I.add(changed[0][0],(1e-8,1e-8))
        result=P.block_certificate(blocks,changed,CONTEXT,P.Meter())
        self.assertNotEqual(result['global_input_sha256'],original['global_input_sha256'])
        result=P.block_certificate(blocks,d,{**CONTEXT,'wire-binding':'different'},P.Meter())
        self.assertNotEqual(result['global_input_sha256'],original['global_input_sha256'])
        meter=P.Meter();w,h=P.produce(blocks[0][0],CONTEXT,[[0,1],[0,1]],meter)
        with self.assertRaisesRegex(ValueError,'signed RHS'):
            P.signed_factor_solve(w,np.array([1.,1.],dtype=np.longdouble),meter)

    def test_board_success_schur_failure(self):
        blocks,d,_=separated_fixture()
        patterns=[[[0],[1]],[[0],[1]]]
        for index,(a,B) in enumerate(blocks):
            meter=P.Meter();w,h=P.produce(a,CONTEXT,patterns[index],meter)
            c=P.verify(a,CONTEXT,w,h,meter)
            self.assertEqual(c['status'],'CERTIFIED')
            RESULTS['diagonal_board_'+str(index)]=c
        with self.assertRaisesRegex(ValueError,'small interval Schur residual refuses') as refusal:
            P.block_certificate(blocks,d,CONTEXT,P.Meter(),patterns)
        RESULTS['diagonal_factor_schur_refusal']=str(refusal.exception)

    def test_disconnected_block_schur_and_shared_terminal_refuse(self):
        blocks,d,_=separated_fixture(wire=0.)
        with self.assertRaises((ValueError,AssertionError)):
            P.block_certificate(blocks,d,CONTEXT,P.Meter())
        blocks,d,_=separated_fixture()
        blocks[1][1][0,0]=1.
        with self.assertRaisesRegex(ValueError,'shared terminal'):
            P.block_certificate(blocks,d,CONTEXT,P.Meter())

    def test_grounded_and_floating_join(self):
        c,_ = run(joined(), 'joined_nondyadic_stored')
        self.assertEqual(c['status'],'CERTIFIED')
        # KB copper alone is singular; joining to grounded KA fixes it.
        with self.assertRaises(ValueError): exact_inverse(csr([[3,-3],[-3,3]]))

    def test_nonsymmetric_cancellation(self):
        c,_ = run(csr([[1.,-1.],[1.,0.]]),'nonsymmetric_cancellation')
        self.assertEqual(c['status'],'CERTIFIED')
        self.assertGreaterEqual(c['K'],3.)
        self.assertEqual(exact_norm(csr([[1.,-1.],[1.,0.]])),2)

    def test_signed_sweep_is_invalid(self):
        a = csr([[1,0,0],[1,1,0],[1,1,1]])
        c,_ = run(a,'signed_sweep_adversary')
        self.assertEqual(exact_norm(a),2)
        self.assertGreaterEqual(c['K'],4.)
        # Signed inverse-times-ones would return [1,0,0], falsely bounding norm by 1.
        self.assertEqual([sum(r) for r in exact_inverse(a)], [1,0,0])

    def test_weak_grounding_and_nearly_singular(self):
        c,_ = run(csr([[1.+2**-30,-1.],[-1.,1.]]),'weak_grounding')
        self.assertEqual(c['status'],'CERTIFIED')
        c,_ = run(csr([[1.,1.],[1.,1.+2**-40]]),'nearly_singular')
        self.assertEqual(c['status'],'CERTIFIED')
        self.assertGreater(c['inverse_infinity_upper'],1e12)

    def test_singular_and_disconnected_refuse(self):
        for a in [csr([[1,-1],[-1,1]]),csr([[1,0],[0,0]])]:
            with self.assertRaises((ValueError,AssertionError)): run(a,'singular')

    def test_q_refusal_nonsingular(self):
        a = csr([[2.,2.],[0.,1.]])
        _, w = run(csr(np.eye(2)), 'identity')
        w['matrix'] = P.I.matrix_hash(a)
        c = P.verify(a, CONTEXT, w, P.digest(w), P.Meter())
        RESULTS['nonsingular_q_refusal'] = c
        self.assertEqual(c['status'],'REFUSED')
        self.assertGreaterEqual(c['q'],1)
        self.assertEqual(exact_norm(a),F(3,2))

    def test_fixed_rooted_tree_factor_storage(self):
        for side in [4,8]:
            for ground in [1.,2**-30]:
                a=grid(side,ground);n=a.shape[0]
                pattern=[[i] if i==0 else [i-side if i>=side else i-1,i] for i in range(n)]
                meter=P.Meter();w,h=P.produce(a,CONTEXT,pattern,meter)
                cert=P.verify(a,CONTEXT,w,h,meter)
                self.assertEqual(cert['factor_entries'],2*n-1)
                self.assertEqual(cert['updates'],sum(cert['phase_updates'].values()))
                if cert['status']=='CERTIFIED' and n<=16:
                    self.assertGreaterEqual(F(cert['inverse_infinity_upper']),exact_norm(a))
                RESULTS[f'rooted_tree_{side}x{side}_ground_{ground!r}']=cert

    def test_sparse_pattern_dropped_grid(self):
        for side in [4,8]:
            c,_ = run(grid(side, 1. if side == 4 else 2**-40),f'dropped_grid_{side}x{side}',full=False)
            self.assertGreater(c['dropped_products'],0)
            self.assertEqual(c['status'],'CERTIFIED' if side == 4 else 'REFUSED')

    def test_rank_one_cannot_be_replaced_by_edges(self):
        w = [F(1,2),F(1,2)]; v = [F(1),F(-1)]; t=F(0); rt=F(1)
        exact = (sum(x*y for x,y in zip(w,v))-t)**2/rt
        independent_edges = sum(x*(y-t)**2/rt for x,y in zip(w,v))
        self.assertEqual(exact,0); self.assertEqual(independent_edges,1)
        matrix = csr([[.25,.25],[.25,.25]])
        class Budget:
            def check(self): pass
        got = P.V.energy_interval(matrix,[0,1],np.array([1.,-1.]),0.,[False,False],Budget())
        self.assertLessEqual(got[0],0); self.assertGreaterEqual(got[1],0)
        self.assertLess(got[1],1e-12)

    def test_valid_but_stage_c_inconclusive(self):
        c,_ = run(csr([[1.+2**-30,-1.],[-1.,1.]]),'loose_stage_c')
        error = P.I.upper_mul(c['inverse_infinity_upper'],1e-8)
        self.assertGreater(error,1)
        class Budget:
            def check(self): pass
        energy = P.V.energy_interval(csr([[1.]]),[0],np.array([1.]),error,[False],Budget())
        self.assertEqual(P.V.screen(energy,energy,(-error,error))['status'],'INCONCLUSIVE')

    def test_selected_field_energy_and_reaction_enclosures(self):
        a = joined()
        cert,_ = run(a,'selected_field_enclosures')
        inverse = exact_inverse(a)
        exact_x = [r[2] for r in inverse]  # one selected unit RHS only
        x = np.array([float(v)+1e-8 for v in exact_x])
        f = np.zeros(6); f[2]=1.
        class Budget:
            def check(self): pass
        budget=Budget()
        residual=P.V.residual_bound(a,np.zeros((6,0)),np.zeros((0,0)),x,np.zeros(0),f,[],budget)
        error=P.I.upper_mul(cert['inverse_infinity_upper'],residual)
        self.assertGreaterEqual(F(error),max(abs(F(float(v))-e) for v,e in zip(x,exact_x)))
        local=csr([[2.,-2.],[-2.,2.]])
        energy=P.V.energy_interval(local,[0,1],x,error,[False]*6,budget)
        exact_energy=2*(exact_x[0]-exact_x[1])**2
        self.assertLessEqual(F(energy[0]),exact_energy);self.assertGreaterEqual(F(energy[1]),exact_energy)
        # TP990026-style held reaction includes the WHOLE distributed stamp.
        field=np.array([0.,float(exact_x[1]),float(exact_x[2])])
        K=csr([[2.,-2.,0.],[-2.,2.,0.],[0.,0.,1.]])
        weights=np.array([1/3,2/3]);rt=.7;vt=np.array([.3])
        reaction=P.V.reaction_interval(K,[0],field,error,[True,False,False],[(np.array([0,1]),weights)],vt,rt,budget)
        exact_reaction=-2*exact_x[1]+F(float(weights[0]))*(F(float(weights[1]))*exact_x[1]-F(float(vt[0])))/F(rt)
        self.assertLessEqual(F(reaction[0]),exact_reaction);self.assertGreaterEqual(F(reaction[1]),exact_reaction)

    def test_binding_and_malformed_witnesses(self):
        a=csr([[2.,-1.],[-1.,2.]])
        _,w=run(a,'binding_base'); h=P.digest(w)
        mutations = [lambda x:x['L'][1].clear(), lambda x:x['permutation'].reverse(),
                     lambda x:x.update(context='stale'),lambda x:x['U'][0].append([0,2.]),
                     lambda x:x['L'][0].append([1,1.]),lambda x:x['U'][0].clear(),
                     lambda x:x['U'][0].__setitem__(0,[0,float('inf')])]
        for mutate in mutations:
            bad=copy.deepcopy(w); mutate(bad)
            with self.assertRaises((ValueError,AssertionError)):
                P.verify(a,CONTEXT,bad,h,P.Meter())
        for mutate in mutations[3:6]:
            bad=copy.deepcopy(w);mutate(bad)
            with self.assertRaises((ValueError,AssertionError)):
                P.verify(a,CONTEXT,bad,P.digest(bad),P.Meter())
        for foreign in [2, True, np.float64(2.)]:
            bad=copy.deepcopy(w);bad['U'][0][0][1]=foreign
            with self.assertRaises((ValueError,AssertionError)):
                P.verify(a,CONTEXT,bad,P.digest(bad),P.Meter())
        with self.assertRaises((ValueError,AssertionError)):
            P.verify(csr([[3.,-1.],[-1.,2.]]),CONTEXT,w,h,P.Meter())
        with self.assertRaises((ValueError,AssertionError)):
            P.verify(a,{**CONTEXT,'termination':'wrong edges'},w,h,P.Meter())

    def test_noncanonical_nonfinite_and_caps(self):
        bad=csr([[1.,0.],[0.,1.]]); bad.data[0]=float('nan')
        with self.assertRaises((ValueError,AssertionError)): run(bad,'nonfinite')
        dup=csr_matrix((np.array([1.,1.]),np.array([0,0]),np.array([0,2])),shape=(1,1))
        with self.assertRaises((ValueError,AssertionError)): run(dup,'duplicates')
        a=csr([[2.,-1.],[-1.,2.]])
        meter=P.Meter(P.I.Work(max_updates=1))
        with self.assertRaises((ValueError,AssertionError)):
            P.produce(a,CONTEXT,P.pattern_of(a,True),meter)
        self.assertGreater(meter.work.updates,1)
        meter=P.Meter(P.I.Work(max_entries=1))
        with self.assertRaises((ValueError,AssertionError)):
            P.produce(a,CONTEXT,P.pattern_of(a,True),meter)


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'synthetic_only':True,'tests':result.testsRun,'success':result.wasSuccessful(),
                      'limits':{'order':128,'wall_seconds':30,'cpu_seconds':20,'address_space_MiB':512,'blas_threads':1},
                      'results':RESULTS},indent=2,allow_nan=False))
    raise SystemExit(0 if result.wasSuccessful() else 1)
