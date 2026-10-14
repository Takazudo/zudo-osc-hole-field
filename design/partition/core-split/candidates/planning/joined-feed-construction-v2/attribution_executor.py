"""Serialized selected-excitation engine; no production execution authority.

The guarded lifecycle owns admission and invokes run_pipeline. Source fixtures
exercise this identical artifact/serialization path with separately bounded
inputs. Neither fixture_report nor a global joined matrix is used here.
"""
import gc
import hashlib
import math
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

import attribution_reconstruction as C
import attribution_uniqueness as U
import attribution_resolution as V
import finite_adapter as A
import finite_solve as S
import finite_units as F
import resistance_attribution as R
from attribution_transport import decode, Output

PAD = 'e97b2d02-463a-5a6d-ab37-748ce29d7cf8'
BARREL = '87d2de81-b7e7-5e5c-9063-52b28f51939e'
HELD = [('TP990002','982d0043-2374-5b74-b189-fead016006b5'),
        ('TP990014','8ba40524-d0d5-50d2-9a63-f7a23aa882a4'),
        ('TP990026','4837930f-294a-5712-878f-44a71b63bce6')]
NET, CASE, DEPTH = '+12V','nominal-average','uniform-dielectric'


def scalar(value):
    f = float(value)
    R.need(math.isfinite(f) and (value == 0 or f != 0), 'unrepresentable output scalar')
    return f


class MeshItems:
    """Replay all original chunks in retained order; at most one decoded chunk.

    A.Assembly deliberately iterates this replayable source several times. Each
    pass revalidates/decompresses every chunk, including its original plan range.
    Assembly retains coordinate and stiffness arrays from multiple chunks; the
    complete live-array overlap is additional to one decoded chunk container.
    """
    def __init__(self, board, desc, op, plan, budget):
        self.board, self.desc, self.op, self.plan, self.budget = board, desc, op, plan, budget
        self.expected, self.chunks, _ = F.plan(desc,plan['pitch'],plan['face_pitch'],plan['tile_mm'],plan['origin'])
        R.need(len(self.chunks) == len(board['mesh']) and plan['chunks'] == [list(x) for x in self.chunks], 'missing/reordered chunk plan')
        R.need(plan['items'] == len(self.expected) and plan['desc_sha256'] == board['desc']['sha256'] == op['desc_sha256'], 'mesh plan identity drift')
        R.need(op['pitch'] == plan['pitch'] and op['face_pitch'] == plan['face_pitch'] and op['origin'] == plan['origin'], 'operator mesh settings drift')
        self.passes = 0

    def __len__(self):
        return len(self.expected)

    def __iter__(self):
        self.passes += 1
        for index, binding in enumerate(self.board['mesh']):
            chunk = decode(binding,self.budget)
            R.need(chunk['chunk'] == index and chunk['desc_sha256'] == self.board['desc']['sha256'], 'missing/reordered mesh chunk')
            for key in ('pitch','face_pitch','tile_mm','origin'):
                R.need(chunk[key] == self.plan[key], 'mesh chunk construction drift')
            lo, hi = self.chunks[index]
            R.need(len(chunk['items']) == hi-lo, 'chunk item count differs')
            for offset, item in enumerate(chunk['items']):
                self.budget.check()
                expected = self.expected[lo+offset]
                R.need((item['group'],item['tile']) == expected, 'mesh item order differs')
                yield item
            del item, chunk


