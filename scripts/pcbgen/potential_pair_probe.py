"""Capture the unchanged P potential pair, independently of later localization.

Only two global potential RHS are solved. Existing local condensed-operator
construction may rebuild local current/potential barrel bases; no global
current solve, source change, mesh refinement or restriction release occurs.
"""
import argparse
from fractions import Fraction as F
import json
import hashlib
from pathlib import Path
import pickle
import time

import numpy as np
from scipy.sparse import coo_matrix
from scripts.pcbgen.regional_probe import sha, verify_hashes
from scripts.pcbgen.observation_support_bound import upward
from scripts.pcbgen.batch_checkpoint_store import digest_dense_operand, digest_sparse_operand


def exact(x):
    return F(*x.as_integer_ratio()) if hasattr(x,'as_integer_ratio') else F(x)


class RecordingFactor:
    """Mirror refine's initial copy and sequential float64 +=, never np.sum."""
    def __init__(self, factor, matrix, rhs):
        self.factor=factor;self.matrix=matrix;self.rhs=np.asarray(rhs,dtype=np.float64)
        if self.rhs.shape!=(matrix.shape[0],2):raise ValueError('exactly two potential columns required')
        self.field=np.zeros_like(self.rhs);self.calls=[]
        self.matrix_digest=digest_sparse_operand(matrix);self.rhs_digest=digest_dense_operand(self.rhs)
        self.extended=matrix.astype(np.longdouble)

    def solve(self, rhs, *args, **kwargs):
        if args or kwargs or len(self.calls)>=3:raise ValueError('unexpected potential factor invocation')
        if not self.calls:expected=self.rhs[1:]
        else:
            residual=float(np.max(abs(self.matrix@self.field-self.rhs)))
            if residual<=2.5e-9:raise ValueError('unexpected correction below retained refinement threshold')
            expected=np.asarray(-(self.extended@self.field.astype(np.longdouble)-self.rhs.astype(np.longdouble))[1:],dtype=float)
        if np.asarray(rhs).shape!=expected.shape or not np.array_equal(rhs,expected):
            raise ValueError('factor RHS differs from exact retained refinement order')
        result=self.factor.solve(rhs)
        if result.dtype!=np.float64 or result.shape!=expected.shape or not np.isfinite(result).all():
            raise ValueError('invalid factor output')
        if not self.calls:self.field[1:]=result
        else:self.field[1:]+=result
        self.calls.append({'rhs_sha256':digest_dense_operand(np.asarray(rhs)),
                           'increment_sha256':digest_dense_operand(result)})
        return result

    def verify(self, result):
        rows=result['potential_refinement']
        if len(rows)!=1 or (rows[0]['start'],rows[0]['stop'])!=(0,2):
            raise ValueError('capture requires one complete two-column batch')
        if len(self.calls)!=1+rows[0]['corrections'] or np.any(self.field[0]!=0):
            raise ValueError('refinement count or gauge mismatch')
        if digest_sparse_operand(self.matrix)!=self.matrix_digest or digest_dense_operand(self.rhs)!=self.rhs_digest:
            raise ValueError('potential solve operands changed')
        residual=float(np.max(abs(self.matrix@self.field-self.rhs)))
        if residual>1e-8 or residual!=rows[0]['final_float64_residual_A']:
            raise ValueError('independent final equation residual differs')
        if not np.array_equal(np.max(abs(self.field),axis=0),result['field_maximum_by_profile_ohm']):
            raise ValueError('captured coefficients differ from solver field maxima')
        return {'calls':self.calls,'independent_equation_residual_A':residual,
                'matrix_sha256':self.matrix_digest,'rhs_sha256':self.rhs_digest,
                'field_sha256':digest_dense_operand(self.field),'shape':list(self.field.shape),
                'accumulation':'initial copy; sequential float64 in-place += in retained refine order'}


