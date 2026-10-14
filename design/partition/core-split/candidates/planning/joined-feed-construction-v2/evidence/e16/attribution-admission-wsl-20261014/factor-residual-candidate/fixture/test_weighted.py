"""Extension of the retained fixture; oracle inputs never enter the producer.

Run under outer timeout 30s. Importing test_prototype sets 512MiB/20CPU limits.
"""
import test_prototype as T
from test_prototype import P, F, np, csr, CONTEXT
import copy
import hashlib
import inspect
import json
import math
from pathlib import Path
import resource
import time
import tracemalloc
import unittest
import weakref

RESULTS = {}


def tree(a, side):
    return [[i] if i == 0 else [i-side if i >= side else i-1, i] for i in range(a.shape[0])]


def oracle_weights(a):
    # Independent, dense, <=16 ONLY. Not imported/called by prototype.py.
    return [float(sum(map(abs, row))) for row in T.exact_inverse(a)]


def snapshot(meter):
    return {'total_updates': meter.work.updates, 'phase_updates': dict(meter.phases),
            'peak_live_slots': meter.work.peak_entries, 'current_reserved_slots': meter.live,
            'discarded_factor_products': meter.dropped_products,
            'weight_passes_completed': meter.weight_passes_completed,
            'weight_outputs': meter.weight_outputs,
            'auxiliary_system_order': 0, 'auxiliary_construction_updates': 0,
            'counter_convention': 'historical primitive/kernel calls; not production updates'}