def _board_selected(op, red, cfg, case, depth, board, binding, checker, budget):
    fixed, sources = S.held_nodes(op,cfg,board,NET)
    free = np.flatnonzero(~fixed)
    terms, _, _ = S.terminal_stamps(op,cfg)
    R.need(red['N'] == op['N'] and red['terms'] == terms and np.array_equal(red['free'],free)
           and red['source_pads'] == sources, 'incorrect free/held/source/terminal mapping')
    R.need((red['board'],red['net'],red['case'],red['depth']) == (board,NET,CASE,DEPTH), 'reduction identity drift')
    R.need(red['Y'].shape == (len(free),len(terms)) and np.isfinite(red['Y']).all(), 'invalid retained basis')
    Af,B,D,free,pos,_,_,_,_,Kb = S.board_parts(op,case,depth,cfg,board,NET)
    del Kb
    context = binding | {'board':board,'case':case,'depth':depth,'return_state':'all-present',
                         'held':hashlib.sha256(fixed.tobytes()).hexdigest(),
                         'free':hashlib.sha256(memoryview(free).cast('B')).hexdigest(),
                         'source_pads':sources,'terms':terms,'construction':'finite_solve.board_parts'}
    cert = U.certify(Af,context,context,checker,border=(B,D),reference=True)
    cert['B_infinity_upper'],cert['BT_infinity_upper'] = V.matrix_norms(B)
    budget.check()
    R.need(R._max(S._extended_residual(Af,red['Y'],B))/max(R._max(B),1e-30) <= 1e-9,'retained basis residual failed')
    R.need(R._max(red['S']-np.asarray(D-B.T@red['Y'],dtype=float))/max(R._max(red['S']),1e-30) <= 1e-9,'retained Schur differs')
    u = None
    q = np.zeros(len(terms))
    residual = 0.
    scale = None
    if board == 'KB':
        ns, w = op['supports'][PAD]
        R.need(len(ns) == len(set(map(int,ns))) and (pos[ns] >= 0).all(), 'invalid/held observation support')
        R.need(np.isfinite(w).all() and (w >= 0).all() and abs(w.sum()-1) <= 1e-9, 'invalid observation weights')
        f = np.zeros(len(free)); f[pos[ns]] = w
        scale = R._max(f)
        lu = spla.splu(Af,permc_spec='MMD_AT_PLUS_A',diag_pivot_thresh=0.,options={'SymmetricMode':True})
        u,residual = S.refined_solve(lu,Af,f,extended_solution=True)
        del lu, f
        R.need(math.isfinite(residual) and residual <= 1e-9,'selected solve residual failed')
        q = np.asarray(B.T@u,dtype=float)
    del Af,B,D,pos
    gc.collect()
    return {'N':op['N'],'free':free,'Y':red['Y'],'u0':u,'terms':terms,'S':red['S'],'g':q},cert,scale,residual