def potential_rhs(conductor, profiles):
    """Reproduce the frozen API's sparse source operand, without solving it."""
    unique=[];lookup={};wr=[];wc=[];wv=[]
    for col,profile in enumerate(profiles):
        if sum((F(current) for _,_,current in profile),F()):raise ValueError('unbalanced finite source')
        for layer,patch,current in profile:
            key=layer,patch.wkb
            if key not in lookup:lookup[key]=len(unique);unique.append((layer,patch))
            wr.append(lookup[key]);wc.append(col);wv.append(current)
    W=coo_matrix((wv,(wr,wc)),shape=(len(unique),len(profiles))).tocsc()
    rows=[];cols=[];values=[]
    for col,(layer,patch) in enumerate(unique):
        vector=conductor.projections[layer].T@conductor.trials[layer].nodal_area_current(patch,1.)
        active=np.flatnonzero(vector);rows.extend(active);cols.extend([col]*len(active));values.extend(vector[active])
    return (coo_matrix((values,(rows,cols)),shape=(conductor.potential_matrix.shape[0],len(unique))).tocsc()@W).toarray()


def reduced_port_indices(conductor):
    """Recover original port identities through UPDATED restricted projections."""
    count=int(conductor.port_offsets[-1]);result=np.full(count,-1,dtype=np.int64)
    for mapping,P in zip(conductor.vertex_maps,conductor.projections):
        P=P.tocsr()
        for vertex,weights in mapping.items():
            if len(weights)!=1:continue
            port,weight=next(iter(weights.items()))
            if weight!=1:raise ValueError('corner trace lacks unit weight')
            a,b=P.indptr[vertex:vertex+2]
            if b-a!=1 or P.data[a]!=1:raise ValueError('restricted corner lacks a unit reduced trace')
            index=int(P.indices[a])
            if result[port] not in (-1,index):raise ValueError('one original port has inconsistent reduced traces')
            result[port]=index
    if np.any(result<0):raise ValueError('missing original barrel port trace')
    return result


def reconstruct_nodal_traces(conductor, field, port_indices):
    """Anchor exact canonical linear traces, with explicit float export errors.

    Non-interface vertices must have a unit reduced projection. Interface
    values use V_start+t*(V_end-V_start), preserving exact constants. Exported
    nodal_error bounds only conversion to float; the exact definition is bound
    by the recorded mesh parameters/port coefficients and this code.
    """
    ports=field[port_indices];nodes=[];errors=[];indices=[];maximum=0.
    trace_allowance=[F(64)*F(float(np.finfo(float).eps))*sum((abs(exact(x)) for x in ports[:,k]),F()) for k in range(2)]
    for layer,(sheet,P,mapping) in enumerate(zip(conductor.sheets,conductor.projections,conductor.vertex_maps)):
        P=P.tocsr();projected=np.asarray(P@field);values=projected.copy();error=np.zeros_like(values)
        unit=np.full(len(sheet.xy),-1,dtype=np.int64)
        for vertex in range(len(sheet.xy)):
            a,b=P.indptr[vertex:vertex+2]
            if b-a==1 and P.data[a]==1:unit[vertex]=P.indices[a]
            elif vertex not in mapping:raise ValueError('non-interface vertex lacks unit reduced coefficient')
        assigned={}
        for (ib,sector),pieces in sheet.interface_faces.items():
            n=conductor.barrels[ib][0].angular_count
            first=int(conductor.port_offsets[ib])+layer*n+sector
            second=int(conductor.port_offsets[ib])+layer*n+(sector+1)%n
            for piece in pieces:
                for vertex,t in zip(piece['vertices'],piece['parameters']):
                    vertex=int(vertex);t=exact(t)
                    if not 0<=t<=1:raise ValueError('interface parameter leaves its sector')
                    actual=tuple(exact(ports[first,k])+t*(exact(ports[second,k])-exact(ports[first,k])) for k in range(2))
                    if vertex in assigned and assigned[vertex]!=actual:raise ValueError('shared canonical potential traces disagree')
                    assigned[vertex]=actual
        if set(assigned)!=set(mapping):raise ValueError('interface vertex coverage differs from projection')
        for vertex,actual in assigned.items():
            for k,value in enumerate(actual):
                values[vertex,k]=float(value);error[vertex,k]=upward(abs(value-F(values[vertex,k])))
                delta=abs(value-F(projected[vertex,k]));maximum=max(maximum,upward(delta))
                if delta>trace_allowance[k]:raise ValueError('projection trace discrepancy exceeds coefficient roundoff envelope')
                if unit[vertex]>=0 and value!=exact(field[unit[vertex],k]):
                    raise ValueError('unit reduced source trace differs from canonical interpolation')
        nodes.append(values);errors.append(error);indices.append(unit)
    return nodes,errors,indices,{'maximum_projected_vs_canonical_trace_difference':maximum,
        'trace_definition':'exact V_start+t*(V_end-V_start) on each canonical sector; constant in foil depth'}