def measured(call, meter):
    tracemalloc.start(); started = time.monotonic()
    try:
        result = call()
    except ValueError as exc:
        result = {'status': 'REFUSED', 'reason': str(exc)}
    elapsed = time.monotonic()-started
    _, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
    result.update(accounting=snapshot(meter), measured_wall_seconds=elapsed,
                  traced_peak_bytes=peak,
                  process_high_water_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    assert meter.work.updates == sum(meter.phases.values())
    return result


def board_case(a, pattern, mode, oracle=None):
    meter = P.Meter()
    def execute():
        w, h = P.produce(a, CONTEXT, pattern, meter)
        packet = stamp = None
        if mode == 'candidate': packet, stamp = P.produce_weights(a, CONTEXT, w, h, meter)
        elif mode == 'oracle':
            packet = P.weight_packet(a, CONTEXT, w, oracle, 'oracle:tiny-Fraction-only')
            stamp = P.digest(packet)
        result = P.verify(a, CONTEXT, w, h, meter, packet, stamp)
        result['producer_outcome'] = ('CANDIDATE_EMITTED' if mode == 'candidate' else
                                      'ORACLE_ONLY' if mode == 'oracle' else 'UNIT_WEIGHTS')
        result['weights'] = None if packet is None else packet['values']
        result['coupled_acceptance'] = 'NOT APPLICABLE: board-only fixture'
        result['screen'] = 'NOT RUN: no physical selected fixture for this board'
        return result
    result = measured(execute, meter)
    result.setdefault('producer_outcome', 'CANDIDATE_EMITTED' if meter.weight_outputs else
                      'CANDIDATE_FAILED' if mode == 'candidate' else 'ORACLE_ONLY' if mode == 'oracle' else 'UNIT_WEIGHTS')
    result.setdefault('coupled_acceptance','NOT APPLICABLE: board-only fixture')
    result.setdefault('screen','NOT RUN: board certificate unavailable')
    result['producer_failure_reason'] = result.get('reason') if result['producer_outcome']=='CANDIDATE_FAILED' else None
    return result


class Budget:
    def check(self): pass


def physical_result(cert, blocks, exact):
    """Actual resolution APIs; separately stored D and wire injection, one RHS."""
    inv = T.exact_inverse_values(exact)
    exact_x = [row[2] for row in inv]
    x = np.array([float(v)+1e-8 for v in exact_x])
    from scipy.sparse import block_diag
    A = block_diag([a for a, _ in blocks], format='csr')
    B = np.vstack([b for _, b in blocks])
    raw = float(1/.7); D = np.eye(2)*raw
    wire = float(-exact[4][5])
    delta = P.I.sub((float(x[4]),)*2, (float(x[5]),)*2)
    injection = P.I.mul((wire,)*2, delta)
    f = np.array([0.,0.,1.,0.])
    rho = P.V.residual_bound(A, B, D, x[:4], x[4:], f,
                            [injection, (-injection[1],-injection[0])], Budget())
    error = P.I.upper_mul(cert['inverse_infinity_upper'], rho)
    assert F(error) >= max(abs(F(float(v))-e) for v,e in zip(x,exact_x))
    copper_form = csr([[2.,-2.],[-2.,2.]])
    energy = P.V.energy_interval(copper_form,[0,1],x,error,[False]*6,Budget())
    expected = 2*(exact_x[0]-exact_x[1])**2
    assert F(energy[0]) <= expected <= F(energy[1])
    # Preserve complete distributed quadratic (w^T v-t)^2/Rt, not edges.
    weights = [F(1,4),F(3,4)]; rt=F(.7)
    delta = P.I.sub(P.I.add(P.I.mul((.25,)*2,P.V.field_interval(x[0],error)),
                            P.I.mul((.75,)*2,P.V.field_interval(x[1],error))),
                     P.V.field_interval(x[4],error))
    whole = P.I.div_positive(P.I.mul(delta,delta),(.7,.7))
    exact_whole=(weights[0]*exact_x[0]+weights[1]*exact_x[1]-exact_x[4])**2/rt
    assert F(whole[0]) <= exact_whole <= F(whole[1])
    # Same held-functional fixture as legacy test, tied to this certified field.
    held_field=np.array([0.,float(x[1]),float(x[2])])
    K=csr([[2.,-2.,0.],[-2.,2.,0.],[0.,0.,1.]])
    reaction=P.V.reaction_interval(K,[0],held_field,error,[True,False,False],
              [(np.array([0,1]),np.array([1/3,2/3]))],np.array([.3]),.7,Budget())
    exact_reaction=-2*exact_x[1]+F(1/3)*(F(2/3)*exact_x[1]-F(.3))/rt
    assert F(reaction[0]) <= exact_reaction <= F(reaction[1])
    return {'residual_upper':rho,'field_error_upper':error,'copper_energy':energy,
            'whole_distributed_termination_energy':whole, 'held_reaction':reaction,
            'screen':P.V.screen(energy,energy,reaction),
            'screen_scope':'synthetic target equals local copper functional; not actual TP990026 disposition',
            'reference_inverse_norm':float(max(sum(map(abs,row)) for row in inv))}


def coupled_case(blocks, d, exact, patterns, mode):
    supplied=None
    oracle_setup=P.Meter()
    setup_started=time.monotonic()
    if mode=='oracle':
        supplied=[]
        for i,(a,_) in enumerate(blocks):
            context={**CONTEXT,'board':i}
            # Oracle-only packet setup; block_certificate still charges its own
            # factor producer. This setup is NOT a candidate runtime operation.
            w,_=P.produce(a,context,patterns[i],oracle_setup)
            oracle_setup.offset=oracle_setup.live
            packet=P.weight_packet(a,context,w,oracle_weights(a),'oracle:tiny-Fraction-only')
            supplied.append((packet,P.digest(packet)))
    setup_elapsed=time.monotonic()-setup_started
    meter=P.Meter()
    result=measured(lambda:P.block_certificate(blocks,d,CONTEXT,meter,patterns,
                    'supplied' if mode=='oracle' else mode, supplied),meter)
    result['producer_outcome']=('CANDIDATE_EMITTED' if len(meter.weight_outputs)==len(blocks) else
                               'CANDIDATE_FAILED' if mode=='candidate' else
                               'ORACLE_ONLY' if mode=='oracle' else 'UNIT_WEIGHTS')
    result['oracle_control_preparation']={'accounting':snapshot(oracle_setup),
        'wall_seconds':setup_elapsed,'scope':'separate test-only oracle packet factor preparation; never producer input or fit evidence'}
    result['all_factor_certificate_kernel_updates_including_oracle_preparation']=meter.work.updates+oracle_setup.work.updates
    result['attempted_boards']=meter.board_certificates
    result['producer_failure_reason']=result.get('reason') if result['producer_outcome']=='CANDIDATE_FAILED' else None
    result['coupled_acceptance']=result['status']
    result['screen']='NOT RUN: no coupled certificate'
    if result['status']=='CERTIFIED':
        # Independent exact Schur, including original nonsymmetric coefficients.
        schur=[[exact[4+i][4+j] for j in range(2)] for i in range(2)]
        for a,b in blocks:
            inv=T.exact_inverse(a)
            for i in range(2):
                for j in range(2):
                    schur[i][j]-=sum(F(float(b[k,i]))*inv[k][l]*F(float(b[l,j]))
                                     for k in range(2) for l in range(2))
        for i in range(2):
            for j in range(2):
                lo,hi=result['schur_intervals'][i][j]
                assert F(lo)<=schur[i][j]<=F(hi)
        result.update(physical_result(result,blocks,exact))
    else:
        try: result['reference_inverse_norm']=float(max(sum(map(abs,row)) for row in T.exact_inverse_values(exact)))
        except ValueError: result['reference']='exact singular'
    return result


class WeightedTests(unittest.TestCase):
    def test_retained_grids_and_held_out(self):
        for side,ground in [(4,1.),(8,1.),(9,1.),(4,2.**-30),(8,2.**-30)]:
            a=T.grid(side,ground); pattern=tree(a,side)
            oracle=oracle_weights(a) if side==4 else None
            case={}
            for mode in [None,'candidate']+(['oracle'] if oracle is not None else []):
                result=board_case(a,pattern,mode,oracle)
                if result['status']=='CERTIFIED' and oracle is not None:
                    self.assertGreaterEqual(F(result['inverse_infinity_upper']),T.exact_norm(a))
                case[str(mode)]=result
            case['reference']=float(T.exact_norm(a)) if oracle is not None else 'connected grounded graph; exact dense oracle NOT RUN above order16'
            RESULTS[f'tree_{side}_ground_{ground}']=case
        # New negative result: positive eight-pass output fails contraction.
        c=RESULTS['tree_4_ground_1.0']
        self.assertEqual(c['candidate']['status'],'REFUSED')
        self.assertGreater(c['candidate']['q'],1.)
        self.assertEqual(c['oracle']['status'],'CERTIFIED')

    def test_retained_incomplete_grid_pattern(self):
        for side, ground in [(4,1.),(8,2.**-40)]:
            a=T.grid(side,ground);pattern=P.pattern_of(a,False)
            oracle=oracle_weights(a) if side==4 else None
            case={str(mode):board_case(a,pattern,mode,oracle)
                  for mode in [None,'candidate']+(['oracle'] if oracle else [])}
            for result in case.values():
                if result['status']=='CERTIFIED' and oracle:
                    self.assertGreaterEqual(F(result['inverse_infinity_upper']),T.exact_norm(a))
            RESULTS[f'incomplete_grid_{side}']=case

    def test_deterministic_producer_without_oracle_access(self):
        from unittest.mock import patch
        a=T.grid(4);meter=P.Meter();w,h=P.produce(a,CONTEXT,tree(a,4),meter)
        with patch.object(T,'exact_inverse',side_effect=AssertionError('oracle access forbidden')), patch.object(T,'exact_inverse_values',side_effect=AssertionError('oracle access forbidden')):
            first,fh=P.produce_weights(a,CONTEXT,w,h,meter)
            before=meter.work.updates
            second,sh=P.produce_weights(a,CONTEXT,w,h,meter)
        self.assertEqual(first,second);self.assertEqual(fh,sh)
        self.assertGreater(meter.work.updates,before)
        self.assertEqual(meter.weight_passes_completed,16)
        RESULTS['deterministic_two_attempts_same_meter']=snapshot(meter)

    def test_signed_disconnected_and_producer_failures(self):
        for name,a in [('mixed_signed',csr([[-2.,1.],[1.,2.]])),
                       ('nonsymmetric',csr([[1.,-1.],[1.,0.]])),
                       ('disconnected',csr([[1.,-1.,0.],[-1.,1.,0.],[0.,0.,2.]])),
                       ('overflow',csr([[1e-300,1e300],[0.,1.]]))]:
            pattern=P.pattern_of(a,True) if name not in ('disconnected','overflow') else [[i] for i in range(a.shape[0])]
            case={}
            try: oracle=oracle_weights(a)
            except (ValueError,OverflowError): oracle=None
            for mode in [None,'candidate']+(['oracle'] if oracle is not None else []):
                result=board_case(a,pattern,mode,oracle)
                if result['status']=='CERTIFIED': self.assertGreaterEqual(F(result['inverse_infinity_upper']),T.exact_norm(a))
                case[str(mode)]=result
            RESULTS[name]=case
        self.assertEqual(RESULTS['disconnected']['candidate']['status'],'REFUSED')
        self.assertEqual(RESULTS['overflow']['candidate']['status'],'REFUSED')

    def test_complete_coupled_cases(self):
        for name,ground,nonsym,wire,diagonal in [
            ('floating_KB_grounded_KA',1.,False,4.,False),
            ('weak_ground_inconclusive',2.**-30,False,4.,False),
            ('nonsymmetric_stamps',1.,True,4.,False),
            ('mixed_sign_coupled',1.,False,4.,False),
            ('board_pass_schur_fail',1.,False,4.,True),
            ('disconnected_wire',1.,False,0.,False)]:
            blocks,d,exact=T.separated_fixture(ground,nonsym,wire)
            if name=='mixed_sign_coupled':
                blocks[0]=(csr([[-2.,1.],[1.,2.]]),blocks[0][1])
                for i in range(2):
                    for j in range(2):exact[i][j]=F(float(blocks[0][0][i,j]))
            patterns=[[[0],[1]] if diagonal else [[0,1],[0,1]] for _ in blocks]
            case={str(mode):coupled_case(blocks,d,exact,patterns,mode) for mode in [None,'candidate','oracle']}
            RESULTS[name]=case
        self.assertEqual(RESULTS['floating_KB_grounded_KA']['candidate']['status'],'CERTIFIED')
        self.assertEqual(RESULTS['weak_ground_inconclusive']['candidate']['screen']['status'],'INCONCLUSIVE')
        self.assertEqual(RESULTS['board_pass_schur_fail']['candidate']['status'],'REFUSED')
        self.assertEqual(RESULTS['disconnected_wire']['candidate']['status'],'REFUSED')

    def test_nonuniform_weighted_schur_and_scale(self):
        blocks,d,exact=T.separated_fixture(nonsymmetric=True)
        patterns=[[[0,1],[0,1]]]*2
        for scale in [2.**-200,1.,2.**200]:
            packets=[]
            for i,(a,_) in enumerate(blocks):
                ctx={**CONTEXT,'board':i};w,_=P.produce(a,ctx,patterns[i],P.Meter())
                packet=P.weight_packet(a,ctx,w,[scale,7.*scale],'test:nonuniform-scale')
                packets.append((packet,P.digest(packet)))
            result=P.block_certificate(blocks,d,CONTEXT,P.Meter(),patterns,'supplied',packets)
            physical_result(result,blocks,exact)
            self.assertGreaterEqual(F(result['inverse_infinity_upper']),max(sum(map(abs,r)) for r in T.exact_inverse_values(exact)))
            RESULTS[f'nonuniform_scale_{scale}']=result

    def test_stale_malformed_scale_underflow_and_overflow(self):
        a=csr([[2.,-1.],[-1.,2.]])
        meter=P.Meter();w,h=P.produce(a,CONTEXT,P.pattern_of(a,True),meter)
        packet,stamp=P.produce_weights(a,CONTEXT,w,h,meter)
        refusals=[]
        for values in [[],[1.], [0.,1.],[-1.,1.],[True,1.],[1,1.],
                       [float('nan'),1.],[float('inf'),1.],[5e-324,1.],[2.**401,1.],
                       [np.float64(1.),1.],[[1.],1.]]:
            bad=copy.deepcopy(packet);bad['values']=values
            refused_meter=P.Meter()
            with self.assertRaises(ValueError) as rejection:P.verify(a,CONTEXT,w,h,refused_meter,bad,'bad')
            refusals.append({'input':repr(values),'reason':str(rejection.exception),
                             'accounting':snapshot(refused_meter),'coupled_acceptance':'REFUSED',
                             'screen':'NOT RUN: malformed weights','producer_outcome':'ADVERSARIAL_INPUT'})
        bad=copy.deepcopy(packet);bad['values'][0]*=2
        with self.assertRaisesRegex(ValueError,'digest'):P.verify(a,CONTEXT,w,h,P.Meter(),bad,stamp)
        for key in ['context','matrix','factor']:
            bad=copy.deepcopy(packet);bad[key]='stale'
            with self.assertRaisesRegex(ValueError,'binding'):P.verify(a,CONTEXT,w,h,P.Meter(),bad,P.digest(bad))
        badw=copy.deepcopy(w);badw['U'][0][0][1]+=1.
        with self.assertRaisesRegex(ValueError,'binding'):
            P.verify(a,CONTEXT,badw,P.digest(badw),P.Meter(),packet,stamp)
        # Tiny exact E product underflows in binary64; outward verification still
        # encloses it, while approximate producer accuracy is never a premise.
        a=csr([[1.,5e-324],[0.,1.]])
        w,h=P.produce(a,CONTEXT,[[0],[1]],P.Meter())
        packet=P.weight_packet(a,CONTEXT,w,[2.**-400,2.**-400],'test:underflow')
        cert=P.verify(a,CONTEXT,w,h,P.Meter(),packet,P.digest(packet))
        self.assertEqual(cert['status'],'CERTIFIED')
        self.assertGreater(cert['residual_row_upper'][0],0.)
        self.assertGreaterEqual(F(cert['inverse_infinity_upper']),T.exact_norm(a))
        RESULTS['underflow_enclosed']=cert
        RESULTS['malformed_weight_refusals']=refusals

    def test_actual_residual_row_lifetime_and_failed_work(self):
        references=[];original=P.ResidualRow
        class ObservedRow(original):
            def __init__(self):
                super().__init__();references.append(weakref.ref(self))
        class ObservedMeter(P.Meter):
            def entries(self,n):
                if self.phase in ('residual','weighted_residual','weight_production_residual') and n<self.live-self.offset:
                    self_test.assertTrue(all(ref() is None for ref in references))
                    frame=inspect.currentframe().f_back
                    self_test.assertNotIn('row',frame.f_locals)
                    self_test.assertNotIn('put',frame.f_locals)
                super().entries(n)
        self_test=self;P.ResidualRow=ObservedRow
        try:
            a=T.grid(4);meter=ObservedMeter();w,h=P.produce(a,CONTEXT,tree(a,4),meter)
            packet,stamp=P.produce_weights(a,CONTEXT,w,h,meter)
            P.verify(a,CONTEXT,w,h,meter,packet,stamp)
            self.assertTrue(all(ref() is None for ref in references))
            self.assertEqual(len(references),9*16)
        finally:P.ResidualRow=original
        meter=P.Meter(P.I.Work(max_updates=100))
        with self.assertRaisesRegex(ValueError,'arithmetic cap'):
            P.produce_weights(a,CONTEXT,w,h,meter)
        self.assertGreater(meter.work.updates,100)
        self.assertEqual(meter.work.updates,sum(meter.phases.values()))
        RESULTS['discarded_capped_attempt']=snapshot(meter)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(WeightedTests))
    print(json.dumps({'synthetic_only':True,'tests':result.testsRun,'success':result.wasSuccessful(),
        'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                         [Path(P.__file__),Path(__file__),Path(T.__file__)]},
        'limits':{'order':128,'oracle_order':16,'wall_seconds':30,'CPU_seconds':20,'AS_MiB':512,'threads':1},
        'measurement_scope':'traced bytes/wall cover candidate invocation only; RSS is cumulative process high-water including fixture/oracles; physical evaluation and exact oracles outside candidate meter',
        'results':RESULTS},indent=2,allow_nan=False))
    raise SystemExit(0 if result.wasSuccessful() else 1)