def _account_board(op, assembly, items, field, vt, cfg, case, depth, board, scale, output, budget, voltage_error):
    """Exhaustive local partition plus independently applied original classes."""
    K,Kb,_ = A.laplacian(op['Kg_face'],op['Kg_inner'],op['barrels'],op['rings'],case,depth)
    fixed,_ = S.held_nodes(op,cfg,board,NET)
    partition = C.PatternSum(K)
    current = np.zeros(op['N'],dtype=np.longdouble)
    classes = {'sheet_union':np.longdouble(0),'barrel':np.longdouble(0),'termination':np.longdouble(0)}
    ids,physical = set(),set()
    largest = None
    barrel_energy = np.longdouble(0)
    barrel_intervals = []
    copper_bounds = U.ZERO
    barrel_bounds = U.ZERO
    def emit(row):
        nonlocal largest
        row['effective_resistance_ohm'] = row['joule_energy_W']
        row['effective_resistance_mohm'] = scalar(np.longdouble(row['joule_energy_W'])*1000)
        output.row(row)
        if largest is None or row['joule_energy_W'] > largest['joule_energy_W']:
            largest = row
    for meta,nodes,matrix in C.copper_stream(assembly,items,items.expected,case,depth,board,NET):
        budget.check()
        key = (meta['kind'],tuple(meta['object_ids']),tuple(meta['layer_interval']),R.digest(meta['region']))
        R.need(meta['id'] not in ids and key not in physical,'duplicate physical ownership')
        ids.add(meta['id']);physical.add(key)
        R.need(np.isfinite(matrix.data).all(),'nonfinite component')
        ms = max(R._max(matrix.data),1e-30)
        R.need(R._max((matrix-matrix.T).data)/ms <= 1e-9 and R._max(np.asarray(matrix.sum(axis=1)).ravel())/ms <= 1e-9,'invalid local symmetry/conservation')
        partition.add(nodes,matrix)
        local_v = field[nodes]
        local_i = -S._extended_residual(matrix,local_v,np.zeros(len(nodes)))
        np.add.at(current,nodes,local_i.astype(np.longdouble))
        energy = local_v@local_i.astype(np.longdouble)
        R.need(energy >= 0,'negative component energy')
        classes[meta['kind']] += energy
        enclosure = V.energy_interval(matrix,nodes,field,voltage_error,fixed,budget)
        copper_bounds = U.add(copper_bounds,enclosure)
        row = {k:v for k,v in meta.items() if k != 'branch'} | {'joule_energy_W':scalar(energy)}
        if 'branch' in meta:
            row['oriented_current_A'] = scalar(local_v@meta['branch']['weights']/meta['branch']['resistance_ohm'])
        if meta['object_ids'] == [BARREL] and meta['kind'] == 'barrel':
            barrel_energy += energy
            barrel_bounds = U.add(barrel_bounds,enclosure)
            barrel_intervals.append(meta['layer_interval'])
        emit(row)
    original = -S._extended_residual(K,field,np.zeros(op['N']))
    partition_error = partition.relative_error()
    R.need(partition_error <= 1e-9,'complete operator partition failed')
    R.need(R._max(current-original)/scale <= 1e-9,'complete node current partition failed')
    del partition
    independent = {}
    independent['sheet_union'] = sum(np.longdouble(field@(op['Kg_'+cls]@field))*case[thick]/case['rho_ohm_mm']
                                   for cls,thick in (('face','outer_copper_mm'),('inner','inner_copper_mm')))
    independent['barrel'] = np.longdouble(field@(Kb@field))
    ts,rt,supports = S.terminal_stamps(op,cfg)
    terminal = np.zeros(len(ts),dtype=np.longdouble)
    for j,(ns,w) in enumerate(supports):
        budget.check()
        # Whole distributed rank-one stamp, including both node and terminal.
        delta = w@field[ns]-vt[j]
        amp = delta/rt
        current[ns] += w*amp
        original[ns] += w*amp
        terminal[j] = -amp
        energy = delta*amp
        classes['termination'] += energy
        emit({'id':board+':termination:'+ts[j],'kind':'termination','board':board,'net':NET,
              'object_ids':[ts[j]],'layer_interval':['interface'],
              'region':{'wire':S.wire_of(ts[j])},'joule_energy_W':scalar(energy),'oriented_current_A':scalar(amp)})
    independent['termination'] = sum((w@field[ns]-vt[j])**2/rt for j,(ns,w) in enumerate(supports))
    operator_energy = field@original+vt@terminal
    f = np.zeros(op['N'],dtype=np.longdouble)
    if board == 'KB':
        ns,w = op['supports'][PAD]; f[ns] = w
    fixed,_ = S.held_nodes(op,cfg,board,NET)
    R.need((field[fixed] == 0).all() and (f[fixed] == 0).all(),'changed held potential')
    R.need(R._max((original-f)[~fixed])/scale <= 1e-9,'free/global nodal KCL failed')
    reactions = {}
    reaction_bounds = {}
    used = set()
    if board == cfg['source_support']['board']:
        for pad in cfg['source_support']['pads'][NET]:
            ns = op['supports'][pad['pad_id']][0][op['support_inside'][pad['pad_id']]]
            R.need(not used.intersection(map(int,ns)), 'overlapping held source patches')
            used.update(map(int,ns))
            reaction_bounds[pad['ref']] = V.reaction_interval(K,ns,field,voltage_error,fixed,supports,vt,rt,budget)
            reactions[pad['ref']] = scalar(np.sum(original[ns]-f[ns],dtype=np.longdouble))
    budget.check()
    return {'classes':{k:scalar(v) for k,v in classes.items()},
            'independent_classes':{k:scalar(v) for k,v in independent.items()},
            'operator_energy_W':scalar(operator_energy),'source_reactions_A':reactions,
            'source_reaction_intervals_A':reaction_bounds,'copper_energy_interval_W':copper_bounds,
            'barrel_energy_interval_W':barrel_bounds,
            'source_total_A':scalar(np.sum(original[fixed]-f[fixed],dtype=np.longdouble)),
            'load_A':scalar(f.sum()),'work_W':scalar(field@f),'terminal_A':list(map(scalar,terminal)),
            'barrel_energy_W':scalar(barrel_energy),'barrel_intervals':barrel_intervals,
            'largest_component':largest,'partition_relative':partition_error,'mesh_passes':items.passes}


