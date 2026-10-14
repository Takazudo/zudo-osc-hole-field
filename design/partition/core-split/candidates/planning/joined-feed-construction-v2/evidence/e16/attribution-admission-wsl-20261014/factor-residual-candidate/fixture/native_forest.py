"""Bounded native forest adapter for existing synthetic prototype inputs only."""
import ctypes as C
import hashlib
import json
import math
import scipy.sparse as sp
from pathlib import Path
import subprocess
import numpy as np
import prototype as P
from native_exact import Stats, FLAGS

SOURCE=Path(__file__).with_suffix('.cpp')
PHASES=('input_validation','exact_rows','forest_selection_reduction','root_paths','norm','interval')
IP=C.POINTER(C.c_int32)
DP=C.POINTER(C.c_double)
class Board(C.Structure):
    _fields_=[('n',C.c_uint32),('nnz',C.c_uint32),('terminals',C.c_uint32),
              ('indptr',IP),('indices',IP),('columns',IP),('data',DP),('coupling',DP)]
class Result(C.Structure):
    _fields_=[(k,C.c_double) for k in ('bound','ground','radius','deficit','q','midpoint_bound','interval_radius','interval_q')]+[
        ('root',C.c_uint32),('edges',C.c_uint32),('index_visits',C.c_uint64*6),
        ('coefficient_reads',C.c_uint64*6),('row_visits',C.c_uint64),('phases',Stats*6)]