def require_same_restriction(actual, retained):
    """Compare exact serialized values, not tuple/list GeoJSON containers."""
    def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
    if canonical(actual)!=canonical(retained):
        different=[key for key in sorted(set(actual)|set(retained))
                   if canonical(actual.get(key))!=canonical(retained.get(key))]
        raise ValueError('potential restriction differs from frozen operator: '+','.join(different))


def snapshot_capture_inputs(manifest_path, code_path=__file__):
    """Bind the exact parsed manifest bytes and executable before any work."""
    manifest_path=Path(manifest_path);raw=manifest_path.read_bytes()
    manifest=json.loads(raw)
    own={str(manifest_path):hashlib.sha256(raw).hexdigest(),str(Path(code_path)):sha(code_path)}
    verify_hashes(own)
    return manifest,own


def capture(manifest_path, output):
    import platform,scipy,shapely
    from scripts.pcbgen import control_model_entry
    from scripts.pcbgen.ground_volume_geometry import extract
    from scripts.pcbgen.ground_reference import ordered_profiles
    from scripts.pcbgen.sheet_volume import SheetVolume
    from scripts.pcbgen.contact_constraints import restrict_wetted_terminals
    from scripts.pcbgen.potential_trial_matrix import potential_matrix
    started=time.monotonic();manifest_path=Path(manifest_path)
    m,own=snapshot_capture_inputs(manifest_path);output=Path(output)
    if output.exists():raise ValueError('fresh capture directory required')
    if not output.resolve().is_relative_to(Path('.circuit-cache').resolve()):raise ValueError('capture artifacts must remain ignored')
    verify_hashes(m['input_sha256']);verify_hashes(m['helper_sha256'])
    pair=json.loads(Path(m['pair_receipt']).read_text());verify_hashes(pair['input_sha256'])
    old=json.loads(Path(m['full_receipt']).read_text())
    for key in ('native','profiles','potential_mesh','current_mesh','full_receipt','native_receipt','native_manifest'):
        if pair['input_sha256'].get(m[key])!=m['input_sha256'][m[key]]:raise ValueError('input not linked to retained pair: '+key)
    if pair['raw_field_artifacts']['current-fields.npz']!=m['input_sha256'][m['current_fields']]:raise ValueError('current archive link differs')
    source=Path(m['native']);native=source.read_bytes()
    prerequisite=control_model_entry.enter(source,native,m['native_receipt'],m['native_manifest'],True,0)
    def verify():
        verify_hashes(m['input_sha256']);verify_hashes(m['helper_sha256']);verify_hashes(pair['input_sha256']);verify_hashes(own)
        control_model_entry.verify_unchanged(prerequisite)
    verify()
    rho=1.7241e-5*(1+.003947*50)
    geometry=extract(source,rho,refinement=old['refinement'],include_loads=True,main_strands=True)
    control_model_entry.select_ports(geometry,prerequisite)
    mains,reference,ports,profiles,identity=ordered_profiles(geometry,0)
    if identity!=pair['reference_contact'] or len(profiles)!=343:raise ValueError('complete function basis/reference changed')
    retained=json.loads(Path(m['profiles']).read_text())['profiles']
    if len(retained)!=len(ports)+1:raise ValueError('finite profile count changed')
    for p,q in zip(ports+[reference],retained):
        if (p['ref'],p['pad'],p['layer'],p['kind'])!=(q['ref'],q['pad'],q['layer'],q['kind']) or not p['patch'].equals_exact(shapely.geometry.shape(q['patch_geojson']),0):raise ValueError('finite profile changed')
    selected=[(ports[i]['ref'],ports[i]['pad']) for i in (4,128)]
    if selected!=[('J900134','2'),('C107','2')]:raise ValueError('selected P pair changed')
    profiles=[profiles[i] for i in (4,128)]
    key,sheets=pickle.loads(Path(m['potential_mesh']).read_bytes())
    if key!=m['potential_cache_key']:raise ValueError('potential mesh epoch key changed')
    verify()
    print('capture: assemble unchanged potential operator; local barrel bases may be rebuilt',flush=True)
    conductor=SheetVolume(sheets,[rho/t for t in geometry['thickness']],geometry['barrels'],certificate_mode='potential')
    restriction=restrict_wetted_terminals(conductor,mains)
    require_same_restriction(restriction,old['counts']['potential']['wetted_terminal_trial_restriction'])
    port_indices=reduced_port_indices(conductor)
    rhs=potential_rhs(conductor,profiles)
    proxy=RecordingFactor(conductor.potential_factor,conductor.potential_matrix,rhs)
    conductor.potential_factor=proxy
    verify()
    result=potential_matrix(conductor,profiles,batch_size=2)
    verify()
    proof=proxy.verify(result)
    nodes,errors,node_indices,traces=reconstruct_nodal_traces(conductor,proxy.field,port_indices)
    verify();output.mkdir(parents=True)
    data={'reduced_field':proxy.field,'rhs':rhs,'port_reduced_indices':port_indices,'port_values':proxy.field[port_indices]}
    for layer in range(len(nodes)):
        data['nodal_'+str(layer)]=nodes[layer];data['nodal_error_'+str(layer)]=errors[layer]
        data['node_reduced_index_'+str(layer)]=node_indices[layer]
    np.savez_compressed(output/'potential-fields.npz',**data)
    record={'status':'CAPTURE VERIFIED; nominal unchanged P pair only; regional localization separate',
        'input_sha256':{**m['input_sha256'],**m['helper_sha256'],**pair['input_sha256'],**own},
        'manifest':str(manifest_path),'source_pair':selected,'reference_contact':identity,
        'native_prerequisite':prerequisite,'restriction':restriction,'capture':proof,'trace_reconstruction':traces,
        'potential_lower_ohm':result['energy'].tolist(),
        'prior_potential_lower_ohm':pair['matrices_ohm']['lower'],
        'maximum_lower_change_ohm':float(np.max(abs(result['energy']-np.asarray(pair['matrices_ohm']['lower'])))),
        'solver_receipt':{k:v for k,v in result.items() if k!='energy'},
        'artifact_sha256':{'potential-fields.npz':sha(output/'potential-fields.npz')},
        'libraries':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'shapely':shapely.__version__},
        'scope':['Two global potential RHS only; no global current solve or full basis solve.',
                 'Unchanged local barrel current/potential bases may be reconstructed by the existing potential API.',
                 'All finite profiles, copper, material parameters and wetted restrictions remain fixed.',
                 'Original current fields/receipts are unchanged; no issue38 or physical admission.'],
        'runtime_sec':time.monotonic()-started}
    verify();(output/'capture.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'capture':str(output/'capture.json'),'sha256':sha(output/'capture.json'),
                      'runtime_sec':record['runtime_sec'],'lower_change_ohm':record['maximum_lower_change_ohm']}),flush=True)
    return record


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',default='design/partition/potential-pair-probe.json')
    parser.add_argument('--output',required=True)
    args=parser.parse_args();capture(args.manifest,args.output)