def run_pipeline(packet, output_path, budget):
    """Internal operation; lifecycle must validate sealed request before calling.

    packet is a complete data manifest, not an authority token. No CLI exposes
    this internal engine directly. Fixture entry validates ceilings separately.
    """
    output = Output(output_path,budget)
    try:
        budget.phase = 'configuration'
        cfg,cases = decode(packet['config'],budget),decode(packet['cases'],budget)
        R.need(cfg['source_support']['board'] == 'KA' and cfg['source_support']['mode'] == 'equipotential_patches', 'source configuration drift')
        R.need([(p['ref'],p['pad_id']) for p in cfg['source_support']['pads'][NET]] == HELD,'held identities differ')
        case,depth = cases['cases'][CASE],cfg['depth_cases'][DEPTH]
        R.need(all(cfg['numerical_tolerances'][k] == 1e-9 for k in ('kcl_relative','energy_relative','reciprocity_relative','support_weight_sum')), 'tolerance drift')
        removed = set(packet.get('fixture_removed',[]))
        R.need(not removed or packet.get('fixture_only') is True, 'production return state must be all-present')
        R.need(packet.get('certificate_method')==U.REFERENCE_METHOD,'certificate method binding differs')
        checker = U.Work(**packet['certificate_limits'],checkpoint=budget.check)
        fields,certs = {},{}
        scale = None
        for board in ('KA','KB'):
            budget.phase = board+'-free-operator-basis-selected-solve'
            source = packet['boards'][board]
            op = decode(source['operator'],budget)
            red = decode(source['reduction'],budget)
            R.need(red['bindings']['operator'] == source['operator']['sha256'] and red['bindings']['config'] == packet['config']['sha256']
                   and red['bindings']['cases'] == packet['cases']['sha256'] and red['bindings']['method'] == packet['solver_sha256'], 'stale reduction input binding')
            # Discard all simultaneous-load fields before numerical work.
            red = {k:red[k] for k in ('N','terms','free','source_pads','board','net','case','depth','Y','S')}
            fields[board],certs[board],local_scale,residual = _board_selected(op,red,cfg,case,depth,board,
                {'inputs':source['operator']['sha256'],'source':packet['source_bindings']},checker,budget)
            if local_scale is not None:
                scale = local_scale
            del op,red
            gc.collect()
        budget.phase = 'exact-coupled-uniqueness'
        G,wires = S.small_system(fields['KA'],fields['KB'],cfg,removed)
        expected_wires = sorted(int(w[1:]) for w,net in cfg['wires']['pairs'].items() if net == NET)
        R.need(wires == expected_wires and len(wires) > 0,'wire coverage differs')
        coupling = U.certify_coupled(certs['KA']['schur_intervals'],certs['KB']['schur_intervals'],cfg['wires']['bulk_ohm'],[w not in removed for w in wires],checker,reference=True)
        U.certify(sp.csr_matrix(G),{'return_state':'all-present'},{'return_state':'all-present'},checker,reference=True)
        vt = np.linalg.solve(G,-np.r_[fields['KA']['g'],fields['KB']['g']])
        R.need(np.isfinite(vt).all() and R._max(G@vt+np.r_[fields['KA']['g'],fields['KB']['g']])/scale <= 1e-9,'coupled solve residual failed')
        k = len(wires)
        budget.phase = 'whole-free-operator-residual-enclosure'
        residual_upper = 0.
        for index,board in enumerate(('KA','KB')):
            source = packet['boards'][board]
            op = decode(source['operator'],budget)
            Af,B,D,free,pos,_,_,_,_,Kb = S.board_parts(op,case,depth,cfg,board,NET)
            del Kb
            data = fields[board]
            terminal = vt[index*k:(index+1)*k]
            x = -data['Y']@terminal
            if data['u0'] is not None:
                x = x+data['u0']
            rhs = np.zeros(len(free))
            if board == 'KB':
                ns,w = op['supports'][PAD];rhs[pos[ns]]=w
            wire_injection=[]
            for j,wire in enumerate(wires):
                if wire in removed:
                    wire_injection.append(U.ZERO)
                else:
                    diff=U.sub(V.pair(vt[index*k+j]),V.pair(vt[(1-index)*k+j]))
                    wire_injection.append(U.mul(diff,V.pair(1./cfg['wires']['bulk_ohm'])))
            residual_upper=max(residual_upper,V.residual_bound(Af,B,D,x,terminal,rhs,wire_injection,budget))
            del op,Af,B,D,free,pos,x,rhs
            gc.collect()
        inverse_upper=V.network_inverse_bound(certs,coupling)
        voltage_error=U.upper_mul(inverse_upper,residual_upper)
        reports = {}
        for index,board in enumerate(('KA','KB')):
            budget.phase = board+'-mapping-accounting'
            data = fields.pop(board)
            if data['u0'] is None:
                data['u0'] = np.zeros(len(data['free']),dtype=np.longdouble)
            terminal = vt[index*k:(index+1)*k]
            field = S.reconstruct_potential(data,terminal)
            del data
            source = packet['boards'][board]
            op,desc,plan = (decode(source[key],budget) for key in ('operator','desc','plan'))
            R.need(desc['board'] == board and desc['net'] == NET, 'description identity drift')
            items = MeshItems(source,desc,op,plan,budget)
            assembly = A.Assembly(desc,items)
            C.check_assembly(assembly,op)
            # Exact original numbering/mapping and full geometric stiffness were
            # checked; discard duplicate derived operators before accounting.
            del assembly.Kg,assembly.node_xy,assembly.supports,assembly.support_inside
            reports[board] = _account_board(op,assembly,items,field,terminal,cfg,case,depth,board,scale,output,budget,voltage_error)
            del op,desc,plan,items,assembly,field
            gc.collect()
        budget.phase = 'complete-network-reconciliation'
        bulk = np.longdouble(0)
        R.need(removed <= set(wires), 'unknown removed fixture wire')
        currents = np.where([w not in removed for w in wires],(vt[:k]-vt[k:])/cfg['wires']['bulk_ohm'],0.)
        largest = max((r['largest_component'] for r in reports.values()),key=lambda r:r['joule_energy_W'])
        for j,w in enumerate(wires):
            if w in removed:
                continue
            e = np.longdouble(currents[j])**2*cfg['wires']['bulk_ohm']; bulk += e
            row = {'id':f'wire:W{w}','kind':'wire_bulk','board':'KA+KB','net':NET,'object_ids':[f'W{w}'],
                   'layer_interval':['wire'],'region':{'wire':w},'joule_energy_W':scalar(e),
                   'oriented_current_A':scalar(currents[j]),'effective_resistance_ohm':scalar(e),'effective_resistance_mohm':scalar(e*1000)}
            output.row(row)
            if row['joule_energy_W'] > largest['joule_energy_W']:
                largest = row
        for board,sign in (('KA',1),('KB',-1)):
            R.need(R._max(np.asarray(reports[board]['terminal_A'])+sign*currents)/scale <= 1e-9,'interface/wire balance failed')
        R.need(abs(sum(r['source_total_A']+r['load_A'] for r in reports.values()))/scale <= 1e-9,'global KCL failed')
        energy = bulk+sum(sum(r['classes'].values()) for r in reports.values())
        work = sum(r['work_W'] for r in reports.values())
        R.need(abs(float(energy-work))/max(abs(work),1e-30) <= 1e-9,'selected work reconciliation failed')
        escale = max(abs(work),1e-30)
        for cls in ('sheet_union','barrel','termination'):
            mismatch = sum(r['classes'][cls]-r['independent_classes'][cls] for r in reports.values())
            R.need(abs(mismatch)/escale <= 1e-9, 'class energy reconciliation failed: '+cls)
        R.need(abs(float(energy-bulk-sum(r['operator_energy_W'] for r in reports.values())))/escale <= 1e-9, 'complete operator energy reconciliation failed')
        copper = sum(r['classes']['sheet_union']+r['classes']['barrel'] for r in reports.values())
        summary = {'identity':{'board':'KB','ref':'U7105','pin':'4','pad_uuid':PAD,'net':NET,'case':CASE,'depth':DEPTH,'return_state':'all-present' if not removed else 'remove-'+'-'.join('W'+str(w) for w in sorted(removed)),'current_A':1},
                   'boards':reports,'uniqueness':{'boards':certs,'coupled':coupling},
                   'total_ohm':scalar(energy),'copper_ohm':scalar(copper),'bulk_W':scalar(bulk),
                   'selected_solve_residual':residual,'normalization_max_global_nodal_injection_A':scale,
                   'largest_component':largest,'stage_C':'INCONCLUSIVE',
                   'source_bindings':packet['source_bindings'],'production_evidence':False,
                   'resolution':{'free_residual_infinity_upper_A':residual_upper,
                                 'inverse_infinity_upper_ohm':inverse_upper,
                                 'voltage_error_infinity_upper_V':voltage_error}}
        if 'comparison' in packet:
            budget.phase = 'retained-projection-comparison'
            summary.update(compare_retained(packet,reports,energy,copper,budget))
        budget.phase = 'serialization'
        return output.finish(summary)
    except BaseException as exc:
        output.fail(exc)
        raise