def build(directory):
    target=Path(directory)/'native_forest.so'
    subprocess.run(['c++',*FLAGS,str(SOURCE),'-o',str(target)],check=True,capture_output=True,text=True)
    sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (SOURCE,SOURCE.with_name('native_exact.cpp'))}
    return target,{'sources':sources,'binary_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'compiler':subprocess.run(['c++','--version'],check=True,capture_output=True,text=True).stdout.splitlines()[0],'flags':FLAGS}

def metadata(a):
    """Check every pointer capacity without traversing coefficient/index values.

    Native validation owns finite coefficients and canonical CSR ordering.
    The Python boundary owns actual buffer lengths, dtypes and virtual layout.
    """
    def need(ok,text):
        if not ok:raise ValueError('native metadata: '+text)
    def array(x,dtype,shape):
        need(type(x) is np.ndarray and x.dtype==np.dtype(dtype) and x.shape==shape
             and x.flags.c_contiguous and x.flags.aligned,'array shape/dtype/contiguity/alignment')
    if isinstance(a,P.JoinedRows):
        blocks=a.blocks;midpoint=a.midpoint;intervals=a.intervals;t=a.m
        need(type(t) is int and 0<t<=8,'terminal order')
        need(type(midpoint) is list and type(intervals) is list and len(midpoint)==len(intervals)==t,'terminal layout')
        for row,ends in zip(midpoint,intervals):
            need(type(row) is list and type(ends) is list and len(row)==len(ends)==t,'terminal row shape')
            need(all(type(x) is float and math.isfinite(x) for x in row),'midpoint finite value')
            need(all(type(x) is tuple and len(x)==2 and all(type(v) is float and math.isfinite(v) for v in x)
                     and x[0]<=x[1] for x in ends),'interval value')
    else:blocks=((a,np.empty((a.shape[0],0),dtype=np.float64),()),);midpoint=[];intervals=[];t=0
    need(type(blocks) in (list,tuple) and 0<len(blocks)<=2,'board count')
    total=0;offsets=[]
    for block in blocks:
        need(type(block) in (list,tuple) and len(block)==3,'board schema')
        m,b,columns=block
        need(sp.isspmatrix_csr(m) and len(m.shape)==2 and m.shape[0]==m.shape[1] and 0<m.shape[0]<=128,'CSR shape/order')
        n=m.shape[0]
        need(type(m.data) is np.ndarray and m.data.ndim==1 and m.data.size<=16384,'data length')
        array(m.data,np.float64,(m.data.size,));array(m.indices,np.int32,(m.data.size,));array(m.indptr,np.int32,(n+1,))
        need(type(columns) is tuple and len(columns)<=t and all(type(v) is int and 0<=v<t for v in columns)
             and list(columns)==sorted(set(columns)),'terminal map')
        array(b,np.float64,(n,len(columns)));offsets.append(total);total+=n
    need(0<total+t<=128,'combined order')
    if isinstance(a,P.JoinedRows):
        need(a.offsets==offsets and a.free==total and a.shape==(total+t,total+t),'stale virtual layout')
    return blocks,midpoint,intervals

class Kernel:
    def __init__(self,path):
        self.lib=C.CDLL(str(path))
        self.lib.e16_forest_result_size.restype=C.c_uint32
        self.lib.e16_forest_scratch_size.restype=C.c_uint32
        if self.lib.e16_forest_result_size()!=C.sizeof(Result):raise ValueError('native forest ABI')
        self.lib.e16_forest.argtypes=[C.c_uint32,C.POINTER(Board),C.c_uint32,DP,DP,DP,
            C.POINTER(C.c_uint32),DP,C.POINTER(Result)]
        self.lib.e16_forest.restype=C.c_int
    def certify(self,a,context):
        blocks,midpoint,intervals=metadata(a);n=a.shape[0]
        original=P.operator_hash(a);ctx=P.digest(context)
        terminals=len(midpoint)
        if len(blocks)>2 or terminals>8:raise ValueError('native block/terminal cap')
        kept=[];boards=(Board*len(blocks))()
        for k,(matrix,b,columns) in enumerate(blocks):
            for array,dtype in ((matrix.indptr,np.int32),(matrix.indices,np.int32),(matrix.data,np.float64),(b,np.float64)):
                if array.dtype!=dtype or not array.flags.c_contiguous:raise ValueError('native requires borrowed contiguous exact dtype')
            cols=np.array(columns,dtype=np.int32);kept.append(cols)
            boards[k]=Board(matrix.shape[0],matrix.data.size,len(columns),matrix.indptr.ctypes.data_as(IP),
                matrix.indices.ctypes.data_as(IP),cols.ctypes.data_as(IP),matrix.data.ctypes.data_as(DP),b.ctypes.data_as(DP))
        mid=np.array(midpoint,dtype=np.float64).reshape(terminals,terminals)
        lo=np.array([[x[0] for x in row] for row in intervals],dtype=np.float64).reshape(terminals,terminals)
        hi=np.array([[x[1] for x in row] for row in intervals],dtype=np.float64).reshape(terminals,terminals)
        interval_hash=P.digest(intervals)
        parent=np.empty(n,dtype=np.uint32);edge=np.empty(n,dtype=np.float64);result=Result()
        code=self.lib.e16_forest(len(blocks),boards,terminals,mid.ctypes.data_as(DP),lo.ctypes.data_as(DP),hi.ctypes.data_as(DP),
            parent.ctypes.data_as(C.POINTER(C.c_uint32)),edge.ctypes.data_as(DP),C.byref(result))
        phase={name:s.snapshot() for name,s in zip(PHASES,result.phases)}
        report={'status':'REFUSED' if code else 'CERTIFIED','native_code':code,'phase_work':phase,
            'index_visits':dict(zip(PHASES,result.index_visits)),
            'coefficient_reads':dict(zip(PHASES,result.coefficient_reads)),
            'row_visits':result.row_visits,'selected_edges':result.edges,
            'native_fixed_scratch_bytes':self.lib.e16_forest_scratch_size(),
            'native_result_bytes':C.sizeof(Result),'native_board_descriptor_bytes':C.sizeof(boards),
            'owned_array_payload_bytes':sum(x.nbytes for x in (*kept,mid,lo,hi,parent,edge)),
            'borrowed_array_payload_bytes':sum(m.indptr.nbytes+m.indices.nbytes+m.data.nbytes+b.nbytes for m,b,_ in blocks),
            'python_validation_and_binding':'two metadata-only buffer/layout validations, two streamed input hashes and context/interval digests; native owns coefficient/pattern validation',
            'resource_scope':'fixed scratch charged throughout; stack/compiler/Python overhead not established by payload counts; no production fit',
            'matrix_sha256':original,'context_sha256':ctx,'interval_sha256':interval_hash}
        report['proposed_scalar_contributions']=sum(s.proposed_contributions for s in result.phases)
        report['native_kernel_units']=sum(s.kernel_units for s in result.phases)
        report['native_floating_calls']=sum(s.floating_calls for s in result.phases)
        report['input_hash_passes']=2
        report['auxiliary_solve_order']=0
        report['coupled_method']='whole joined operator coercivity; no factor solve or separate Schur solve in this lane'
        metadata(a)
        current_intervals=a.intervals if isinstance(a,P.JoinedRows) else []
        if original!=P.operator_hash(a) or ctx!=P.digest(context) or interval_hash!=P.digest(current_intervals):
            report.update(status='REFUSED',reason='input/context changed during proof');return report
        if code:report['reason']=f'native forest refusal code={code}';return report
        report.update(inverse_infinity_upper=result.bound,midpoint_inverse_infinity_upper=result.midpoint_bound,
            root=result.root,ground=result.ground,tree_radius_bound_upper=result.radius,
            diagonal_deficit_upper=result.deficit,coercivity_shift_q=result.q,
            interval_radius_infinity_upper=result.interval_radius,interval_perturbation_q=result.interval_q,
            witness_sha256=hashlib.sha256(parent.tobytes()+edge.tobytes()+json.dumps([original,ctx,interval_hash,result.root,result.ground]).encode()).hexdigest())
        return report