def compare_retained(packet, reports, energy, copper, budget):
    """Compare only the independently bound original unit-current projection.

    Loaded watts/u0/g are not reconstructed or used. Stage C remains unresolved
    unless interval forward-error enclosures resolve its threshold and source
    reaction. Residuals are multiplied by the certified full inverse norm.
    """
    retained = decode(packet['comparison'],budget)
    R.need((retained['net'],retained['case'],retained['depth']) == (NET,CASE,DEPTH), 'retained comparison identity differs')
    expected = {'ka_operator':packet['boards']['KA']['operator']['sha256'],
                'kb_operator':packet['boards']['KB']['operator']['sha256'],
                'ka_reduction':packet['boards']['KA']['reduction']['sha256'],
                'kb_reduction':packet['boards']['KB']['reduction']['sha256'],
                'config':packet['config']['sha256'],'method':packet['solver_sha256']}
    R.need(all(retained['bindings'].get(k)==v for k,v in expected.items()),'retained comparison binding drift')
    projection = retained['states']['all-present']['driving_point']['KB']
    R.need(projection['pads'].count(PAD)==1, 'retained observation missing/duplicate')
    i=projection['pads'].index(PAD)
    total_ref=projection['R_driving_point_ohm'][i]
    copper_ref=projection['R_copper_ohm'][i]
    R.need(all(math.isfinite(x) and x > 0 for x in (total_ref,copper_ref)), 'invalid retained projection')
    # Unchanged reduction-versus-monolithic criterion, not energy/KCL tolerance.
    for value,reference in ((energy,total_ref),(copper,copper_ref)):
        R.need(abs(float(value)-reference)/reference <= 1e-8,'retained unit-current comparison failed')
    intervals = reports['KA']['barrel_intervals']
    R.need(intervals and not reports['KB']['barrel_intervals'],'named original barrel missing/ambiguous')
    share=reports['KA']['barrel_energy_W']/copper
    reaction=reports['KA']['source_reactions_A']['TP990026']
    copper_interval=U.add(tuple(reports['KA']['copper_energy_interval_W']),tuple(reports['KB']['copper_energy_interval_W']))
    result=V.screen(tuple(reports['KA']['barrel_energy_interval_W']),copper_interval,
                    tuple(reports['KA']['source_reaction_intervals_A']['TP990026']))
    return {'retained_comparison':{'input_sha256':packet['comparison']['sha256'],
                                 'total_ohm':total_ref,'copper_ohm':copper_ref,'status':'PASS'},
            'mechanism_screen':{'named_barrel':BARREL,'exact_intervals':intervals,
                                'copper_share':scalar(share),'minimum_share':.1,
                                'TP990026_reaction_A':reaction,'resolution':result},
            'stage_C':result['status']}
